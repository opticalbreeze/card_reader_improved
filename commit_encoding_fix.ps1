# UTF-8 encoding fix
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

# Change to script directory (UNC path supported in PowerShell)
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host "Current directory: $(Get-Location)" -ForegroundColor Cyan
Write-Host ""

# Check if it's a git repository
if (-not (Test-Path .git)) {
    Write-Host "Error: Not a git repository!" -ForegroundColor Red
    Write-Host "Current path: $(Get-Location)" -ForegroundColor Yellow
    exit 1
}

Write-Host "Adding files..." -ForegroundColor Green
git add pi_client.py win_client.py config.py lcd_i2c.py test_led.py .vscode/settings.json setup_utf8.bat README_ENCODING_FIX.md

Write-Host ""
Write-Host "Committing changes..." -ForegroundColor Green
git commit -m "Fix character encoding issues - UTF-8 output support for Windows"

Write-Host ""
Write-Host "Pushing to GitHub..." -ForegroundColor Green
git push origin main

Write-Host ""
Write-Host "Done!" -ForegroundColor Green
Write-Host ""
Read-Host "Press Enter to exit"

