@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "PS_SCRIPT=%SCRIPT_DIR%uninstall_jarvis.ps1"

if not exist "%PS_SCRIPT%" (
    echo File not found: "%PS_SCRIPT%"
    pause
    exit /b 1
)

echo Jarvis uninstall
echo.
echo 1. Remove program only
echo 2. Remove program and user data
echo 3. Cancel
echo.
choice /c 123 /n /m "Choose an option: "

if errorlevel 3 (
    echo.
    echo Uninstall cancelled.
    pause
    exit /b 0
)

set "REMOVE_DATA_ARG="
if errorlevel 2 set "REMOVE_DATA_ARG=-RemoveData"

echo.
echo Requesting permission to uninstall Jarvis...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
 "$proc = Start-Process PowerShell -Verb RunAs -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File ""%PS_SCRIPT%"" %REMOVE_DATA_ARG%' -PassThru -Wait; exit $proc.ExitCode"

if errorlevel 1 (
    echo.
    echo Uninstaller failed.
    pause
    exit /b 1
)

echo.
echo Uninstall completed.
pause
