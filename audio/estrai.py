#!/usr/bin/env python3
"""Estrae dai capitoli .mdx il "testo parlato", paragrafo per paragrafo, in audio/manifest.json.

Regole: si leggono titoli, paragrafi, liste, tabelle, Aside, spiegazioni dei <Curl>; NON si leggono
blocchi di codice, import, frontmatter, <Prova>, <Sandbox>. Il paragrafo che precede un <Prova>
è marcato `pausa`; i paragrafi dentro <details> sono `nascosto` (letti solo se il lettore apre).
Per ogni paragrafo: `id`, `hash` (del testo parlato), `dom` (testo com'è nella pagina, per
associarlo all'elemento HTML), `voce` (testo con le pronunce corrette).

Uso: python audio/estrai.py [--pagina json/01-cos-e-json] [--stampa]
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
DOCS = RADICE / "site" / "src" / "content" / "docs"
MANIFEST = RADICE / "audio" / "manifest.json"
PRONUNCIA = json.loads((RADICE / "audio" / "pronuncia.json").read_text())
# ordine: prima le parole (solo Piper), poi i simboli (tutte le voci) — come il file originale,
# così gli hash del testo per Piper non cambiano e gli MP3 esistenti restano validi
REGOLE_PIPER = [(re.compile(k), v) for k, v in {**PRONUNCIA["parole_piper"], **PRONUNCIA["simboli"]}.items()]
REGOLE_SIMBOLI = [(re.compile(k), v) for k, v in PRONUNCIA["simboli"].items()]

# --- pulizia del markdown inline -------------------------------------------------------------

def inline(t: str) -> str:
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", t)
    t = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", t)          # link → testo
    t = re.sub(r"<a [^>]*>(.*?)</a>", r"\1", t)
    t = re.sub(r"</?(em|strong|b|i|code|kbd|span|br|sup|sub)\b[^>]*>", "", t)
    t = t.replace("**", "").replace("__", "")
    t = re.sub(r"(?<!\w)\*(?!\s)(.+?)(?<!\s)\*(?!\w)", r"\1", t)   # *corsivo*
    t = re.sub(r"(?<!\w)_(?!\s)(.+?)(?<!\s)_(?!\w)", r"\1", t)
    t = re.sub(r"`([^`]*)`", r"\1", t)
    t = t.replace("\\_", "_").replace("\\*", "*").replace("\\|", "|")
    t = html.unescape(t)
    return re.sub(r"\s+", " ", t).strip()


def voce(t: str, regole=None) -> str:
    """Testo parlato. Default: regole per Piper (con riscritture fonetiche); REGOLE_SIMBOLI: per le
    voci che sanno leggere l'inglese (browser, cloud), con le parole inglesi lasciate come sono."""
    for rx, sost in (regole or REGOLE_PIPER):
        t = rx.sub(sost, t)
    t = t.replace("{", " graffa aperta ").replace("}", " graffa chiusa ").replace("[", " quadra aperta ").replace("]", " quadra chiusa ")
    t = re.sub(r"[`*_#>|\\]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def norma(t: str) -> str:
    """Forma normalizzata usata dal player per riconoscere l'elemento HTML."""
    return re.sub(r"[^a-z0-9àèéìòù]+", "", t.lower())[:160]


# --- parsing riga per riga ---------------------------------------------------------------------

RE_H = re.compile(r"^(#{1,4})\s+(.*)")
RE_LI = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.*)")
RE_TAB = re.compile(r"^\s*\|.*\|\s*$")
RE_TAB_SEP = re.compile(r"^\s*\|?\s*:?-{2,}")


def stringhe_js(s: str) -> list[str]:
    """Tutte le stringhe letterali ('…', "…", `…`) in ordine, gestendo gli escape."""
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c in "'\"`":
            j = i + 1
            buf = []
            while j < len(s) and s[j] != c:
                if s[j] == "\\" and j + 1 < len(s):
                    buf.append(s[j + 1]); j += 2; continue
                buf.append(s[j]); j += 1
            out.append("".join(buf)); i = j + 1
        else:
            i += 1
    return out


