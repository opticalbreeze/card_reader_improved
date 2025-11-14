# UTF-8 encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

Set-Location "\\nas\nas_1\card_reader_improved"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Windows版スリープ復帰修正をプッシュ" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/3] 変更されたファイルを確認中..." -ForegroundColor Yellow
git status --short

Write-Host ""
Write-Host "[2/3] ファイルを追加中..." -ForegroundColor Yellow
git add win_client.py

Write-Host ""
Write-Host "[3/3] コミット・プッシュ中..." -ForegroundColor Yellow
git commit -m "Fix Windows sleep recovery - Improve card reader detection after sleep/wake"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "GitHubにプッシュ中..." -ForegroundColor Yellow
    git push origin main
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ プッシュ成功！" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "❌ プッシュ失敗。手動で実行してください:" -ForegroundColor Red
        Write-Host "   git push origin main" -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "❌ コミット失敗" -ForegroundColor Red
}

Write-Host ""
Write-Host "Enterキーを押すと終了します..."
Read-Host | Out-Null

