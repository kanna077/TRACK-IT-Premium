$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example. Update the database and email values."
}

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

docker compose up -d db redis

python backend\manage.py migrate
python backend\manage.py check
python backend\manage.py seed_demo

Set-Location frontend
npm install
npm run typecheck

Write-Host ""
Write-Host "TRACK-IT setup completed."
Write-Host "Run .\run-backend.ps1 and .\run-frontend.ps1 in separate terminals."
