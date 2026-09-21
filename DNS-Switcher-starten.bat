@echo off
setlocal
py -3 --version >nul 2>&1
if %errorlevel%==0 (
    start "" pyw.exe "%~dp0dns_switcher.py"
    exit /b 0
)
python --version >nul 2>&1
if %errorlevel%==0 (
    pythonw.exe "%~dp0dns_switcher.py"
    exit /b 0
)
echo Python 3 wurde nicht gefunden.
echo Bitte Python von https://www.python.org/downloads/windows/ installieren
echo und dabei "Add Python to PATH" aktivieren.
pause
