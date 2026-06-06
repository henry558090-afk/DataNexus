# One-click dev launcher: start backend (8000) and frontend (5179) in two new windows.
# Usage: run  .\start-dev.ps1  from the project root.
# Note: keep this script ASCII-only (PowerShell 5.1 misreads non-BOM UTF-8).
$root = $PSScriptRoot

Start-Process powershell -ArgumentList @(
    '-NoExit', '-Command',
    "Set-Location '$root\backend'; .\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8010"
)

Start-Process powershell -ArgumentList @(
    '-NoExit', '-Command',
    "Set-Location '$root\frontend'; npm run dev"
)

Write-Host ''
Write-Host 'Started: backend http://127.0.0.1:8010  /  frontend http://localhost:5179' -ForegroundColor Green
Write-Host 'Open http://localhost:5179  (login: admin / admin12345)' -ForegroundColor Green
