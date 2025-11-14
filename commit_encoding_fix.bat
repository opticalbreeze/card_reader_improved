@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo Adding files...
git add pi_client.py win_client.py config.py lcd_i2c.py test_led.py .vscode/settings.json setup_utf8.bat README_ENCODING_FIX.md

echo.
echo Committing changes...
git commit -m "Fix character encoding issues - UTF-8 output support for Windows"

echo.
echo Pushing to GitHub...
git push origin main

echo.
echo Done!
pause

