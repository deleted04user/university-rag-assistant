# Lance l'API (8001) + le site statique (8080) et ouvre le navigateur.
$root = $PSScriptRoot
$py = Join-Path $root "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Error "Venv introuvable. Exécutez d'abord dans backend : python -m venv .venv ; .\.venv\Scripts\pip install -r requirements.txt"
    exit 1
}

foreach ($p in 8001, 8080) {
    Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue |
        ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
}

Start-Process -FilePath $py -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8001" `
    -WorkingDirectory (Join-Path $root "backend") -WindowStyle Normal

Start-Sleep -Seconds 2

Start-Process -FilePath "python" -ArgumentList "-m", "http.server", "8080", "--bind", "127.0.0.1" `
    -WorkingDirectory (Join-Path $root "frontend") -WindowStyle Normal

Start-Sleep -Seconds 1
Start-Process "http://127.0.0.1:8080/"

Write-Host "API : http://127.0.0.1:8001/docs"
Write-Host "Site : http://127.0.0.1:8080/"
