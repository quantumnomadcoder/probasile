@echo off
chcp 65001 >nul
rem Double-cliquez sur ce fichier pour installer Probasile (une seule fois).
set "ICI=%~dp0"
echo Installation des modules necessaires (a faire une seule fois)...
py -m pip install --user -r "%ICI%requirements.txt"
if errorlevel 1 (
    echo.
    echo Echec : verifiez que Python 3 est installe ^(https://www.python.org/downloads/^),
    echo avec la case "Add Python to PATH" cochee, puis relancez ce fichier.
    pause
    exit /b 1
)

rem Raccourcis dans le menu Demarrer et sur le bureau (sans fenetre noire : pythonw)
for /f "usebackq delims=" %%i in (`py -c "import sys,os;print(os.path.join(os.path.dirname(sys.executable),'pythonw.exe'))"`) do set "PYW=%%i"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$s=New-Object -ComObject WScript.Shell; foreach($d in @([Environment]::GetFolderPath('Programs'),[Environment]::GetFolderPath('Desktop'))){ $l=$s.CreateShortcut((Join-Path $d 'Probasile.lnk')); $l.TargetPath=$env:PYW; $l.Arguments=[char]34+$env:ICI+'collecte.py'+[char]34; $l.WorkingDirectory=$env:ICI; $l.IconLocation=$env:ICI+'icone.ico'; $l.Description='Probasile'; $l.Save() }"

echo.
echo Termine. Probasile est dans le menu Demarrer et sur le bureau.
echo Pour l'epingler a la barre des taches : clic droit sur Probasile dans le menu
echo Demarrer, puis "Epingler a la barre des taches".
echo.
set "REP="
set /p REP="Lancer Probasile maintenant ? [O/n] "
if /i not "%REP%"=="n" start "" "%PYW%" "%ICI%collecte.py"
