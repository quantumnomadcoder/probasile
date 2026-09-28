#!/bin/sh
# Double-cliquez sur ce fichier pour installer Probasile (macOS).
cd "$(dirname "$0")" || exit 1
chmod +x installer_mac_linux.sh lancer_mac_linux.command 2>/dev/null
exec ./installer_mac_linux.sh --pause --proposer-lancement
