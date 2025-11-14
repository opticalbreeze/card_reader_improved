# UTF-8 encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

Set-Location "\\nas\nas_1\card_reader_improved"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  変更をコミット・プッシュ" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/4] 変更されたファイルを確認中..." -ForegroundColor Yellow
git status --short
Write-Host ""

Write-Host "[2/4] ファイルを追加中..." -ForegroundColor Yellow
git add win_client.py
git add setup_autostart_fixed.sh
git add RASPBERRY_AUTOSTART_GUIDE.md
git add push_sleep_fix.ps1
git add PUSH_INSTRUCTIONS.md
Write-Host "  追加完了" -ForegroundColor Green
Write-Host ""

Write-Host "[3/4] コミット中..." -ForegroundColor Yellow
$commitMessage = "Add Windows sleep recovery fix and Raspberry Pi autostart setup script

- Fix Windows sleep recovery: Improve card reader detection after sleep/wake
  - Enhanced periodic reader check with automatic restart
  - Improved nfcpy reader error handling (reinitialize on consecutive errors)
  - Improved PC/SC reader error handling (refresh reader objects after sleep)
  - Added reader monitoring restart functionality
- Add Raspberry Pi autostart setup script (setup_autostart_fixed.sh)
- Add Raspberry Pi autostart guide (RASPBERRY_AUTOSTART_GUIDE.md)"

git commit -m $commitMessage

if ($LASTEXITCODE -eq 0) {
    Write-Host "  コミット完了" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "[4/4] GitHubにプッシュ中..." -ForegroundColor Yellow
    git push origin main
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "  ✅ プッシュ成功！" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Red
        Write-Host "  ❌ プッシュ失敗" -ForegroundColor Red
        Write-Host "========================================" -ForegroundColor Red
        Write-Host ""
        Write-Host "手動で実行してください:" -ForegroundColor Yellow
        Write-Host "  git push origin main" -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "  ❌ コミット失敗" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
}

Write-Host ""
Write-Host "Enterキーを押すと終了します..."
Read-Host | Out-Null

