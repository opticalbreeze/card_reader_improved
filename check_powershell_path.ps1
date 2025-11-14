# PowerShellパス確認スクリプト
Write-Host "=== PowerShell Path Check ===" -ForegroundColor Cyan

# 1. 現在のPowerShellのパス
Write-Host "`n1. Current PowerShell Path:" -ForegroundColor Yellow
Write-Host $PSHOME

# 2. PowerShell実行ファイルの場所
Write-Host "`n2. PowerShell Executable:" -ForegroundColor Yellow
$psPath = Join-Path $PSHOME "powershell.exe"
Write-Host $psPath
Write-Host "Exists: $(Test-Path $psPath)"

# 3. 環境変数PATHからPowerShellを検索
Write-Host "`n3. PowerShell in PATH:" -ForegroundColor Yellow
$env:PATH -split ';' | Where-Object { $_ -like '*PowerShell*' } | ForEach-Object { Write-Host $_ }

# 4. where.exeでPowerShellを検索
Write-Host "`n4. PowerShell found by where.exe:" -ForegroundColor Yellow
$whereResult = cmd /c "where powershell 2>&1"
Write-Host $whereResult

# 5. ネットワークドライブからの実行確認
Write-Host "`n5. Current Location:" -ForegroundColor Yellow
Write-Host (Get-Location).Path
Write-Host "Is Network Path: $((Get-Location).Path -like '\\*')"

# 6. Cursorが使用する可能性のあるパス
Write-Host "`n6. Cursor's Expected Path:" -ForegroundColor Yellow
$cursorPath = "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
Write-Host $cursorPath
Write-Host "Exists: $(Test-Path $cursorPath)"

# 7. 代替パス
Write-Host "`n7. Alternative PowerShell Paths:" -ForegroundColor Yellow
$altPaths = @(
    "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
    "C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe",
    "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
)
foreach ($path in $altPaths) {
    $exists = Test-Path $path
    Write-Host "$path : $exists" -ForegroundColor $(if ($exists) { "Green" } else { "Red" })
}

