# UTF-8 encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

Set-Location "\\nas\nas_1\card_reader_improved"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  分析と修正をプッシュ" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/4] 変更されたファイルを確認中..." -ForegroundColor Yellow
git status --short
Write-Host ""

Write-Host "[2/4] ファイルを追加中..." -ForegroundColor Yellow
git add FAILURE_REPORT.md
git add WHY_MANUAL_VS_AUTOSTART_DIFFERENCE.md
git add check_pcscd_config.sh
git add pi_client.py
git add attendance-client-fixed.service
Write-Host "  追加完了" -ForegroundColor Green
Write-Host ""

Write-Host "[3/4] コミット中..." -ForegroundColor Yellow
$commitMessage = "Add failure analysis and fix GUI/GPIO issues

- Add FAILURE_REPORT.md: Comprehensive analysis of failed attempts
- Add WHY_MANUAL_VS_AUTOSTART_DIFFERENCE.md: Detailed analysis of why manual vs autostart differs
- Add check_pcscd_config.sh: Script to check PC/SC service configuration and logs
- Fix GUI startup: Only start GUI if DISPLAY environment variable is set (fixes systemd service issue)
- Fix GPIO duplicate initialization: Handle existing PWM objects gracefully
- Add PCSCLITE_CSOCK_NAME environment variable to service file

Key findings:
- PC/SC service may reject connections from systemd service sessions
- Need to check /etc/pcscd/pcscd.conf configuration
- Need to check PC/SC service logs for connection rejection reasons"

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

