# ============================================================================
# Push Encoding Fix Scripts to GitHub
# ============================================================================

# Set UTF-8 encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
try {
    chcp 65001 | Out-Null
} catch {
    # Ignore if chcp is not available
}

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "  Push Encoding Fix Scripts to GitHub" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

# Workspace path
$workspacePath = "\\nas\nas_1\card_reader_improved"
Set-Location $workspacePath

# Add only encoding fix files
Write-Host "[1] Adding encoding fix files..." -ForegroundColor Yellow
git add analyze_encoding_issues.ps1
git add analyze_encoding_issues_fixed.ps1
git add fix_encoding_issues.ps1
git add ENCODING_FIX_SUMMARY.md
Write-Host "  Files added" -ForegroundColor Green
Write-Host ""

# Check status
Write-Host "[2] Files to be committed:" -ForegroundColor Yellow
git status --short
Write-Host ""

# Commit
Write-Host "[3] Committing..." -ForegroundColor Yellow
$commitMessage = "Fix encoding issues - Add PowerShell scripts for encoding analysis and fixes"
git commit -m $commitMessage
if ($LASTEXITCODE -ne 0) {
    Write-Host "  No changes to commit or commit failed" -ForegroundColor Yellow
    git status --short
} else {
    Write-Host "  Commit successful" -ForegroundColor Green
}
Write-Host ""

# Push (force if needed)
Write-Host "[4] Pushing to GitHub..." -ForegroundColor Yellow
git push origin main
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Push failed. Remote is ahead." -ForegroundColor Yellow
    Write-Host "  Using force push to overwrite remote changes..." -ForegroundColor Yellow
    git push origin main --force
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Force push successful" -ForegroundColor Green
    } else {
        Write-Host "  Force push failed" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  Push successful" -ForegroundColor Green
}
Write-Host ""

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "Complete" -ForegroundColor Green
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next step: Pull on Raspberry Pi" -ForegroundColor Yellow
Write-Host "  cd ~/Desktop/attendance/card_reader_improved" -ForegroundColor White
Write-Host "  git pull origin main" -ForegroundColor White
Write-Host ""
Write-Host "Press Enter to exit..." -ForegroundColor Yellow
Read-Host | Out-Null

