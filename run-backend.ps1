$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
& .\.venv\Scripts\Activate.ps1
docker start trackit-premium-db 2>$null | Out-Null
python backend\manage.py runserver
