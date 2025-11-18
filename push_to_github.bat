@echo off
chcp 65001 >nul
echo ========================================
echo GitHubへのプッシュスクリプト
echo ========================================
echo.

REM 現在のディレクトリを確認
cd /d "%~dp0"
echo 作業ディレクトリ: %CD%
echo.

REM Gitリポジトリの初期化確認
if not exist ".git" (
    echo [1/5] Gitリポジトリを初期化しています...
    git init
    if errorlevel 1 (
        echo エラー: Gitリポジトリの初期化に失敗しました
        pause
        exit /b 1
    )
    echo Gitリポジトリを初期化しました
) else (
    echo [1/5] Gitリポジトリは既に初期化されています
)
echo.

REM リモートリポジトリの確認
echo [2/5] リモートリポジトリを確認しています...
git remote get-url origin >nul 2>&1
if errorlevel 1 (
    echo リモートリポジトリを設定しています...
    git remote add origin https://github.com/opticalbreeze/card_reader_improved.git
    if errorlevel 1 (
        echo エラー: リモートリポジトリの設定に失敗しました
        pause
        exit /b 1
    )
    echo リモートリポジトリを設定しました
) else (
    echo リモートリポジトリは既に設定されています
    git remote get-url origin
)
echo.

REM ファイルをステージング
echo [3/5] ファイルをステージングしています...
git add .
if errorlevel 1 (
    echo エラー: ファイルのステージングに失敗しました
    pause
    exit /b 1
)
echo ファイルをステージングしました
echo.

REM 変更があるか確認
git diff --cached --quiet
if errorlevel 1 (
    REM 変更がある場合、コミット
    echo [4/5] 変更をコミットしています...
    git commit -m "LCD文字化け対策強化: 制御文字除去、カードID検証、詳細デバッグログ追加"
    if errorlevel 1 (
        echo エラー: コミットに失敗しました
        pause
        exit /b 1
    )
    echo 変更をコミットしました
) else (
    echo [4/5] コミットする変更がありません
)
echo.

REM ブランチ名を確認
echo [5/5] ブランチ名を確認しています...
for /f "tokens=*" %%i in ('git branch --show-current 2^>nul') do set CURRENT_BRANCH=%%i
if "%CURRENT_BRANCH%"=="" (
    echo ブランチが存在しません。mainブランチを作成します...
    git checkout -b main
    set CURRENT_BRANCH=main
)

echo 現在のブランチ: %CURRENT_BRANCH%
echo.

REM GitHubにプッシュ
echo GitHubにプッシュしています...
git push -u origin %CURRENT_BRANCH%
if errorlevel 1 (
    echo.
    echo エラー: プッシュに失敗しました
    echo.
    echo 考えられる原因:
    echo 1. GitHubの認証情報が設定されていない
    echo 2. リモートリポジトリへのアクセス権限がない
    echo 3. ネットワーク接続の問題
    echo.
    echo 対処法:
    echo - GitHubの認証情報を設定してください
    echo - リモートリポジトリのURLを確認してください
    echo - ネットワーク接続を確認してください
    pause
    exit /b 1
)

echo.
echo ========================================
echo プッシュが完了しました！
echo ========================================
echo.
echo リポジトリURL:
echo https://github.com/opticalbreeze/card_reader_improved
echo.
pause