def estrai_file(path: Path) -> list[dict]:
    testo = path.read_text(encoding="utf-8")
    if testo.startswith("---"):
        fine = testo.find("\n---", 3)
        testo = testo[fine + 4:]
    righe = testo.split("\n")
    blocchi: list[dict] = []
    in_code = False
    in_details = 0
    tag_saltati = 0          # dentro <Prova>/<Sandbox> multi-riga
    in_curl: list[str] | None = None
    par: list[str] = []
    tab: list[str] = []

    def chiudi_par():
        nonlocal par
        if par:
            t = inline(" ".join(par))
            if t:
                blocchi.append({"tipo": "p", "dom": t})
        par = []

    def chiudi_tab():
        nonlocal tab
        if tab:
            righe_t = [r for r in tab if not RE_TAB_SEP.match(r)]
            celle = [[inline(c) for c in r.strip().strip("|").split("|")] for r in righe_t]
            if celle:
                intestazione = celle[0]
                for r in celle[1:]:
                    frase = "; ".join(f"{intestazione[i]}: {v}" if i < len(intestazione) and intestazione[i] else v
                                      for i, v in enumerate(r) if v)
                    blocchi.append({"tipo": "tr", "dom": " ".join(v for v in r if v), "voce_src": frase})
        tab = []

    i = 0
    while i < len(righe):
        r = righe[i]
        s = r.strip()
        if s.startswith("```"):
            chiudi_par(); chiudi_tab(); in_code = not in_code; i += 1; continue
        if in_code:
            i += 1; continue
        if in_curl is not None:
            in_curl.append(r)
            if s.endswith("/>"):
                blob = "\n".join(in_curl); in_curl = None
                m = re.search(r"spiega=\{\[(.*)\]\}", blob, re.S)
                if m:
                    strs = stringhe_js(m.group(1))
                    coppie = [(strs[k], strs[k + 1]) for k in range(0, len(strs) - 1, 2)]
                    frasi = ["Il comando curl, opzione per opzione."]
                    for tok, sp in coppie:
                        frasi.append(f"{inline(tok)}: {inline(sp)}")
                    blocchi.append({"tipo": "curl", "dom": inline(coppie[0][0]) if coppie else "", "voce_src": " ".join(frasi)})
            i += 1; continue
        if s.startswith("<Curl"):
            chiudi_par(); chiudi_tab(); in_curl = [r]
            if s.endswith("/>"):
                in_curl.append(""); righe.insert(i + 1, "/>")  # forza la chiusura al giro dopo
            i += 1; continue
        if tag_saltati or s.startswith(("<Prova", "<Sandbox")):
            chiudi_par(); chiudi_tab()
            if s.startswith("<Prova") and blocchi:
                blocchi[-1]["pausa"] = True
            if not (s.endswith("/>") or ("/>" in s)):
                tag_saltati = 1
            elif tag_saltati and s.endswith("/>"):
                tag_saltati = 0
            if s.startswith("<") and s.endswith("/>"):
                tag_saltati = 0
            i += 1; continue
        if s.startswith("<details"):
            chiudi_par(); chiudi_tab(); in_details += 1; i += 1; continue
        if s.startswith("</details"):
            chiudi_par(); chiudi_tab(); in_details = max(0, in_details - 1); i += 1; continue
        if s.startswith("<summary"):
            chiudi_par(); chiudi_tab()
            t = inline(re.sub(r"</?summary>", "", s))
            if t:
                blocchi.append({"tipo": "summary", "dom": t})
            i += 1; continue
        m = re.match(r"<Aside\b[^>]*?(?:title=\"([^\"]*)\")?[^>]*>", s)
        if s.startswith("<Aside"):
            chiudi_par(); chiudi_tab()
            tipo = re.search(r'type="(\w+)"', s)
            titolo = re.search(r'title="([^"]*)"', s)
            nomi = {"tip": "Suggerimento", "note": "Nota", "caution": "Attenzione", "danger": "Pericolo"}
            t = titolo.group(1) if titolo else nomi.get(tipo.group(1) if tipo else "note", "Nota")
            blocchi.append({"tipo": "aside", "dom": inline(t)})
            i += 1; continue
        if s.startswith("import ") or s in ("</Aside>", "<Tabs", "</Tabs>", "</TabItem>", "<Steps>", "</Steps>", "<CardGrid", "</CardGrid>") \
                or s.startswith(("<Tabs", "<TabItem", "</TabItem", "<Steps", "</Steps", "<CardGrid", "</CardGrid", "<Card ", "</Card>", "<Prova", ":::")):
            chiudi_par(); chiudi_tab(); i += 1; continue
        if not s:
            chiudi_par(); chiudi_tab(); i += 1; continue
        m = RE_H.match(s)
        if m:
            chiudi_par(); chiudi_tab()
            blocchi.append({"tipo": f"h{len(m.group(1))}", "dom": inline(m.group(2))}); i += 1; continue
        if RE_TAB.match(s):
            chiudi_par(); tab.append(s); i += 1; continue
        chiudi_tab()
        m = RE_LI.match(r)
        if m:
            chiudi_par()
            blocchi.append({"tipo": "li", "dom": inline(m.group(1))}); i += 1; continue
        if r.startswith("   ") and blocchi and blocchi[-1]["tipo"] == "li" and not par:
            # continuazione indentata di un elemento di lista: nel DOM sta dentro lo stesso <li>
            blocchi[-1]["dom"] = inline(blocchi[-1]["dom"] + " " + s); i += 1; continue
        if s.startswith("<") and not s.startswith("<code") and not re.match(r"<(em|strong|b|i|code|kbd|a)\b", s):
            i += 1; continue
        par.append(s)
        if in_details:
            pass
        i += 1
    chiudi_par(); chiudi_tab()

    # segna i nascosti (dentro <details>): secondo passaggio semplice sui marcatori
    out = []
    for n, b in enumerate(blocchi):
        b["id"] = f"p{n}"
        src = b.pop("voce_src", None) or b["dom"]
        if b["tipo"].startswith("h"):
            src = src + "."
        b["voce"] = voce(src)
        b["t"] = voce(src, REGOLE_SIMBOLI)
        b["hash"] = hashlib.sha1(b["voce"].encode()).hexdigest()[:12]
        b["n"] = norma(b["dom"])
        out.append(b)
    return out


