@echo off
setlocal
cd /d "%~dp0"

echo [1/2] Starting backend on http://127.0.0.1:8000 ...
start "ZengCloud Backend" cmd /k "cd /d "%~dp0backend" && "%~dp0.venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000"

echo [2/2] Starting frontend on http://localhost:5173 ...
start "ZengCloud Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

timeout /t 3 >nul
start http://localhost:5173/

echo.
echo Opened browser. Login: admin / admin123
echo Keep the two new windows open while using the app.
pause
