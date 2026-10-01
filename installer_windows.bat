@echo off
chcp 65001 >nul
rem Double-cliquez sur ce fichier pour installer Probasile (une seule fois).
rem Il installe aussi Python si besoin (pour cet utilisateur, sans droits d'administrateur).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer_windows.ps1"
