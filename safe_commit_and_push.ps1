# ============================================================================
# Safe Commit and Push Script
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
Write-Host "  Safe Commit and Push" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

# Workspace path
$workspacePath = "\\nas\nas_1\card_reader_improved"
Set-Location $workspacePath

# Check current commit
Write-Host "[1] Current commit:" -ForegroundColor Yellow
git log --oneline -1
Write-Host ""

# Check remote status
Write-Host "[2] Checking remote status..." -ForegroundColor Yellow
git fetch origin
$localCommit = git rev-parse HEAD
$remoteCommit = git rev-parse origin/main

if ($localCommit -ne $remoteCommit) {
    Write-Host "  Warning: Local branch is different from remote" -ForegroundColor Yellow
    Write-Host "  Local:  $localCommit" -ForegroundColor Cyan
    Write-Host "  Remote: $remoteCommit" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Remote commits ahead:" -ForegroundColor Yellow
    git log --oneline HEAD..origin/main
    Write-Host ""
    Write-Host "  Do you want to pull remote changes first? (Y/N)" -ForegroundColor Yellow
    Write-Host "  Warning: This may overwrite local changes!" -ForegroundColor Red
    $pullConfirm = Read-Host
    if ($pullConfirm -eq "Y" -or $pullConfirm -eq "y") {
        Write-Host "  Pulling remote changes..." -ForegroundColor Yellow
        git pull origin main
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  Pull failed. Please resolve conflicts manually." -ForegroundColor Red
            exit 1
        }
        Write-Host "  Pull successful" -ForegroundColor Green
    } else {
        Write-Host "  Skipping pull. Will force push later if needed." -ForegroundColor Yellow
    }
    Write-Host ""
}

# Show files to add
Write-Host "[3] Files to be added:" -ForegroundColor Yellow
git status --short
Write-Host ""

# Add encoding fix files
Write-Host "[4] Adding encoding fix files..." -ForegroundColor Yellow
git add analyze_encoding_issues.ps1
git add analyze_encoding_issues_fixed.ps1
git add fix_encoding_issues.ps1
git add ENCODING_FIX_SUMMARY.md
Write-Host "  Encoding fix files added" -ForegroundColor Green
Write-Host ""

# Check if there are other modified files
$modifiedFiles = git status --porcelain | Where-Object { $_ -match '^ M' }
if ($modifiedFiles) {
    Write-Host "  Other modified files detected:" -ForegroundColor Yellow
    git status --short | Where-Object { $_ -match '^ M' }
    Write-Host ""
    Write-Host "  Do you want to add these files too? (Y/N)" -ForegroundColor Yellow
    $addAllConfirm = Read-Host
    if ($addAllConfirm -eq "Y" -or $addAllConfirm -eq "y") {
        git add -A
        Write-Host "  All files added" -ForegroundColor Green
    }
    Write-Host ""
}

# Commit
Write-Host "[5] Committing changes..." -ForegroundColor Yellow
$commitMessage = "Fix encoding issues - Add PowerShell scripts for encoding analysis and fixes"
git commit -m $commitMessage
if ($LASTEXITCODE -eq 0) {
    Write-Host "  Commit successful" -ForegroundColor Green
} else {
    Write-Host "  Commit failed or no changes to commit" -ForegroundColor Yellow
    Write-Host "  Checking status..." -ForegroundColor Yellow
    git status --short
}
Write-Host ""

# Push
Write-Host "[6] Pushing to GitHub..." -ForegroundColor Yellow
git push origin main
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Push failed. Remote is ahead." -ForegroundColor Red
    Write-Host ""
    Write-Host "  Options:" -ForegroundColor Yellow
    Write-Host "    1. Pull and merge: git pull origin main" -ForegroundColor White
    Write-Host "    2. Force push (dangerous): git push origin main --force" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Do you want to force push? (Y/N)" -ForegroundColor Yellow
    Write-Host "  Warning: This will overwrite remote changes!" -ForegroundColor Red
    $forceConfirm = Read-Host
    if ($forceConfirm -eq "Y" -or $forceConfirm -eq "y") {
        git push origin main --force
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  Force push successful" -ForegroundColor Green
        } else {
            Write-Host "  Force push failed" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "  Push cancelled" -ForegroundColor Yellow
    }
} else {
    Write-Host "  Push successful" -ForegroundColor Green
}
Write-Host ""

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "Complete" -ForegroundColor Green
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Enter to exit..." -ForegroundColor Yellow
Read-Host | Out-Null

