"""Assembla una pagina inglese da un modello con la prosa tradotta e i blocchi di codice presi
tali e quali dalla pagina italiana, così codice, comandi e output restano identici.

Uso: python3 scripts/traduci.py <pagina-it.mdx> <pagina-en.mdx> < modello
Nel modello: ⟦B0⟧, ⟦B1⟧… = n-esimo blocco ``` della pagina italiana;
             ⟦C0⟧, ⟦C1⟧… = n-esimo `<Curl cmd={`…`}` (il comando, senza la spiegazione).
Ogni blocco deve comparire esattamente una volta, altrimenti lo script si ferma.
"""
import re
import sys

it_path, en_path = sys.argv[1:3]
src = open(it_path, encoding='utf-8').read()
modello = sys.stdin.read()
B = re.findall(r"^[ \t]*```[\s\S]*?^[ \t]*```", src, flags=re.M)
C = re.findall(r"<Curl cmd=\{`[\s\S]*?`\}", src)
for nome, lista in (('B', B), ('C', C)):
    usati = [int(n) for n in re.findall(rf"⟦{nome}(\d+)⟧", modello)]
    if sorted(usati) != list(range(len(lista))):
        sys.exit(f"{nome}: nel modello {sorted(usati)}, nella pagina italiana {len(lista)} blocchi")
    for i, testo in enumerate(lista):
        modello = modello.replace(f"⟦{nome}{i}⟧", testo.lstrip(' \t') if nome == 'B' else testo)
open(en_path, 'w', encoding='utf-8').write(modello)
print(f"{en_path}: {len(B)} blocchi di codice, {len(C)} comandi curl copiati")
