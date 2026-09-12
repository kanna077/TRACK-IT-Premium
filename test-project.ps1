$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
& .\.venv\Scripts\Activate.ps1

$env:DB_ENGINE = "sqlite"
$env:EMAIL_HOST_USER = ""
python backend\manage.py test
python backend\manage.py makemigrations --check --dry-run

Set-Location frontend
npm run typecheck
npm run lint
