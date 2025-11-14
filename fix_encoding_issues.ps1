# ============================================================================
# Fix Encoding Issues Script
# ============================================================================

# Set UTF-8 encoding at the start
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
try {
    chcp 65001 | Out-Null
} catch {
    # Ignore if chcp is not available
}

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "  Fix Encoding Issues" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

# Workspace path
$workspacePath = "\\nas\nas_1\card_reader_improved"
Set-Location $workspacePath

# 1. PowerShell Input Encoding
Write-Host "[1] Setting PowerShell Input Encoding to UTF-8..." -ForegroundColor Yellow
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
Write-Host "  Done" -ForegroundColor Green
Write-Host ""

# 2. Git Encoding Settings
Write-Host "[2] Setting Git encoding configuration..." -ForegroundColor Yellow
git config --global i18n.commitencoding utf-8
git config --global i18n.logoutputencoding utf-8
git config --global core.quotepath false

# Local repository settings
git config i18n.commitencoding utf-8
git config i18n.logoutputencoding utf-8
git config core.quotepath false

Write-Host "  Global settings:" -ForegroundColor Cyan
Write-Host "    i18n.commitencoding = utf-8" -ForegroundColor Green
Write-Host "    i18n.logoutputencoding = utf-8" -ForegroundColor Green
Write-Host "    core.quotepath = false" -ForegroundColor Green
Write-Host "  Local repository settings updated" -ForegroundColor Green
Write-Host ""

# 3. Environment Variables
Write-Host "[3] Setting environment variables..." -ForegroundColor Yellow
try {
    [Environment]::SetEnvironmentVariable("PYTHONIOENCODING", "utf-8", "User")
    Write-Host "  PYTHONIOENCODING = utf-8 (User environment variable)" -ForegroundColor Green
    Write-Host "    Note: This will take effect in new PowerShell sessions" -ForegroundColor Gray
} catch {
    Write-Host "  Warning: Failed to set PYTHONIOENCODING: $_" -ForegroundColor Yellow
}

# Set for current session
$env:PYTHONIOENCODING = "utf-8"
Write-Host "  PYTHONIOENCODING = utf-8 (Current session)" -ForegroundColor Green
Write-Host ""

# 4. PowerShell Profile Setup
Write-Host "[4] Setting up PowerShell profile..." -ForegroundColor Yellow
$profileContent = @"
# UTF-8 Encoding Settings
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
`$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
try {
    chcp 65001 | Out-Null
} catch {
    # Ignore if chcp is not available
}
"@

if (Test-Path $PROFILE) {
    $currentProfile = Get-Content $PROFILE -Raw -ErrorAction SilentlyContinue
    if ($currentProfile -notmatch "UTF-8 Encoding Settings") {
        Add-Content $PROFILE "`n$profileContent"
        Write-Host "  Added UTF-8 settings to PowerShell profile" -ForegroundColor Green
    } else {
        Write-Host "  PowerShell profile already contains UTF-8 settings" -ForegroundColor Cyan
    }
} else {
    # Create profile directory if it doesn't exist
    $profileDir = Split-Path $PROFILE -Parent
    if (-not (Test-Path $profileDir)) {
        New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
    }
    Set-Content $PROFILE $profileContent
    Write-Host "  Created PowerShell profile with UTF-8 settings" -ForegroundColor Green
}
Write-Host "  Profile path: $PROFILE" -ForegroundColor Gray
Write-Host ""

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "Fix Complete" -ForegroundColor Green
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Summary:" -ForegroundColor Yellow
Write-Host "  - PowerShell input encoding set to UTF-8 (current session)" -ForegroundColor White
Write-Host "  - Git commit/log encoding set to UTF-8 (global and local)" -ForegroundColor White
Write-Host "  - PYTHONIOENCODING environment variable set" -ForegroundColor White
Write-Host "  - PowerShell profile configured for UTF-8" -ForegroundColor White
Write-Host ""
Write-Host "Notes:" -ForegroundColor Yellow
Write-Host "  - Environment variable changes require a new PowerShell session" -ForegroundColor White
Write-Host "  - Git commit messages will be saved in UTF-8 from now on" -ForegroundColor White
Write-Host "  - Existing commit messages with mojibake cannot be fixed automatically" -ForegroundColor White
Write-Host ""
Write-Host "To verify settings:" -ForegroundColor Yellow
Write-Host "  git config --list | Select-String encoding" -ForegroundColor White
Write-Host "  `$env:PYTHONIOENCODING" -ForegroundColor White
Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Enter to exit..." -ForegroundColor Yellow
Read-Host | Out-Null

