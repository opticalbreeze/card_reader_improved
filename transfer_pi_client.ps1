# Transfer files to Raspberry Pi
# Usage: .\transfer_pi_client.ps1

$RaspberryIP = "192.168.1.74"
$Username = "raspberry"
$RemotePath = "/home/raspberry/Desktop/card_reader_improved"

Write-Host "========================================"
Write-Host "Raspberry Pi File Transfer"
Write-Host "========================================"
Write-Host "IP: $RaspberryIP"
Write-Host "User: $Username"
Write-Host "Path: $RemotePath"
Write-Host ""

# Files to transfer
$files = @("pi_client.py", "lcd_i2c.py")

# Transfer files
Write-Host "Starting transfer..."
Write-Host ""

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "Transferring: $file"
        $target = "${Username}@${RaspberryIP}:${RemotePath}/"
        scp $file $target
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Success: $file" -ForegroundColor Green
        } else {
            Write-Host "Failed: $file" -ForegroundColor Red
        }
    } else {
        Write-Host "Warning: $file not found" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "========================================"
Write-Host "Transfer complete!"
Write-Host "========================================"
