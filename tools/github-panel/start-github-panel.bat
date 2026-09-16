@echo off
setlocal
cd /d "%~dp0"

echo Starting ZengCloud GitHub Panel...
echo Browser will open http://127.0.0.1:8787/
echo.

if exist "%~dp0..\..\.venv\Scripts\python.exe" (
  "%~dp0..\..\.venv\Scripts\python.exe" "%~dp0server.py"
) else (
  python "%~dp0server.py"
)

pause
