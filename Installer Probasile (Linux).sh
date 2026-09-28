#!/bin/sh
# Double-cliquez sur ce fichier pour installer Probasile (Linux).
# S'il s'ouvre dans un éditeur de texte : clic droit -> « Exécuter comme un programme »
# (ou « Lancer », « Run as a Program » selon le gestionnaire de fichiers).
cd "$(dirname "$0")" || exit 1
ICI="$(pwd)"
chmod +x installer_mac_linux.sh lancer_mac_linux.command 2>/dev/null
MOI="$ICI/$(basename "$0")"

if [ -t 1 ]; then
    exec ./installer_mac_linux.sh --pause --proposer-lancement
fi

# lancé sans terminal (double-clic) : on en ouvre un pour afficher l'installation
if command -v gnome-terminal >/dev/null 2>&1; then exec gnome-terminal -- "$MOI"; fi
if command -v konsole >/dev/null 2>&1; then exec konsole -e "$MOI"; fi
if command -v xfce4-terminal >/dev/null 2>&1; then exec xfce4-terminal -x "$MOI"; fi
if command -v mate-terminal >/dev/null 2>&1; then exec mate-terminal -x "$MOI"; fi
if command -v qterminal >/dev/null 2>&1; then exec qterminal -e "\"$MOI\""; fi
if command -v lxterminal >/dev/null 2>&1; then exec lxterminal -e "\"$MOI\""; fi
if command -v x-terminal-emulator >/dev/null 2>&1; then exec x-terminal-emulator -e "$MOI"; fi
if command -v xterm >/dev/null 2>&1; then exec xterm -e "$MOI"; fi

# aucun terminal trouvé : installation sans fenêtre, compte rendu dans installation.txt
./installer_mac_linux.sh > installation.txt 2>&1
if command -v notify-send >/dev/null 2>&1; then
    notify-send "Probasile" "Installation terminée : voir installation.txt dans le dossier du programme."
fi
