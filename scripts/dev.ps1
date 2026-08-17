# Starts SentinelChain AI locally: backend (FastAPI) + frontend (Vite) in separate windows.
# Usage: powershell -ExecutionPolicy Bypass -File scripts/dev.ps1

$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"

if (-not (Test-Path (Join-Path $backend ".venv"))) {
    Write-Output "Creating backend virtual environment..."
    python -m venv (Join-Path $backend ".venv")
    & (Join-Path $backend ".venv\Scripts\python.exe") -m pip install -r (Join-Path $backend "requirements.txt")
}

if (-not (Test-Path (Join-Path $frontend "node_modules"))) {
    Write-Output "Installing frontend dependencies..."
    Push-Location $frontend
    npm install
    Pop-Location
}

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backend'; .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontend'; npm run dev"

Write-Output "Backend:  http://localhost:8000/docs"
Write-Output "Frontend: http://localhost:5173"
