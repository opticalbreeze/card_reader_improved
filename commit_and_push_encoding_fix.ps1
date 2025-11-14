# ============================================================================
# Commit and Push Encoding Fix Scripts
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
Write-Host "  Commit and Push Encoding Fix Scripts" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

# Workspace path
$workspacePath = "\\nas\nas_1\card_reader_improved"
Set-Location $workspacePath

# Check Git status
Write-Host "[1] Checking Git status..." -ForegroundColor Yellow
$status = git status --porcelain
if ($status) {
    Write-Host "Changes detected:" -ForegroundColor Cyan
    git status --short
    Write-Host ""
} else {
    Write-Host "No changes detected" -ForegroundColor Green
    Write-Host ""
}

# Show what will be committed
Write-Host "[2] Files to be committed:" -ForegroundColor Yellow
git status --short
Write-Host ""

# Ask for confirmation
Write-Host "Do you want to commit and push these changes? (Y/N)" -ForegroundColor Yellow
$confirm = Read-Host
if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host "Cancelled" -ForegroundColor Yellow
    exit 0
}

# Add files
Write-Host "[3] Adding files..." -ForegroundColor Yellow
git add analyze_encoding_issues.ps1
git add analyze_encoding_issues_fixed.ps1
git add fix_encoding_issues.ps1
git add ENCODING_FIX_SUMMARY.md
Write-Host "Files added" -ForegroundColor Green
Write-Host ""

# Commit
Write-Host "[4] Committing changes..." -ForegroundColor Yellow
$commitMessage = "Fix encoding issues - Add PowerShell scripts for encoding analysis and fixes"
git commit -m $commitMessage
if ($LASTEXITCODE -eq 0) {
    Write-Host "Commit successful" -ForegroundColor Green
} else {
    Write-Host "Commit failed" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Push
Write-Host "[5] Pushing to GitHub..." -ForegroundColor Yellow
git push origin main
if ($LASTEXITCODE -eq 0) {
    Write-Host "Push successful" -ForegroundColor Green
} else {
    Write-Host "Push failed" -ForegroundColor Red
    Write-Host "You may need to pull first: git pull origin main" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "Complete" -ForegroundColor Green
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Enter to exit..." -ForegroundColor Yellow
Read-Host | Out-Null

