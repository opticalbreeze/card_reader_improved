# GitHubへのプッシュスクリプト (PowerShell版)
# エンコーディング: UTF-8

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "GitHubへのプッシュスクリプト" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 現在のディレクトリを確認
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir
Write-Host "作業ディレクトリ: $PWD" -ForegroundColor Green
Write-Host ""

# Gitリポジトリの初期化確認
if (-not (Test-Path ".git")) {
    Write-Host "[1/5] Gitリポジトリを初期化しています..." -ForegroundColor Yellow
    try {
        git init
        Write-Host "Gitリポジトリを初期化しました" -ForegroundColor Green
    }
    catch {
        Write-Host "エラー: Gitリポジトリの初期化に失敗しました" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        Read-Host "Enterキーを押して終了"
        exit 1
    }
}
else {
    Write-Host "[1/5] Gitリポジトリは既に初期化されています" -ForegroundColor Green
}
Write-Host ""

# リモートリポジトリの確認
Write-Host "[2/5] リモートリポジトリを確認しています..." -ForegroundColor Yellow
try {
    $remoteUrl = git remote get-url origin 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "リモートリポジトリを設定しています..." -ForegroundColor Yellow
        git remote add origin https://github.com/opticalbreeze/card_reader_improved.git
        if ($LASTEXITCODE -ne 0) {
            Write-Host "エラー: リモートリポジトリの設定に失敗しました" -ForegroundColor Red
            Read-Host "Enterキーを押して終了"
            exit 1
        }
        Write-Host "リモートリポジトリを設定しました" -ForegroundColor Green
    }
    else {
        Write-Host "リモートリポジトリは既に設定されています" -ForegroundColor Green
        Write-Host "  URL: $remoteUrl" -ForegroundColor Gray
    }
}
catch {
    Write-Host "エラー: リモートリポジトリの確認に失敗しました" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Read-Host "Enterキーを押して終了"
    exit 1
}
Write-Host ""

# ファイルをステージング
Write-Host "[3/5] ファイルをステージングしています..." -ForegroundColor Yellow
try {
    git add .
    if ($LASTEXITCODE -ne 0) {
        Write-Host "エラー: ファイルのステージングに失敗しました" -ForegroundColor Red
        Read-Host "Enterキーを押して終了"
        exit 1
    }
    Write-Host "ファイルをステージングしました" -ForegroundColor Green
}
catch {
    Write-Host "エラー: ファイルのステージングに失敗しました" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Read-Host "Enterキーを押して終了"
    exit 1
}
Write-Host ""

# 変更があるか確認
Write-Host "[4/5] 変更を確認しています..." -ForegroundColor Yellow
try {
    git diff --cached --quiet
    if ($LASTEXITCODE -ne 0) {
        # 変更がある場合、コミット
        Write-Host "変更をコミットしています..." -ForegroundColor Yellow
        $commitMessage = "メモリリーク対策版を追加 - 長時間動作時の問題を解決"
        git commit -m $commitMessage
        if ($LASTEXITCODE -ne 0) {
            Write-Host "エラー: コミットに失敗しました" -ForegroundColor Red
            Read-Host "Enterキーを押して終了"
            exit 1
        }
        Write-Host "変更をコミットしました" -ForegroundColor Green
    }
    else {
        Write-Host "コミットする変更がありません" -ForegroundColor Gray
    }
}
catch {
    Write-Host "エラー: コミット処理に失敗しました" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Read-Host "Enterキーを押して終了"
    exit 1
}
Write-Host ""

# ブランチ名を確認
Write-Host "[5/5] ブランチ名を確認しています..." -ForegroundColor Yellow
try {
    $currentBranch = git branch --show-current
    if ([string]::IsNullOrEmpty($currentBranch)) {
        Write-Host "ブランチが存在しません。mainブランチを作成します..." -ForegroundColor Yellow
        git checkout -b main
        $currentBranch = "main"
    }
    Write-Host "現在のブランチ: $currentBranch" -ForegroundColor Green
}
catch {
    Write-Host "エラー: ブランチの確認に失敗しました" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Read-Host "Enterキーを押して終了"
    exit 1
}
Write-Host ""

# GitHubにプッシュ
Write-Host "GitHubにプッシュしています..." -ForegroundColor Yellow
try {
    git push -u origin $currentBranch
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "エラー: プッシュに失敗しました" -ForegroundColor Red
        Write-Host ""
        Write-Host "考えられる原因:" -ForegroundColor Yellow
        Write-Host "1. GitHubの認証情報が設定されていない" -ForegroundColor Gray
        Write-Host "2. リモートリポジトリへのアクセス権限がない" -ForegroundColor Gray
        Write-Host "3. ネットワーク接続の問題" -ForegroundColor Gray
        Write-Host ""
        Write-Host "対処法:" -ForegroundColor Yellow
        Write-Host "- GitHubの認証情報を設定してください" -ForegroundColor Gray
        Write-Host "- リモートリポジトリのURLを確認してください" -ForegroundColor Gray
        Write-Host "- ネットワーク接続を確認してください" -ForegroundColor Gray
        Read-Host "Enterキーを押して終了"
        exit 1
    }
}
catch {
    Write-Host "エラー: プッシュに失敗しました" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Read-Host "Enterキーを押して終了"
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "プッシュが完了しました！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "リポジトリURL:" -ForegroundColor Yellow
Write-Host "https://github.com/opticalbreeze/card_reader_improved" -ForegroundColor Cyan
Write-Host ""
Read-Host "Enterキーを押して終了"

