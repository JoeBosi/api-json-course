#!/usr/bin/env python3
"""Sintetizza con Piper un MP3 per ogni paragrafo di audio/manifest.json che non esiste ancora.

Output: site/public/audio/<hash>.mp3 (il nome è l'hash del testo parlato: stesso testo in due
pagine = un solo file; testo cambiato = file nuovo) e site/public/audio/manifest.json per il
player. Modello in audio/voci/ (scaricato se manca). File orfani rimossi.

Uso: uv run --with piper-tts python audio/genera.py [--processi 3] [--pagina json/01-cos-e-json]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.request
import wave
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
MANIFEST = RADICE / "audio" / "manifest.json"
VOCI = RADICE / "audio" / "voci"
OUT = RADICE / "site" / "public" / "audio"
HF = "https://huggingface.co/rhasspy/piper-voices/resolve/main/it/it_IT/{nome}/{qualita}/it_IT-{nome}-{qualita}.onnx"

_voice = None


def modello(voce: str) -> Path:
    VOCI.mkdir(parents=True, exist_ok=True)
    onnx = VOCI / f"{voce}.onnx"
    _, nome, qualita = voce.split("-")
    for suffisso in ("", ".json"):
        f = VOCI / f"{voce}.onnx{suffisso}"
        if not f.exists():
            url = HF.format(nome=nome, qualita=qualita) + suffisso
            print(f"scarico {url}", file=sys.stderr)
            urllib.request.urlretrieve(url, f)
    return onnx


def _init(voce: str):
    global _voice
    from piper import PiperVoice
    _voice = PiperVoice.load(str(modello(voce)))


def _sintetizza(args: tuple[str, str]) -> tuple[str, float]:
    h, testo = args
    from piper.config import SynthesisConfig
    wav_path = OUT / f"{h}.wav"
    with wave.open(str(wav_path), "wb") as w:
        _voice.synthesize_wav(testo, w, syn_config=SynthesisConfig(length_scale=1.05))
    with wave.open(str(wav_path)) as w:
        durata = w.getnframes() / w.getframerate()
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(wav_path), "-codec:a", "libmp3lame", "-b:a", "64k",
                    "-ar", "22050", "-ac", "1", str(OUT / f"{h}.mp3")], check=True)
    wav_path.unlink()
    return h, round(durata, 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--processi", type=int, default=3)
    ap.add_argument("--pagina")
    ap.add_argument("--solo-manifest", action="store_true",
                    help="scrive solo il manifest pubblico, senza generare MP3 con Piper "
                         "(la lettura usa la voce del browser)")
    a = ap.parse_args()
    m = json.loads(MANIFEST.read_text())
    voce = m.get("voce", "it_IT-paola-medium")
    OUT.mkdir(parents=True, exist_ok=True)
    durate = m.setdefault("durate", {})
    pagine = {a.pagina: m["pagine"][a.pagina]} if a.pagina else m["pagine"]
    da_fare = {}
    if not a.solo_manifest:
        for p in pagine.values():
            for x in p["paragrafi"]:
                if not (OUT / f"{x['hash']}.mp3").exists() or x["hash"] not in durate:
                    da_fare[x["hash"]] = x["voce"]
    print(f"{len(da_fare)} paragrafi da sintetizzare con {voce} ({a.processi} processi)")
    if da_fare:
        modello(voce)
        with ProcessPoolExecutor(a.processi, initializer=_init, initargs=(voce,)) as ex:
            for n, (h, d) in enumerate(ex.map(_sintetizza, list(da_fare.items()), chunksize=4), 1):
                durate[h] = d
                if n % 50 == 0:
                    print(f"  {n}/{len(da_fare)}", file=sys.stderr)
                    MANIFEST.write_text(json.dumps(m, ensure_ascii=False, indent=1))
    vivi = {x["hash"] for p in m["pagine"].values() for x in p["paragrafi"]}
    if not a.pagina and not a.solo_manifest:
        for f in OUT.glob("*.mp3"):
            if f.stem not in vivi:
                f.unlink(); durate.pop(f.stem, None)
    MANIFEST.write_text(json.dumps(m, ensure_ascii=False, indent=1))
    # manifest pubblico: per pagina, solo ciò che serve al player
    cloud = m.get("cloud") or {}
    dirc = OUT / cloud.get("dir", "-")
    pub = {"voce": voce, "cloud": {k: cloud[k] for k in ("voce", "dir", "nome") if k in cloud} or None, "pagine": {}}
    for slug, p in m["pagine"].items():
        pub["pagine"][slug] = [{k: v for k, v in x.items() if k in ("id", "tipo", "hash", "n", "voce", "t", "pausa", "nascosto")}
                               | {"d": durate.get(x["hash"])}
                               | ({"hc": x["hc"], "dc": cloud.get("durate", {}).get(x["hc"])} if x.get("hc") and (dirc / f"{x['hc']}.mp3").exists() else {})
                               for x in p["paragrafi"]]
    (OUT / "manifest.json").write_text(json.dumps(pub, ensure_ascii=False))
    tot = sum(durate.get(x["hash"], 0) for p in m["pagine"].values() for x in p["paragrafi"])
    print(f"audio totale: {tot/60:.1f} minuti, {sum(f.stat().st_size for f in OUT.glob('*.mp3'))/1e6:.1f} MB")


if __name__ == "__main__":
    main()
