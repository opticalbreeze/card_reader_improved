@echo off
chcp 65001 >nul
echo ==========================================
echo [Windows GUIクライアント起動]
echo ==========================================
echo.

cd /d "%~dp0"

python win_client.py

pause

