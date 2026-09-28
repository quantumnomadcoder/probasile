#!/bin/sh
# Installation (une seule fois), sans toucher au Python du système.
#
#   ./installer_mac_linux.sh                 -> environnement DANS le dossier du programme (.venv)
#   ./installer_mac_linux.sh ~/venvs/outils  -> utilise (ou crée) cet environnement-là, partagé
#
# Si un environnement virtuel est déjà activé dans le terminal, le script demande s'il faut l'utiliser.
#   ./installer_mac_linux.sh --retirer       -> retire les raccourcis (menu, bureau, Applications)
#   --pause                                   -> attend « Entrée » à la fin (installation par double-clic)
cd "$(dirname "$0")" || exit 1
ICI="$(pwd)"

CIBLE=""
PAUSE=""
RETIRER=""
PROPOSER=""
for a in "$@"; do
    case "$a" in
        --pause) PAUSE=1 ;;
        --retirer) RETIRER=1 ;;
        --proposer-lancement) PROPOSER=1 ;;
        *) [ -z "$CIBLE" ] && CIBLE="$a" ;;
    esac
done

fin() {  # fin($code) : pause éventuelle puis sortie
    if [ -n "$PAUSE" ]; then
        echo
        printf "Appuyez sur Entrée pour fermer cette fenêtre. "
        read -r _
    fi
    exit "$1"
}

APPS="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
BUREAU="$(xdg-user-dir DESKTOP 2>/dev/null)"
[ -n "$BUREAU" ] || BUREAU="$HOME/Desktop"

if [ -n "$RETIRER" ]; then
    rm -f "$APPS/probasile.desktop" "$BUREAU/Probasile.desktop"
    rm -rf "$HOME/Applications/Probasile.app"
    command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$APPS" >/dev/null 2>&1
    echo "Raccourcis retirés. Pour tout désinstaller, supprimez ensuite le dossier du programme."
    fin 0
fi

if [ -z "$CIBLE" ] && [ -n "$VIRTUAL_ENV" ]; then
    printf "Un environnement virtuel est actif : %s\nL'utiliser pour ce programme ? [o/N] " "$VIRTUAL_ENV"
    read -r rep
    case "$rep" in o|O|oui|Oui) CIBLE="$VIRTUAL_ENV" ;; esac
fi
[ -z "$CIBLE" ] && CIBLE="$ICI/.venv"

# Python de base : jamais celui d'un environnement déjà actif
if [ -n "$VIRTUAL_ENV" ]; then
    BASE="$(python3 -c 'import sys; print(getattr(sys, "_base_executable", sys.executable))')"
else
    BASE="python3"
fi

# Linux (Debian, Ubuntu, Kali…) : proposer d'installer ce qui manque (venv, interface graphique)
if [ "$(uname)" != "Darwin" ] && command -v apt-get >/dev/null 2>&1 && [ -t 0 ]; then
    if ! "$BASE" -c "import venv, ensurepip, tkinter" >/dev/null 2>&1; then
        echo "Il manque des éléments de Python (python3-venv, python3-tk)."
        printf "Les installer maintenant ? Votre mot de passe sera demandé. [O/n] "
        read -r rep
        case "$rep" in
            n|N|non|Non) ;;
            *) sudo apt-get install -y python3-venv python3-full python3-tk ;;
        esac
    fi
fi

if [ ! -x "$CIBLE/bin/python" ]; then
    if ! "$BASE" -c "import venv, ensurepip" >/dev/null 2>&1; then
        echo "Le module venv de Python manque. Installez-le puis relancez ce script :"
        echo "  Kali / Debian / Ubuntu : sudo apt install python3-venv python3-full python3-tk"
        fin 1
    fi
    echo "Création de l'environnement : $CIBLE"
    "$BASE" -m venv "$CIBLE" || fin 1
fi

echo "Installation des modules dans : $CIBLE"
"$CIBLE/bin/python" -m pip install --quiet --upgrade pip
"$CIBLE/bin/python" -m pip install --quiet -r requirements.txt || fin 1

# on retient quel environnement utiliser (le lanceur le lit)
if [ "$CIBLE" = "$ICI/.venv" ]; then
    rm -f .environnement
