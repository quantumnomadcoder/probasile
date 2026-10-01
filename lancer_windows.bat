@echo off
chcp 65001 >nul
where py >nul 2>nul
if not errorlevel 1 (
    py "%~dp0collecte.py" %*
) else (
    python "%~dp0collecte.py" %*
)
if errorlevel 1 pause
