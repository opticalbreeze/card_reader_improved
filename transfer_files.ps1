# ラズパイにpi_client.pyを転送するスクリプト
# 使用方法: .\transfer_files.ps1

$RaspberryIP = "192.168.1.74"
$Username = "raspberry"
$RemotePath = "/home/raspberry/Desktop/card_reader_improved"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ラズパイへのファイル転送" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "IPアドレス: $RaspberryIP" -ForegroundColor White
Write-Host "ユーザー名: $Username" -ForegroundColor White
Write-Host "リモートパス: $RemotePath" -ForegroundColor White
Write-Host ""

# 転送するファイル
$FilesToTransfer = @(
    "pi_client.py",
    "pi_client_simple.py",
    "common_utils.py",
    "constants.py"
)

# ファイル転送
Write-Host "[転送開始] ファイルを転送しています..." -ForegroundColor Green
Write-Host ""

foreach ($file in $FilesToTransfer) {
    if (Test-Path $file) {
        Write-Host "転送中: $file" -ForegroundColor Cyan
        scp $file "${Username}@${RaspberryIP}:${RemotePath}/"
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[成功] $file" -ForegroundColor Green
        } else {
            Write-Host "[エラー] $file の転送に失敗しました" -ForegroundColor Red
        }
    } else {
        Write-Host "[警告] $file が見つかりません（スキップ）" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "転送完了！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

