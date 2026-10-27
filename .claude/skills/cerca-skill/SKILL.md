---
name: cerca-skill
description: Procedura per trovare, valutare e installare in locale (nel progetto) una skill per Claude Code prima di fare un lavoro a mano. Usala all'inizio di ogni task tecnico non banale, quando serve una tecnologia/libreria/formato nuovo, o quando Giuseppe parla di skill, plugin o strumenti.
allowed-tools:
  - Bash(npx -y skills@latest:*)
  - Bash(npx skills:*)
  - Bash(ls:*)
  - Bash(cat:*)
  - WebFetch
  - WebSearch
  - Read
---

# Cerca skill — prima cerca, poi costruisci

## 0. Vale la pena?
Salta solo per: domande, letture di file, modifiche banali a codice già in contesto.
Altrimenti fai **un** giro di ricerca e riporta l'esito in una riga ("nessuna adatta, faccio a mano" va bene).

## 1. Inventario locale
```bash
ls .claude/skills/
cat skills-lock.json
```
Se una skill locale copre il task, usala e fermati qui.

## 2. Ricerca pubblica
```bash
npx -y skills@latest find "<parola chiave>"           # indice skills.sh (installazioni = segnale)
npx -y skills@latest find "<query>" --owner anthropics
npx -y skills@latest add <owner>/<repo> --list        # cosa contiene un repo
npx -y skills@latest use <owner>/<repo>@<skill>       # legge il SKILL.md senza installare
```
Fonti da preferire: repo ufficiale del vendor (es. `fastapi/fastapi`), `anthropics/skills`,
`vercel-labs/skills`. I plugin dei marketplace non sono portabili: preferire la skill equivalente.

## 3. Controllo qualità (tutti e quattro, altrimenti niente)
- **Provenienza**: owner ufficiale o noto, repo con storia.
- **Freschezza**: aggiornata, allineata alle versioni in uso.
- **Lettura**: apri il `SKILL.md` (`use` o WebFetch). Niente esfiltrazioni, pacchetti a sorpresa,
  richieste di credenziali. Le skill girano con i permessi dell'agente: leggerle non è opzionale.
- **Aderenza**: risolve *questo* task, non uno vicino.

## 4. Installazione portabile
```bash
npx -y skills@latest add <owner>/<repo> --skill <nome> -a claude-code --copy -y
ls .claude/skills/<nome>/ && grep '"<nome>"' skills-lock.json
```
`--copy` obbligatorio (senza, la CLI crea symlink alla cache globale che si rompono copiando la
cartella). Mai `-g`.

## 5. Nessuna adatta
Lavora a mano. Se il task si ripeterà, crea una skill locale: `.claude/skills/<nome>/SKILL.md`
(frontmatter `name` + `description` con i casi d'uso, poi la procedura passo-passo).

## 6. Traccia
Una riga in `docs/JOURNAL.md`: skill, fonte, task che l'ha motivata, data.
