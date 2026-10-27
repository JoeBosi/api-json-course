#!/usr/bin/env python3
"""Imposta la password che accende l'API di prova dal sito.

La password NON viene mai scritta da nessuna parte: nel file .env finisce solo il suo hash
scrypt (CORSO_API_PASSWORD_HASH). Il file viene creato con permessi 600 (solo root lo legge).

Uso (via SSH, sul VPS):
    cd /root/Developer/corso-api-json && python3 deploy/imposta-password-api.py

Poi serve un riavvio del servizio perché rilegga il .env:
    systemctl restart corso-api-json
"""
from __future__ import annotations

import getpass
import os
import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RADICE / "api"))

from app.interruttore import genera_hash  # noqa: E402  (dopo sys.path)

CHIAVE = "CORSO_API_PASSWORD_HASH"
ENV = RADICE / ".env"


def chiedi() -> str:
    for _ in range(3):
        p1 = getpass.getpass("Password per accendere l'API di prova: ")
        if len(p1) < 8:
            print("  Troppo corta: almeno 8 caratteri.\n")
            continue
        p2 = getpass.getpass("Ripetila: ")
        if p1 != p2:
            print("  Le due password non coincidono.\n")
            continue
        return p1
    sys.exit("Niente da fare: password non impostata.")


def scrivi(hash_: str) -> None:
    righe = ENV.read_text().splitlines() if ENV.exists() else []
    righe = [r for r in righe if not r.startswith(f"{CHIAVE}=")]
    if righe and righe[-1].strip():
        righe.append("")
    righe += ["# Hash scrypt della password che accende l'API di prova (deploy/imposta-password-api.py)",
              f"{CHIAVE}={hash_}"]
    fd = os.open(ENV, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write("\n".join(righe) + "\n")
    os.chmod(ENV, 0o600)


def main() -> None:
    if not sys.stdin.isatty():
        sys.exit("Serve un terminale: lancialo via SSH, non da uno script.")
    print(f"File di destinazione: {ENV}  (permessi 600, la password NON viene salvata)\n")
    hash_ = genera_hash(chiedi())
    scrivi(hash_)
    print(f"\nFatto: in {ENV} c'è solo l'hash.")
    print("Ora riavvia il servizio perché lo rilegga:\n    systemctl restart corso-api-json")


if __name__ == "__main__":
    main()
