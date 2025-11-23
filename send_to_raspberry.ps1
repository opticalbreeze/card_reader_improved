# SSHでラズパイにシンプル版を送信するスクリプト
# 使用方法: .\send_to_raspberry.ps1

param(
    [string]$RaspberryIP = "192.168.1.74",
    [string]$Username = "raspberry",
    [string]$RemotePath = "/home/raspberry/Desktop/card_reader_improved"
)

# 接続情報の確認
if ([string]::IsNullOrEmpty($RaspberryIP)) {
    Write-Host "ラズパイのIPアドレスを入力してください:" -ForegroundColor Yellow
    $RaspberryIP = Read-Host
}

if ([string]::IsNullOrEmpty($RaspberryIP)) {
    Write-Host "[エラー] IPアドレスが指定されていません" -ForegroundColor Red
    exit 1
}

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
    "start_pi_simple.sh",
    "common_utils.py",
    "constants.py",
    "lcd_i2c.py",
    "gpio_config.py"
)

# ファイルの存在確認
$MissingFiles = @()
foreach ($file in $FilesToTransfer) {
    if (-not (Test-Path $file)) {
        $MissingFiles += $file
    }
}

if ($MissingFiles.Count -gt 0) {
    Write-Host "[警告] 以下のファイルが見つかりません:" -ForegroundColor Yellow
    foreach ($file in $MissingFiles) {
        Write-Host "  - $file" -ForegroundColor Yellow
    }
    Write-Host ""
    $continue = Read-Host "続行しますか? (y/n)"
    if ($continue -ne "y") {
        exit 1
    }
}

# scpコマンドの確認（OpenSSHが必要）
$scpAvailable = $false
try {
    $null = Get-Command scp -ErrorAction Stop
    $scpAvailable = $true
} catch {
    Write-Host "[警告] scpコマンドが見つかりません" -ForegroundColor Yellow
    Write-Host "OpenSSHクライアントをインストールしてください:" -ForegroundColor Yellow
    Write-Host "  Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "または、PuTTYのpscpを使用する場合は、pscp.exeのパスを指定してください:" -ForegroundColor Yellow
    $pscpPath = Read-Host "pscp.exeのパス (Enterでスキップ)"
    if (-not [string]::IsNullOrEmpty($pscpPath)) {
        if (Test-Path $pscpPath) {
            $scpCommand = $pscpPath
            $scpAvailable = $true
        }
    }
}

if (-not $scpAvailable) {
    Write-Host "[エラー] ファイル転送ツールが見つかりません" -ForegroundColor Red
    exit 1
}

# ファイル転送
Write-Host "[転送開始] ファイルを転送しています..." -ForegroundColor Green
Write-Host ""

$transferSuccess = $true
foreach ($file in $FilesToTransfer) {
    if (Test-Path $file) {
        Write-Host "転送中: $file" -ForegroundColor Cyan
        
        # OpenSSHのscpを使用
        $scpArgs = @(
            $file
            "${Username}@${RaspberryIP}:${RemotePath}/"
        )
        scp @scpArgs
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[エラー] $file の転送に失敗しました" -ForegroundColor Red
            $transferSuccess = $false
        } else {
            Write-Host "[成功] $file" -ForegroundColor Green
        }
    }
}

Write-Host ""

if ($transferSuccess) {
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "転送完了！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "ラズパイで以下のコマンドを実行してください:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  cd $RemotePath" -ForegroundColor Cyan
    Write-Host "  chmod +x start_pi_simple.sh" -ForegroundColor Cyan
    Write-Host "  ./start_pi_simple.sh" -ForegroundColor Cyan
    Write-Host ""
} else {
    Write-Host "[エラー] 一部のファイルの転送に失敗しました" -ForegroundColor Red
    exit 1
}

