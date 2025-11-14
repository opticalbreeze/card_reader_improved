# UTF-8 encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

Set-Location "\\nas\nas_1\card_reader_improved"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  コード整理とPC/SC修正をプッシュ" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/4] 変更されたファイルを確認中..." -ForegroundColor Yellow
git status --short
Write-Host ""

Write-Host "[2/4] ファイルを追加中..." -ForegroundColor Yellow
git add pi_client.py
git add attendance-client-fixed.service
git add fix_pcscd_config.sh
git add cleanup_and_fix.sh
git add FINAL_PCSC_FIX.md
Write-Host "  追加完了" -ForegroundColor Green
Write-Host ""

Write-Host "[3/4] コミット中..." -ForegroundColor Yellow
$commitMessage = "Cleanup code and fix PC/SC connection issue

- Simplify PC/SC detection logic in pi_client.py (remove redundant retry/wait code)
- Remove duplicate LCD import code
- Simplify attendance-client-fixed.service (remove unnecessary settings)
- Add PCSCLITE_CSOCK_NAME environment variable to service file
- Add fix_pcscd_config.sh script to fix PC/SC service configuration
- Add cleanup_and_fix.sh script to remove temporary files
- Add FINAL_PCSC_FIX.md documentation

This addresses the root cause: PC/SC service configuration needs to allow connections from systemd services."

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

