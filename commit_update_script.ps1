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
git add update_from_github.sh start_pi.sh check_service_status.sh fix_auto_start.sh

Write-Host ""
Write-Host "Committing changes..." -ForegroundColor Green
git commit -m "Add UTF-8 encoding support to shell scripts and update script"

Write-Host ""
Write-Host "Pushing to GitHub..." -ForegroundColor Green
git push origin main

Write-Host ""
Write-Host "Done!" -ForegroundColor Green
Write-Host ""
Read-Host "Press Enter to exit"

