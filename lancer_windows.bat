@echo off
chcp 65001 >nul
py "%~dp0collecte.py" %*
if errorlevel 1 pause
