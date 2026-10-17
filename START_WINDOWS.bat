@echo off
setlocal
cd /d "%~dp0"
set "LAB_PYTHON=.venv-313\Scripts\python.exe"
py -3.13 -c "import sys; assert sys.version_info[:2] == (3, 13)" >nul 2>&1
if errorlevel 1 (
  echo Python 3.13 is vereist voor deze versie van Crypto Paper Lab.
  echo Installeer Python 3.13 met: py install 3.13
  echo Of download Python 3.13 voor Windows x64 via https://www.python.org/downloads/windows/
  pause
  exit /b 1
)
if not exist "%LAB_PYTHON%" (
  py -3.13 -m venv .venv-313
  if errorlevel 1 goto :failed
)
"%LAB_PYTHON%" -c "import sys; assert sys.version_info[:2] == (3, 13)"
if errorlevel 1 (
  echo De map .venv-313 bevat een andere Python-versie. Hernoem die map en probeer opnieuw.
  pause
  exit /b 1
)
"%LAB_PYTHON%" -m pip install --upgrade pip
if errorlevel 1 goto :failed
"%LAB_PYTHON%" -m pip install --only-binary=:all: -r requirements.txt
if errorlevel 1 goto :failed
echo.
echo Open in je browser: http://127.0.0.1:8501
start "" http://127.0.0.1:8501
"%LAB_PYTHON%" -m uvicorn app:app --host 127.0.0.1 --port 8501
pause
exit /b
:failed
echo.
echo Installatie mislukt. De app wordt niet gestart. Controleer de fout hierboven.
pause
exit /b 1