def marca_nascosti(path: Path, blocchi: list[dict]) -> None:
    """I blocchi dentro <details> diventano `nascosto`: li riconosco rifacendo una passata leggera."""
    testo = path.read_text(encoding="utf-8")
    dentro = set()
    for m in re.finditer(r"<details>(.*?)</details>", testo, re.S):
        for b in blocchi:
            if b["tipo"] != "summary" and b["dom"] and inline(b["dom"])[:40] in inline(m.group(1)):
                dentro.add(b["id"])
    for b in blocchi:
        if b["id"] in dentro:
            b["nascosto"] = True


def slug(path: Path) -> str:
    return str(path.relative_to(DOCS).with_suffix("")).replace("index", "").strip("/")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pagina", help="es. json/01-cos-e-json")
    ap.add_argument("--stampa", action="store_true")
    a = ap.parse_args()
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {"voce": "it_IT-paola-medium", "pagine": {}}
    # solo le pagine italiane: la lettura usa voci italiane, la versione inglese (docs/en/) non ha audio
    files = sorted(p for p in DOCS.rglob("*.md*")
                   if p.name != "index.mdx" and p.relative_to(DOCS).parts[0] != "en")
    if a.pagina:
        files = [p for p in files if slug(p) == a.pagina]
    tot = 0
    for f in files:
        b = estrai_file(f)
        marca_nascosti(f, b)
        vecchi = {x["id"]: x for x in manifest["pagine"].get(slug(f), {}).get("paragrafi", [])}
        for x in b:
            v = vecchi.get(x["id"])
            if v and v.get("t") == x["t"] and v.get("hc"):
                x["hc"] = v["hc"]
        manifest["pagine"][slug(f)] = {"paragrafi": b}
        tot += len(b)
        if a.stampa:
            print(f"\n===== {slug(f)} ({len(b)} paragrafi)")
            for x in b:
                flag = ("[PAUSA] " if x.get("pausa") else "") + ("[nascosto] " if x.get("nascosto") else "")
                print(f"- ({x['tipo']}) {flag}{x['voce'][:200]}")
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
    print(f"{len(files)} pagine, {tot} paragrafi → {MANIFEST.relative_to(RADICE)}")


if __name__ == "__main__":
    main()
