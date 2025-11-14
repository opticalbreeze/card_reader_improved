# UTF-8 encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

Set-Location "\\nas\nas_1\card_reader_improved"

Write-Host "Adding files..." -ForegroundColor Cyan
git add attendance-client-fixed.service
git add create_pcscd_group.sh
git add PCSCD_GROUP_FIX.md
git add FINAL_FIX.md

Write-Host "Committing..." -ForegroundColor Cyan
git commit -m "Fix PC/SC access permission - Add Group=pcscd and create group script"

Write-Host "Pushing to GitHub..." -ForegroundColor Cyan
git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Successfully pushed to GitHub!" -ForegroundColor Green
} else {
    Write-Host "`n❌ Push failed. Try: git push origin main --force" -ForegroundColor Red
}

Write-Host "`nPress Enter to exit..."
Read-Host | Out-Null

