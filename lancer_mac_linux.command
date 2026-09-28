#!/bin/sh
# Lance le programme avec l'environnement choisi à l'installation, quel que soit
# l'environnement éventuellement actif dans le terminal.
cd "$(dirname "$0")" || exit 1
# lancé depuis le menu ou le bureau (sans terminal) : les erreurs vont dans journal_erreurs.txt
[ -t 2 ] || exec 2>>journal_erreurs.txt
if [ -f .environnement ] && [ -x "$(cat .environnement)/bin/python" ]; then
    exec "$(cat .environnement)/bin/python" collecte.py "$@"
elif [ -x .venv/bin/python ]; then
    exec .venv/bin/python collecte.py "$@"
else
    echo "Programme non installé : lancez d'abord ./installer_mac_linux.sh"
    exit 1
fi
