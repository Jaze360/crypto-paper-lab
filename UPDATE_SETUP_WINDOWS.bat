@echo off
echo Eenmalige GitHub-verbinding voor de private updater.
echo Installeer GitHub CLI indien nodig: winget install --id GitHub.cli -e
echo Open na installatie dit bestand opnieuw vanuit een nieuw venster.
where gh >nul 2>&1
if errorlevel 1 (
  echo GitHub CLI is nog niet beschikbaar.
  pause
  exit /b 1
)
gh auth login --hostname github.com --web --git-protocol https
pause
