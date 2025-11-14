# ============================================================================
# 最終的な修正をコミット・プッシュ
# ============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
try {
    chcp 65001 | Out-Null
} catch {
}

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "  最終的な修正をコミット・プッシュ" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

$workspacePath = "\\nas\nas_1\card_reader_improved"
Set-Location $workspacePath

Write-Host "[1] ファイルを追加..." -ForegroundColor Yellow
git add attendance-client-fixed.service
git add FINAL_FIX.md
git add why_manual_works.sh
git add fix_pcsc_permissions.sh
Write-Host "  完了" -ForegroundColor Green
Write-Host ""

Write-Host "[2] コミット..." -ForegroundColor Yellow
git commit -m "Fix PC/SC access permission - Add Group=pcscd to service file and improve environment variables"
if ($LASTEXITCODE -ne 0) {
    Write-Host "  コミット失敗または変更なし" -ForegroundColor Yellow
    git status --short
} else {
    Write-Host "  コミット成功" -ForegroundColor Green
}
Write-Host ""

Write-Host "[3] プッシュ..." -ForegroundColor Yellow
git push origin main
if ($LASTEXITCODE -ne 0) {
    Write-Host "  プッシュ失敗。force pushを試行..." -ForegroundColor Yellow
    git push origin main --force
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  force push成功" -ForegroundColor Green
    } else {
        Write-Host "  force push失敗" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  プッシュ成功" -ForegroundColor Green
}
Write-Host ""

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "完了" -ForegroundColor Green
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "ラズパイ側で実行:" -ForegroundColor Yellow
Write-Host "  1. git pull origin main" -ForegroundColor White
Write-Host "  2. sudo usermod -a -G pcscd raspberry" -ForegroundColor White
Write-Host "  3. sudo cp attendance-client-fixed.service /etc/systemd/system/" -ForegroundColor White
Write-Host "  4. sudo systemctl daemon-reload" -ForegroundColor White
Write-Host "  5. sudo systemctl restart attendance-client-fixed.service" -ForegroundColor White
Write-Host ""
Read-Host "Enterキーを押して終了"

