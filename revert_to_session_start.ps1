# UTF-8 encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

Set-Location "\\nas\nas_1\card_reader_improved"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  セッション開始時点までリポジトリを戻す" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/5] 現在のコミット履歴を確認中..." -ForegroundColor Yellow
git log --oneline -10
Write-Host ""

Write-Host "[2/5] セッション開始時点のコミットを特定中..." -ForegroundColor Yellow
Write-Host "  セッション開始時点は、PC/SC問題の調査を開始する前の状態です" -ForegroundColor Yellow
Write-Host "  以下のコミットまで戻すことを推奨します:" -ForegroundColor Yellow
Write-Host ""

# セッション開始時点のコミットを特定（手動で確認が必要）
Write-Host "  最新のコミット:" -ForegroundColor Yellow
git log --oneline -1
Write-Host ""

$commitHash = Read-Host "  戻したいコミットハッシュを入力してください（Enterで最新から5つ前まで戻す）"

if ([string]::IsNullOrWhiteSpace($commitHash)) {
    # デフォルト: 最新から5つ前まで戻す
    $commits = git log --oneline -5
    Write-Host "  最新5つのコミット:" -ForegroundColor Yellow
    $commits | ForEach-Object { Write-Host "    $_" }
    Write-Host ""
    $commitHash = Read-Host "  戻したいコミットハッシュを入力してください"
}

if ([string]::IsNullOrWhiteSpace($commitHash)) {
    Write-Host "[エラー] コミットハッシュが指定されていません" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[3/5] ローカルリポジトリをリセット中..." -ForegroundColor Yellow
Write-Host "  コミット: $commitHash" -ForegroundColor Yellow
Write-Host "  警告: この操作はローカルの変更を破棄します" -ForegroundColor Red
$confirm = Read-Host "  続行しますか？ (yes/no)"

if ($confirm -ne "yes") {
    Write-Host "[キャンセル] 操作をキャンセルしました" -ForegroundColor Yellow
    exit 0
}

git reset --hard $commitHash

if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] ローカルリポジトリをリセットしました" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "[4/5] リモートリポジトリを確認中..." -ForegroundColor Yellow
    git log --oneline origin/main -5
    Write-Host ""
    
    Write-Host "[5/5] リモートリポジトリを強制プッシュしますか？" -ForegroundColor Yellow
    Write-Host "  警告: これはリモートの履歴を書き換えます" -ForegroundColor Red
    $confirmPush = Read-Host "  強制プッシュしますか？ (yes/no)"
    
    if ($confirmPush -eq "yes") {
        Write-Host "  強制プッシュ中..." -ForegroundColor Yellow
        git push origin main --force
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "========================================" -ForegroundColor Green
            Write-Host "  ✅ リポジトリを戻しました" -ForegroundColor Green
            Write-Host "========================================" -ForegroundColor Green
        } else {
            Write-Host ""
            Write-Host "========================================" -ForegroundColor Red
            Write-Host "  ❌ 強制プッシュ失敗" -ForegroundColor Red
            Write-Host "========================================" -ForegroundColor Red
        }
    } else {
        Write-Host "[スキップ] 強制プッシュをスキップしました" -ForegroundColor Yellow
        Write-Host "  手動で実行する場合: git push origin main --force" -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "  ❌ リセット失敗" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
}

Write-Host ""
Write-Host "Enterキーを押すと終了します..."
Read-Host | Out-Null

