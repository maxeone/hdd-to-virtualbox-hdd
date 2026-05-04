@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "APP=%SCRIPT_DIR%vbox_boot_builder\virtualbox_boot_builder.py"

if not exist "%APP%" (
    echo No encuentro la app:
    echo %APP%
    pause
    exit /b 1
)

net session >nul 2>&1
if not "%errorlevel%"=="0" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%ComSpec%' -Verb RunAs -ArgumentList '/c """"%~f0""""'"
    exit /b
)

python "%APP%"
