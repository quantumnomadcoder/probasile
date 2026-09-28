@echo off
chcp 65001 >nul
rem Retire les raccourcis de Probasile (menu Demarrer, bureau).
powershell -NoProfile -ExecutionPolicy Bypass -Command "foreach($d in @([Environment]::GetFolderPath('Programs'),[Environment]::GetFolderPath('Desktop'))){ Remove-Item -ErrorAction SilentlyContinue (Join-Path $d 'Probasile.lnk') }"
echo Raccourcis retires. Pour tout desinstaller, supprimez ensuite le dossier du programme.
pause
