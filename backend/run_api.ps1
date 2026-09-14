# Démarre l'API sur un port utilisable (8000 souvent réservé sous Windows → 8001).
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Host "Créez d'abord le venv : python -m venv .venv && .\.venv\Scripts\pip install -r requirements.txt"
    exit 1
}
$port = 8001
Write-Host "Démarrage sur http://127.0.0.1:$port (doc: /docs)"
& .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port $port
