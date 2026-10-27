#!/usr/bin/env python3
"""Voce del corso con OpenAI TTS (modello gpt-4o-mini-tts).

Legge audio/manifest.json (campo `t`: testo con l'inglese scritto in inglese) e salva un MP3 per
paragrafo in site/public/audio/oa/<hash>.mp3. Il modello legge da solo i termini inglesi con la
pronuncia inglese: niente marcature, basta il campo `instructions` per tono e ritmo.
Incrementale: l'hash dipende da modello + voce + istruzioni + testo, quindi si rigenera solo ciò
che cambia.

Credenziali: OPENAI_API_KEY in .env (radice del progetto) o nell'ambiente.

Uso (dalla cartella api/):
  uv run python ../audio/genera_openai.py --stima                # quanto costa, senza chiamare l'API
  uv run python ../audio/genera_openai.py --campioni             # pagina /campioni-voce.html
  uv run python ../audio/genera_openai.py --voce marin [--pagina json/01-cos-e-json]
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import html
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx

RADICE = Path(__file__).resolve().parent.parent
MANIFEST = RADICE / "audio" / "manifest.json"
OUT = RADICE / "site" / "public" / "audio" / "oa"
CAMPIONI = RADICE / "site" / "public" / "audio-campioni"
URL = "https://api.openai.com/v1/audio/speech"
MODELLO = "gpt-4o-mini-tts"
VOCI_CAMPIONE = ["marin", "cedar", "sage", "coral"]
PARALLELE = 4

# Guida di lettura: una voce narrante da corso, non da telegiornale. L'inglese va letto in inglese.
ISTRUZIONI = (
    "Sei la voce narrante di un corso di programmazione in italiano. "
    "Leggi in italiano, con tono chiaro, calmo e amichevole, come chi spiega a un collega: "
    "ritmo naturale, pause vere sulla punteggiatura, nessuna enfasi da pubblicità. "
    "I termini tecnici, gli acronimi, i nomi di comandi, opzioni, funzioni e formati sono inglesi "
    "e vanno pronunciati con pronuncia inglese naturale (per esempio JSON, API, array, string, "
    "curl, query, parsing, endpoint, header, payload, request, response, primary key, foreign key), "
    "senza italianizzarli e senza compitarli lettera per lettera se sono parole. "
    "Le sigle che si leggono lettera per lettera (API, URL, HTTP, SQL, ID) vanno scandite "
    "all'inglese. Leggi i simboli e la punteggiatura come farebbe un insegnante a voce: "
    "non nominare le virgolette, non dire 'trattino trattino'."
)

# gpt-4o-mini-tts, prezzi al 24/09/2026 (developers.openai.com/api/docs/models/gpt-4o-mini-tts)
PREZZO_INPUT_M = 0.60      # $ per 1M token di testo (input + instructions)
PREZZO_AUDIO_M = 12.00     # $ per 1M token audio generati
TOKEN_AUDIO_AL_SECONDO = 12.5   # ~1,5 cent al minuto


def chiave() -> str:
    env = RADICE / ".env"
    if env.exists():
        for riga in env.read_text().splitlines():
            if "=" in riga and not riga.lstrip().startswith("#"):
                k, v = riga.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("'\""))
    k = os.environ.get("OPENAI_API_KEY")
    if not k:
        sys.exit("Manca OPENAI_API_KEY (in .env nella radice del progetto).")
    return k


def impronta(testo: str, voce: str, istruzioni: str) -> str:
    return hashlib.sha1(f"{MODELLO}|{voce}|{istruzioni}|{testo}".encode()).hexdigest()[:12]


def sintetizza(client: httpx.Client, testo: str, voce: str, istruzioni: str, dest: Path) -> None:
    corpo = {"model": MODELLO, "voice": voce, "input": testo,
             "instructions": istruzioni, "response_format": "mp3"}
    for tentativo in range(6):
        try:
            r = client.post(URL, json=corpo)
        except httpx.RequestError as e:
            print(f"  rete: {e}; riprovo", file=sys.stderr); time.sleep(5 * (tentativo + 1)); continue
        if r.status_code == 200:
            dest.write_bytes(r.content); return
        if r.status_code in (429, 500, 502, 503, 529):
            attesa = float(r.headers.get("retry-after", 0) or 0) or 5 * (tentativo + 1)
            print(f"  {r.status_code}: riprovo tra {attesa:.0f}s", file=sys.stderr); time.sleep(attesa); continue
        raise SystemExit(f"OpenAI {r.status_code}: {r.text[:300]}")
    raise SystemExit("OpenAI: troppi errori consecutivi")


def durata_mp3(p: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", str(p)], capture_output=True, text=True)
    return round(float(r.stdout.strip() or 0), 2)


def costo(testi: list[str], istruzioni: str) -> tuple[float, float, float]:
    """(dollari input, dollari audio, minuti stimati) — token ≈ caratteri/4, audio ≈ 14 char/s."""
    car = sum(len(t) for t in testi)
    tok_in = (car + len(istruzioni) * len(testi)) / 4
    secondi = car / 14
    return (tok_in / 1e6 * PREZZO_INPUT_M,
            secondi * TOKEN_AUDIO_AL_SECONDO / 1e6 * PREZZO_AUDIO_M,
            secondi / 60)


def pagina_campioni(righe: list[tuple[str, str, str]], testi: dict[str, str]) -> None:
    out = ["<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width'>",
           "<title>Campioni voce</title><style>body{font:16px system-ui;max-width:52rem;margin:2rem auto;padding:0 1rem}"
           "td{padding:.3rem .6rem;vertical-align:middle}audio{height:2rem}</style>",
           "<h1>Campioni di voce per il corso</h1>",
           "<p>Stessi testi, voci diverse (OpenAI <code>gpt-4o-mini-tts</code>). Voci generate da "
           "intelligenza artificiale, non umane.</p><table>"]
    for voce, nome, fn in righe:
        out.append(f"<tr><td><b>{voce}</b></td><td>{nome}</td>"
                   f"<td><audio controls preload=none src='/audio-campioni/{fn}'></audio></td></tr>")
    out.append("</table><h2>Testi</h2>" + "".join(f"<h3>{k}</h3><p>{html.escape(t)}</p>" for k, t in testi.items()))
    (RADICE / "site" / "public" / "campioni-voce.html").write_text("\n".join(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voce", default="marin")
    ap.add_argument("--pagina")
    ap.add_argument("--campioni", action="store_true")
    ap.add_argument("--stima", action="store_true", help="costo stimato, senza chiamare l'API")
    ap.add_argument("--istruzioni", help="sostituisce la guida di lettura predefinita")
    a = ap.parse_args()
    m = json.loads(MANIFEST.read_text())
    istruzioni = a.istruzioni or ISTRUZIONI
    pagine = {a.pagina: m["pagine"][a.pagina]} if a.pagina else m["pagine"]
    testi = [x["t"] for p in pagine.values() for x in p["paragrafi"]]

    if a.stima:
        ci, ca, minuti = costo(testi, istruzioni)
        print(f"{len(testi)} paragrafi, {sum(len(t) for t in testi):,} caratteri → ~{minuti:.0f} min di audio\n"
              f"costo stimato: ${ci:.2f} di testo + ${ca:.2f} di audio = ${ci + ca:.2f}")
        return

    with httpx.Client(timeout=120, headers={"Authorization": f"Bearer {chiave()}"}) as client:
        if a.campioni:
            CAMPIONI.mkdir(parents=True, exist_ok=True)
            esempi = {
                "curl": next(x["t"] for x in m["pagine"]["json/01-cos-e-json"]["paragrafi"] if x["tipo"] == "curl"),
                "teoria": next(x["t"] for x in m["pagine"]["db-api/05-relazioni-e-chiavi-esterne"]["paragrafi"] if len(x["t"]) > 250),
            }
            righe = []
            for v in VOCI_CAMPIONE:
                for nome, t in esempi.items():
                    f = CAMPIONI / f"{v}-{nome}.mp3"
                    if not f.exists():
                        sintetizza(client, t, v, istruzioni, f)
                    righe.append((v, nome, f.name))
            pagina_campioni(righe, esempi)
            ci, ca, _ = costo([t for _ in VOCI_CAMPIONE for t in esempi.values()], istruzioni)
            print(f"{len(righe)} campioni → /campioni-voce.html (costo ~${ci + ca:.2f})")
            return

        OUT.mkdir(parents=True, exist_ok=True)
        cloud = m.setdefault("cloud", {})
        durate = cloud.setdefault("durate", {})
        da_fare = {}
        for p in pagine.values():
            for x in p["paragrafi"]:
                x["hc"] = impronta(x["t"], a.voce, istruzioni)
                if not (OUT / f"{x['hc']}.mp3").exists():
                    da_fare[x["hc"]] = x["t"]
        ci, ca, minuti = costo(list(da_fare.values()), istruzioni)
        print(f"{len(da_fare)} paragrafi da generare con la voce {a.voce} "
              f"(~{minuti:.0f} min di audio, costo stimato ${ci + ca:.2f})")

        fatti = 0
        with cf.ThreadPoolExecutor(PARALLELE) as pool:
            futuri = {pool.submit(sintetizza, client, t, a.voce, istruzioni, OUT / f"{h}.mp3"): h
                      for h, t in da_fare.items()}
            for f in cf.as_completed(futuri):
                f.result()
                h = futuri[f]; durate[h] = durata_mp3(OUT / f"{h}.mp3"); fatti += 1
                if fatti % 25 == 0:
                    print(f"  {fatti}/{len(da_fare)}", file=sys.stderr)
                    MANIFEST.write_text(json.dumps(m, ensure_ascii=False, indent=1))
        for p in pagine.values():
            for x in p["paragrafi"]:
                durate.setdefault(x["hc"], durata_mp3(OUT / f"{x['hc']}.mp3"))
        cloud.update(voce=a.voce, dir="oa", nome=f"{a.voce}, OpenAI", modello=MODELLO, istruzioni=istruzioni)
        MANIFEST.write_text(json.dumps(m, ensure_ascii=False, indent=1))
        tot = sum(durate.get(x["hc"], 0) for p in m["pagine"].values() for x in p["paragrafi"] if x.get("hc"))
        print(f"fatto: {tot / 60:.0f} minuti. Ora `uv run python ../audio/genera.py` riscrive il manifest pubblico.")


if __name__ == "__main__":
    main()
