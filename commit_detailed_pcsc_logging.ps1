# UTF-8 encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

Set-Location "\\nas\nas_1\card_reader_improved"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PC/SC詳細ログ追加をプッシュ" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/4] 変更されたファイルを確認中..." -ForegroundColor Yellow
git status --short
Write-Host ""

Write-Host "[2/4] ファイルを追加中..." -ForegroundColor Yellow
git add pi_client.py
Write-Host "  追加完了" -ForegroundColor Green
Write-Host ""

Write-Host "[3/4] コミット中..." -ForegroundColor Yellow
$commitMessage = "Add detailed PC/SC logging and error handling

- Add detailed logging for PC/SC socket preparation check
- Add explicit environment variable setting (PCSC_SOCKET_PATH, PCSCLITE_CSOCK_NAME)
- Increase retry count from 3 to 5 with longer wait times (2s, 4s, 6s, 8s)
- Add detailed error logging with error type, message, and traceback
- Increase wait time after socket ready from 0.5s to 1.0s
- This will help diagnose why PC/SC works manually but not in systemd service"

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

