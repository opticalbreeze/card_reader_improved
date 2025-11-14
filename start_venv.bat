@echo off
REM ========================================================================
REM Windows版クライアント - 仮想環境自動起動バッチファイル
REM ========================================================================
REM 
REM 使い方：
REM   1. このバッチファイルをダブルクリックで実行
REM   2. 仮想環境が存在しない場合は自動で作成
REM   3. 必要なパッケージを自動インストール
REM   4. Windows版クライアントを起動
REM
REM ========================================================================

echo ========================================
echo 打刻システム - Windowsクライアント起動
echo ========================================
echo.

REM カレントディレクトリをバッチファイルの場所に変更
cd /d %~dp0

REM 仮想環境の存在確認
if exist "venv\Scripts\activate.bat" (
    echo [OK] 仮想環境を検出しました
    goto ACTIVATE
)

echo [情報] 仮想環境が見つかりません
echo [情報] 仮想環境を作成します...
echo.

REM Pythonの存在確認
python --version >nul 2>&1
if errorlevel 1 (
    echo [エラー] Pythonがインストールされていません
    echo [ヒント] https://www.python.org/ からPythonをインストールしてください
    pause
    exit /b 1
)

REM 仮想環境を作成
echo [実行] python -m venv venv
python -m venv venv

if errorlevel 1 (
    echo [エラー] 仮想環境の作成に失敗しました
    pause
    exit /b 1
)

echo [OK] 仮想環境を作成しました
echo.

:ACTIVATE
echo [実行] 仮想環境を有効化
call venv\Scripts\activate.bat

if errorlevel 1 (
    echo [エラー] 仮想環境の有効化に失敗しました
    pause
    exit /b 1
)

echo [OK] 仮想環境を有効化しました
echo.

REM 必要なパッケージがインストールされているか確認
echo [確認] 必要なパッケージを確認中...
python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo [情報] requestsがインストールされていません
    goto INSTALL_PACKAGES
)

python -c "import smartcard" >nul 2>&1
if errorlevel 1 (
    echo [情報] pyscardがインストールされていません
    goto INSTALL_PACKAGES
)

echo [OK] 必要なパッケージがインストールされています
goto RUN_CLIENT

:INSTALL_PACKAGES
echo [情報] 必要なパッケージをインストールします...
echo.

REM requirements_windows.txt が存在する場合
if exist "requirements_windows.txt" (
    echo [実行] pip install -r requirements_windows.txt
    python -m pip install --upgrade pip
    pip install -r requirements_windows.txt
    
    if errorlevel 1 (
        echo [警告] パッケージのインストールに失敗しました
        echo [ヒント] 手動で以下を実行してください:
        echo   pip install -r requirements_windows.txt
        pause
    ) else (
        echo [OK] パッケージをインストールしました
    )
) else (
    REM requirements_windows.txt がない場合は個別インストール
    echo [実行] pip install requests pyscard
    python -m pip install --upgrade pip
    pip install requests pyscard
    
    if errorlevel 1 (
        echo [警告] パッケージのインストールに失敗しました
        pause
    ) else (
        echo [OK] パッケージをインストールしました
    )
)
echo.

:RUN_CLIENT
echo ========================================
echo Windowsクライアントを起動します...
echo ========================================
echo.

REM win_client.py の存在確認
if not exist "win_client.py" (
    echo [エラー] win_client.py が見つかりません
    echo [ヒント] このバッチファイルをプロジェクトのルートディレクトリに配置してください
    pause
    exit /b 1
)

REM クライアントを起動
python win_client.py

REM 終了処理
echo.
echo ========================================
echo クライアントを終了しました
echo ========================================
pause

