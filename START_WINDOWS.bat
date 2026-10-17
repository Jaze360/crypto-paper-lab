@echo off
cd /d "%~dp0"
py -3.13 start_lab.py
if errorlevel 1 echo Starten mislukt. Controleer de melding hierboven.
pause