else
    printf "%s\n" "$CIBLE" > .environnement
fi

if ! "$CIBLE/bin/python" -c "import tkinter" >/dev/null 2>&1; then
    echo
    echo "Attention : l'interface graphique (tkinter) n'est pas disponible."
    echo "  Kali / Debian / Ubuntu : sudo apt install python3-tk"
    echo "  macOS (Homebrew)       : brew install python-tk"
    echo "La ligne de commande fonctionne quand même (./lancer_mac_linux.command --help)."
fi

# ---- raccourcis : menu des applications, bureau (Linux) ; dossier Applications (macOS) ----
chmod +x "$ICI/lancer_mac_linux.command" 2>/dev/null
if [ "$(uname)" = "Darwin" ]; then
    APP="$HOME/Applications/Probasile.app"
    mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
    {
        echo '#!/bin/sh'
        printf 'exec "%s/lancer_mac_linux.command"\n' "$ICI"
    } > "$APP/Contents/MacOS/Probasile"
    chmod +x "$APP/Contents/MacOS/Probasile"
    cat > "$APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>Probasile</string>
  <key>CFBundleDisplayName</key><string>Probasile</string>
  <key>CFBundleIdentifier</key><string>org.probasile.Probasile</string>
  <key>CFBundleExecutable</key><string>Probasile</string>
  <key>CFBundleIconFile</key><string>Probasile</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleShortVersionString</key><string>1.0</string>
</dict></plist>
PLIST
    if command -v sips >/dev/null 2>&1 && command -v iconutil >/dev/null 2>&1; then
        SET="$(mktemp -d)/Probasile.iconset"
        mkdir -p "$SET"
        for t in 16 32 128 256 512; do
            sips -z $t $t "$ICI/icone_1024.png" --out "$SET/icon_${t}x${t}.png" >/dev/null 2>&1
            d=$((t * 2))
            sips -z $d $d "$ICI/icone_1024.png" --out "$SET/icon_${t}x${t}@2x.png" >/dev/null 2>&1
        done
        iconutil -c icns "$SET" -o "$APP/Contents/Resources/Probasile.icns" >/dev/null 2>&1
    fi
    touch "$APP"
    echo "Raccourci créé : Probasile dans le dossier Applications de votre compte (glissez-le dans le Dock)."
else
    mkdir -p "$APPS"
    cat > "$APPS/probasile.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Version=1.0
Name=Probasile
GenericName=Sources et rédaction – droit des étrangers
Comment=Personne n'est illégal·e. Papiers pour toustes.
Exec="$ICI/lancer_mac_linux.command"
Path=$ICI
Icon=$ICI/icone.png
Terminal=false
Categories=Office;
Keywords=asile;droit;étrangers;sources;notes;annexes;
StartupWMClass=Probasile
StartupNotify=true
DESKTOP
    chmod +x "$APPS/probasile.desktop"
    command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$APPS" >/dev/null 2>&1
    if [ -d "$BUREAU" ]; then
        cp "$APPS/probasile.desktop" "$BUREAU/Probasile.desktop"
        chmod +x "$BUREAU/Probasile.desktop"
        command -v gio >/dev/null 2>&1 && gio set "$BUREAU/Probasile.desktop" metadata::trusted true >/dev/null 2>&1
    fi
    echo "Raccourcis créés : Probasile dans le menu des applications (catégorie Bureautique) et sur le bureau."
fi

echo
echo "Terminé. Environnement utilisé : $CIBLE"
echo "Lancez Probasile depuis le menu des applications ou l'icône du bureau."
echo "Pour tout désinstaller : ./installer_mac_linux.sh --retirer, puis supprimer le dossier du programme$( [ "$CIBLE" = "$ICI/.venv" ] || echo " (l'environnement $CIBLE, partagé, reste en place)")."
if [ -n "$PROPOSER" ]; then
    echo
    printf "Lancer Probasile maintenant ? [O/n] "
    read -r rep
    case "$rep" in
        n|N|non|Non) ;;
        *) nohup "$ICI/lancer_mac_linux.command" >/dev/null 2>&1 &
           PAUSE=""
           sleep 2 ;;
    esac
fi
fin 0
