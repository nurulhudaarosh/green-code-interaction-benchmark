@echo off
setlocal
cd /d "%~dp0"

if "%~1"=="" (
    echo.
    echo Green Code Interaction Benchmark
    echo.
    echo Usage:
    echo   sc.bat init
    echo   sc.bat submit
    echo   sc.bat status
    echo   sc.bat reset
    echo.
    exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0sc.ps1" %*
exit /b %ERRORLEVEL%
