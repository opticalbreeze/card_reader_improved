# GitHubプッシュスクリプトの使い方

## 📋 概要

GitHubへのプッシュを自動化するスクリプトです。以下の2つのバージョンがあります：

1. **push_to_github.bat** - Windowsバッチファイル（推奨）
2. **push_to_github.ps1** - PowerShellスクリプト

## 🚀 使い方

### 方法1: バッチファイル（簡単）

1. `push_to_github.bat` をダブルクリック
2. 画面の指示に従って操作
3. 完了！

### 方法2: PowerShellスクリプト

1. PowerShellを開く
2. 以下のコマンドを実行：

```powershell
cd C:\Users\optic\Desktop\クライアント
.\push_to_github.ps1
```

**注意**: PowerShellの実行ポリシーでエラーが出る場合は、以下のコマンドを実行してください：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 📝 スクリプトの動作

スクリプトは以下の手順を自動的に実行します：

1. **Gitリポジトリの初期化確認**
   - `.git`フォルダが存在しない場合、初期化します

2. **リモートリポジトリの設定確認**
   - リモートが設定されていない場合、設定します
   - URL: `https://github.com/opticalbreeze/card_reader_improved.git`

3. **ファイルのステージング**
   - すべての変更をステージングエリアに追加します

4. **コミット**
   - 変更がある場合、コミットします
   - コミットメッセージ: "メモリリーク対策版を追加 - 長時間動作時の問題を解決"

5. **GitHubにプッシュ**
   - 現在のブランチをGitHubにプッシュします
   - ブランチ名が存在しない場合、`main`ブランチを作成します

## ⚠️ 注意事項

### 認証が必要な場合

初回実行時や認証情報が設定されていない場合、GitHubの認証が求められることがあります。

#### 方法1: Personal Access Token (推奨)

1. GitHubにログイン
2. Settings → Developer settings → Personal access tokens → Tokens (classic)
3. "Generate new token" をクリック
4. 必要な権限を選択（`repo`権限が必要）
5. トークンを生成してコピー
6. プッシュ時にパスワードの代わりにトークンを入力

#### 方法2: GitHub CLI

```bash
gh auth login
```

#### 方法3: Git Credential Manager

Windowsの場合、Git Credential Managerが自動的に認証を処理します。

### エラーが発生した場合

#### エラー: "fatal: not a git repository"

- スクリプトが自動的に初期化します
- 手動で初期化する場合: `git init`

#### エラー: "fatal: remote origin already exists"

- 既にリモートが設定されているため、問題ありません
- リモートURLを変更する場合: `git remote set-url origin <新しいURL>`

#### エラー: "Permission denied"

- GitHubの認証情報を確認してください
- Personal Access Tokenを使用してください

#### エラー: "failed to push some refs"

- リモートに新しい変更がある可能性があります
- 以下のコマンドで最新の変更を取得してから再実行：

```bash
git pull origin main --rebase
```

## 🔧 カスタマイズ

### コミットメッセージを変更する

スクリプト内の以下の行を編集：

**バッチファイル (push_to_github.bat)**:
```batch
git commit -m "メモリリーク対策版を追加 - 長時間動作時の問題を解決"
```

**PowerShell (push_to_github.ps1)**:
```powershell
$commitMessage = "メモリリーク対策版を追加 - 長時間動作時の問題を解決"
```

### リモートURLを変更する

スクリプト内の以下の行を編集：

**バッチファイル**:
```batch
git remote add origin https://github.com/opticalbreeze/card_reader_improved.git
```

**PowerShell**:
```powershell
git remote add origin https://github.com/opticalbreeze/card_reader_improved.git
```

## 📚 関連ドキュメント

- [QUICK_START_GITHUB.md](QUICK_START_GITHUB.md) - クイックスタートガイド
- [PUSH_TO_GITHUB.md](PUSH_TO_GITHUB.md) - 詳細な手動手順

## ❓ よくある質問

### Q: スクリプトを実行しても何も起こらない

A: コマンドプロンプトまたはPowerShellで実行してください。ダブルクリックで実行する場合、ウィンドウがすぐに閉じる可能性があります。

### Q: 認証情報を毎回入力する必要がある

A: Git Credential Managerを設定するか、Personal Access Tokenを使用してください。

### Q: 特定のファイルだけをプッシュしたい

A: スクリプトを編集して、`git add .` の代わりに `git add <ファイル名>` を使用してください。

---

**更新日**: 2025年1月

