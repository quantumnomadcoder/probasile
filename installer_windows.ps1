# Installateur Probasile pour Windows (lancé par installer_windows.bat).
# 1. Trouve Python 3.9 ou plus récent (avec tkinter) ; sinon l'installe pour l'utilisateur, sans droits
#    d'administrateur (winget, ou l'installateur officiel de python.org).
# 2. Installe les modules nécessaires (requirements.txt).
# 3. Crée les raccourcis (menu Démarrer, bureau) et propose de lancer Probasile.
$ErrorActionPreference = 'Continue'
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}
$ici = Split-Path -Parent $MyInvocation.MyCommand.Path
$VERSION_PY = '3.12.10'

function Fin($code) {
    Write-Host ''
    Read-Host 'Appuyez sur Entrée pour fermer cette fenêtre' | Out-Null
    exit $code
}

function Python-OK($exe) {
    if (-not $exe -or -not (Test-Path $exe)) { return $false }
    if ($exe -like '*\WindowsApps\*') { return $false }   # raccourci du Microsoft Store, pas un vrai Python
    & $exe -c "import sys, tkinter; sys.exit(0 if sys.version_info >= (3, 9) else 1)" 2>$null
    return ($LASTEXITCODE -eq 0)
}

function Trouver-Python {
    $candidats = @()
    if (Get-Command py -ErrorAction SilentlyContinue) {
        $p = & py -3 -c "import sys; print(sys.executable)" 2>$null
        if ($LASTEXITCODE -eq 0 -and $p) { $candidats += $p.Trim() }
    }
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { $candidats += $cmd.Source }
    foreach ($motif in @("$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe",
                         "$env:ProgramFiles\Python3*\python.exe",
                         "${env:ProgramFiles(x86)}\Python3*\python.exe")) {
        $candidats += (Get-ChildItem $motif -ErrorAction SilentlyContinue | Sort-Object FullName -Descending |
                       ForEach-Object { $_.FullName })
    }
    foreach ($c in $candidats) { if (Python-OK $c) { return $c } }
    return $null
}

Write-Host '=== Installation de Probasile ===' -ForegroundColor Cyan
Write-Host ''
Write-Host '1/3  Recherche de Python…'
$py = Trouver-Python
if (-not $py) {
    Write-Host '     Python n''est pas installé (ou trop ancien) : installation automatique, quelques minutes…' -ForegroundColor Yellow
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host '     Installation par winget (Microsoft)…'
        winget install -e --id Python.Python.3.12 --scope user --silent --accept-package-agreements --accept-source-agreements | Out-Host
        $py = Trouver-Python
    }
    if (-not $py) {
        $arch = $env:PROCESSOR_ARCHITECTURE
        if ($arch -eq 'ARM64') { $nom = "python-$VERSION_PY-arm64.exe" }
        elseif ($arch -eq 'AMD64' -or $env:PROCESSOR_ARCHITEW6432 -eq 'AMD64') { $nom = "python-$VERSION_PY-amd64.exe" }
        else { $nom = "python-$VERSION_PY.exe" }
        $url = "https://www.python.org/ftp/python/$VERSION_PY/$nom"
        $tmp = Join-Path $env:TEMP $nom
        Write-Host "     Téléchargement de Python $VERSION_PY depuis python.org…"
        try {
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            $ProgressPreference = 'SilentlyContinue'
            Invoke-WebRequest -Uri $url -OutFile $tmp -UseBasicParsing
            Write-Host '     Installation de Python (pour cet utilisateur)…'
            Start-Process -FilePath $tmp -Wait -ArgumentList '/quiet', 'InstallAllUsers=0', 'PrependPath=1',
                'Include_launcher=1', 'Include_tcltk=1', 'Include_pip=1', 'Include_test=0'
            Remove-Item $tmp -ErrorAction SilentlyContinue
        } catch {
            Write-Host "     Échec du téléchargement : $($_.Exception.Message)" -ForegroundColor Red
        }
        $py = Trouver-Python
    }
    if (-not $py) {
        Write-Host ''
        Write-Host 'Python n''a pas pu être installé automatiquement.' -ForegroundColor Red
        Write-Host 'Installez-le à la main depuis https://www.python.org/downloads/ (cochez « Add Python to PATH »),'
        Write-Host 'puis relancez ce fichier.'
        Start-Process 'https://www.python.org/downloads/windows/'
        Fin 1
    }
}
$v = & $py -c "import sys; print('%d.%d.%d' % sys.version_info[:3])"
Write-Host "     Python $v : $py" -ForegroundColor Green

Write-Host ''
Write-Host '2/3  Installation des modules nécessaires (une seule fois)…'
& $py -m pip install --user --disable-pip-version-check -r (Join-Path $ici 'requirements.txt')
if ($LASTEXITCODE -ne 0) {
    Write-Host ''
    Write-Host 'Échec de l''installation des modules. Vérifiez la connexion Internet, puis relancez ce fichier.' -ForegroundColor Red
    Fin 1
}
& $py -c "import lxml, pypdf, requests, pycountry" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Un module manque encore : relancez ce fichier.' -ForegroundColor Red
    Fin 1
}
Write-Host '     Modules installés.' -ForegroundColor Green

Write-Host ''
Write-Host '3/3  Raccourcis (menu Démarrer et bureau)…'
$pyw = Join-Path (Split-Path $py) 'pythonw.exe'
if (-not (Test-Path $pyw)) { $pyw = $py }
$s = New-Object -ComObject WScript.Shell
foreach ($d in @([Environment]::GetFolderPath('Programs'), [Environment]::GetFolderPath('Desktop'))) {
    $l = $s.CreateShortcut((Join-Path $d 'Probasile.lnk'))
    $l.TargetPath = $pyw
    $l.Arguments = '"' + (Join-Path $ici 'collecte.py') + '"'
    $l.WorkingDirectory = $ici
    $l.IconLocation = (Join-Path $ici 'icone.ico')
    $l.Description = 'Probasile'
    $l.Save()
}
Write-Host ''
Write-Host 'Terminé. Probasile est dans le menu Démarrer et sur le bureau.' -ForegroundColor Green
Write-Host 'Pour l''épingler à la barre des tâches : clic droit sur Probasile dans le menu Démarrer,'
Write-Host 'puis « Épingler à la barre des tâches ».'
Write-Host ''
$rep = Read-Host 'Lancer Probasile maintenant ? [O/n]'
if ($rep -notmatch '^[nN]') { Start-Process -FilePath $pyw -ArgumentList ('"' + (Join-Path $ici 'collecte.py') + '"') -WorkingDirectory $ici }
exit 0
