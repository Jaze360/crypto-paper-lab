@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  py -m venv .venv
  if errorlevel 1 (echo Python 3 is vereist. & pause & exit /b 1)
  .venv\Scripts\python.exe -m pip install -r requirements.txt
  if errorlevel 1 (echo Installatie van packages mislukt. & pause & exit /b 1)
)
echo.
echo Open in je browser: http://127.0.0.1:8501
start "" http://127.0.0.1:8501
.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8501
pause
