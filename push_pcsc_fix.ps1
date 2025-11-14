# UTF-8 encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

Set-Location "\\nas\nas_1\card_reader_improved"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PC/SC権限修正をプッシュ" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/4] 変更されたファイルを確認中..." -ForegroundColor Yellow
git status --short
Write-Host ""

Write-Host "[2/4] ファイルを追加中..." -ForegroundColor Yellow
git add fix_pcsc_permission_raspberry.sh
git add QUICK_FIX_PCSC.md
git add UPDATE_START_PI.md
Write-Host "  追加完了" -ForegroundColor Green
Write-Host ""

Write-Host "[3/4] コミット中..." -ForegroundColor Yellow
$commitMessage = "Add PC/SC permission fix script and troubleshooting guides

- Add fix_pcsc_permission_raspberry.sh: Script to fix PC/SC access permission issues
- Add QUICK_FIX_PCSC.md: Quick guide for fixing PC/SC access denied errors
- Add UPDATE_START_PI.md: Guide for updating start_pi.sh to latest version"

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

