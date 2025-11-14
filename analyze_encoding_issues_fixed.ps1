# ============================================================================
# Encoding Issues Analysis Script
# ============================================================================

# Set UTF-8 encoding at the start
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
try {
    chcp 65001 | Out-Null
} catch {
    # Ignore if chcp is not available
}

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "  Encoding Issues Analysis" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

# Workspace path
$workspacePath = "\\nas\nas_1\card_reader_improved"
Set-Location $workspacePath

Write-Host "[1] PowerShell Encoding Settings" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
Write-Host "Console.OutputEncoding: $([Console]::OutputEncoding.EncodingName)" -ForegroundColor Cyan
Write-Host "Console.InputEncoding: $([Console]::InputEncoding.EncodingName)" -ForegroundColor Cyan
Write-Host "OutputEncoding: $($OutputEncoding.EncodingName)" -ForegroundColor Cyan
Write-Host "Default: $([System.Text.Encoding]::Default.EncodingName)" -ForegroundColor Cyan
Write-Host ""

Write-Host "[2] Git Encoding Settings" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
$gitConfig = @(
    "i18n.commitencoding",
    "i18n.logoutputencoding",
    "core.quotepath",
    "core.precomposeunicode"
)

foreach ($key in $gitConfig) {
    $value = git config --get $key
    if ($value) {
        Write-Host "  $key = $value" -ForegroundColor Green
    } else {
        Write-Host "  $key = (not set)" -ForegroundColor Gray
    }
}
Write-Host ""

Write-Host "[3] Environment Variables (Encoding Related)" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
$envVars = @(
    "PYTHONIOENCODING",
    "LANG",
    "LC_ALL",
    "LC_CTYPE"
)

foreach ($var in $envVars) {
    $value = [Environment]::GetEnvironmentVariable($var)
    if ($value) {
        Write-Host "  $var = $value" -ForegroundColor Green
    } else {
        Write-Host "  $var = (not set)" -ForegroundColor Gray
    }
}
Write-Host ""

Write-Host "[4] File Encoding Check" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
$testFiles = @("pi_client.py", "config.py", "README.md")
foreach ($file in $testFiles) {
    if (Test-Path $file) {
        $bytes = [System.IO.File]::ReadAllBytes($file)
        $text = [System.IO.File]::ReadAllText($file, [System.Text.Encoding]::UTF8)
        
        # BOM check
        $hasBOM = ($bytes.Length -ge 3) -and ($bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF)
        $bomStatus = if ($hasBOM) { "Yes (UTF-8 BOM)" } else { "No" }
        
        Write-Host "  $file" -ForegroundColor Cyan
        Write-Host "    BOM: $bomStatus" -ForegroundColor $(if ($hasBOM) { "Yellow" } else { "Green" })
        Write-Host "    Size: $($bytes.Length) bytes" -ForegroundColor Gray
        
        # Check if Japanese characters are included
        $hasJapanese = $text -match "[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]"
        $japaneseStatus = if ($hasJapanese) { "Contains Japanese" } else { "No Japanese" }
        Write-Host "    Japanese: $japaneseStatus" -ForegroundColor $(if ($hasJapanese) { "Green" } else { "Gray" })
        Write-Host ""
    }
}

Write-Host "[5] Git commit message encoding check" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
Write-Host "Recent commit messages:" -ForegroundColor Cyan
$commits = git log --oneline -5 --pretty=format:"%h|%s"
foreach ($commit in $commits) {
    $parts = $commit -split '\|', 2
    $hash = $parts[0]
    $message = $parts[1]
    Write-Host "  $hash : $message" -ForegroundColor $(if ($message -match "[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]") { "Green" } else { "Yellow" })
}
Write-Host ""

Write-Host "[6] PowerShell code page check" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
$codePage = [Console]::OutputEncoding.CodePage
Write-Host "Current code page: $codePage" -ForegroundColor Cyan
Write-Host "  65001 = UTF-8" -ForegroundColor Gray
Write-Host "  932 = Shift-JIS (Japanese Windows)" -ForegroundColor Gray
Write-Host ""

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "Analysis complete" -ForegroundColor Green
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Recommended fixes:" -ForegroundColor Yellow
Write-Host "  1. Set PowerShell encoding to UTF-8" -ForegroundColor White
Write-Host "  2. Set Git commit message encoding to UTF-8" -ForegroundColor White
Write-Host "  3. Set environment variable PYTHONIOENCODING to UTF-8" -ForegroundColor White
Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Enter to exit..." -ForegroundColor Yellow
Read-Host | Out-Null

