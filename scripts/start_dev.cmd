@echo off
REM Windows wrapper to run the PowerShell start script
SET SCRIPT_DIR=%~dp0
Powershell -ExecutionPolicy Bypass -NoProfile -File "%SCRIPT_DIR%start_dev.ps1" -Open
