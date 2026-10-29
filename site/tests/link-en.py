"""Controlla i link interni del sito compilato (site/dist).

Per ogni pagina HTML: ogni href interno deve esistere in dist; dalle pagine inglesi i link alle
pagine del corso devono restare in /en/ (altrimenti il lettore inglese finisce sulla pagina
italiana senza volerlo). Uso: python3 tests/link-en.py [dist]
"""
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit, unquote

DIST = Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
TECNICI = ("/api/", "/_astro/", "/pagefind/", "/swagger/", "/audio/", "/favicon", "/sitemap", "/llms", "/robots")

def esiste(percorso: str) -> bool:
    p = DIST / unquote(percorso).lstrip("/")
    return p.is_file() or (p / "index.html").is_file()

rotti, fuori_lingua, pagine = [], [], 0
for html in sorted(DIST.rglob("*.html")):
    pagina = "/" + str(html.relative_to(DIST)).removesuffix("index.html")
    pagine += 1
    testo = html.read_text(encoding="utf-8")
    # il link all'altra lingua (IT/EN nella barra, selettore) è voluto: ha hreflang
    voluti = set(re.findall(r'<a[^>]*href="([^"]+)"[^>]*hreflang=', testo)) | set(re.findall(r'<a[^>]*hreflang="[^"]*"[^>]*href="([^"]+)"', testo))
    for href in re.findall(r'href="([^"]+)"', testo):
        if href in voluti:
            continue
        u = urlsplit(href)
        if u.scheme or u.netloc or not u.path.startswith("/"):
            continue
        if u.path.startswith("/api/"):
            continue                                   # serviti dall'API, non dal sito statico
        if not esiste(u.path):
            rotti.append((pagina, href))
        if pagina.startswith("/en/") and not u.path.startswith("/en/") and not u.path.startswith(TECNICI) and u.path != "/":
            fuori_lingua.append((pagina, href))

print(f"pagine controllate: {pagine}")
print(f"link interni rotti: {len(rotti)}")
for p, h in rotti[:20]: print("  ROTTO", p, "→", h)
print(f"link da /en/ verso pagine italiane: {len(fuori_lingua)}")
for p, h in sorted(set(fuori_lingua))[:40]: print("  IT", p, "→", h)
sys.exit(1 if rotti else 0)
