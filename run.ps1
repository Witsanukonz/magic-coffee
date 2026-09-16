param([int]$Port = 8000)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$pythonPath = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.12 or later is required.' }
    & $pythonPath -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
}
& $pythonPath -c 'import django, PIL' 2>$null
if ($LASTEXITCODE -ne 0) {
    & $pythonPath -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
}
& $pythonPath manage.py migrate --noinput
if ($LASTEXITCODE -ne 0) { throw 'Database migration failed.' }
& $pythonPath manage.py seed_demo
if ($LASTEXITCODE -ne 0) { throw 'Demo setup failed.' }
& $pythonPath manage.py check
if ($LASTEXITCODE -ne 0) { throw 'Django checks failed.' }
Write-Host "`nMAGIC COFFEE is ready at http://127.0.0.1:$Port/" -ForegroundColor Green
Write-Host 'Local demo: demo_admin / demo_customer. Default password: MagicDemo!2026'
Write-Host 'This script uses .venv directly; it does not activate your PowerShell session.'
Write-Host 'Press Ctrl+C to stop the server.'
& $pythonPath manage.py runserver "127.0.0.1:$Port"
