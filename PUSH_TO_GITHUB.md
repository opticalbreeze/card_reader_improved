# GitHubへのプッシュ手順

このドキュメントは、変更内容をGitHubにプッシュする手順を説明します。

## 📋 前提条件

- Gitがインストールされていること
- GitHubアカウントを持っていること
- リポジトリへのアクセス権限があること

## 🚀 手順

### 1. Gitリポジトリの初期化（初回のみ）

```bash
cd C:\Users\optic\Desktop\クライアント
git init
```

### 2. リモートリポジトリの設定（初回のみ）

```bash
git remote add origin https://github.com/opticalbreeze/card_reader_improved.git
```

既にリモートが設定されている場合は、以下のコマンドで確認できます：

```bash
git remote -v
```

### 3. ファイルをステージング

```bash
git add .
```

または、特定のファイルのみ追加する場合：

```bash
git add client_card_reader_unified.py
git add requirements_unified.txt
git add README.md
git add README_メモリリーク対策版.md
git add MEMORY_LEAK_FIX.md
git add CHANGELOG.md
git add .gitignore
```

### 4. コミット

```bash
git commit -m "メモリリーク対策版を追加

- メモリリーク問題を修正
- メモリ監視機能を追加
- NFCリーダーのリソース管理を改善
- キャッシュ管理を改善
- デバッグ出力を強化
- 初心者向けドキュメントを追加"
```

### 5. GitHubにプッシュ

```bash
git push -u origin main
```

または、ブランチ名が `master` の場合は：

```bash
git push -u origin master
```

### 6. ブランチの確認

現在のブランチを確認する場合：

```bash
git branch
```

別のブランチに切り替える場合：

```bash
git checkout -b memory-leak-fix
git push -u origin memory-leak-fix
```

## 📝 コミットメッセージの例

### 良いコミットメッセージ

```
メモリリーク対策版を追加

- メモリリーク問題を修正
- メモリ監視機能を追加
- NFCリーダーのリソース管理を改善
- キャッシュ管理を改善
- デバッグ出力を強化
- 初心者向けドキュメントを追加
```

### より詳細なコミットメッセージ

```
メモリリーク対策版を追加

問題:
- 長時間動作時にカードが読み取れなくなる
- メモリ使用量が時間とともに増え続ける

解決策:
- メモリ監視機能を追加（5分ごとにチェック）
- NFCリーダーのリソース管理を改善
- キャッシュサイズを制限（最大1000件）
- 自動ガベージコレクション機能を追加

効果:
- メモリ使用量を50-100MB程度で安定
- 24時間以上、安定して動作
- 詳細なログで問題を確認可能

ドキュメント:
- 初心者向けガイドを追加
- 技術的な詳細説明を追加
- 変更履歴を追加
```

## 🔧 トラブルシューティング

### エラー: "fatal: not a git repository"

リポジトリが初期化されていません。以下のコマンドを実行してください：

```bash
git init
```

### エラー: "fatal: remote origin already exists"

リモートが既に設定されています。以下のコマンドで確認できます：

```bash
git remote -v
```

リモートを変更する場合：

```bash
git remote set-url origin https://github.com/opticalbreeze/card_reader_improved.git
```

### エラー: "error: failed to push some refs"

リモートリポジトリに新しい変更がある可能性があります。以下のコマンドで最新の変更を取得してください：

```bash
git pull origin main --rebase
```

その後、再度プッシュしてください：

```bash
git push -u origin main
```

### エラー: "Permission denied"

GitHubの認証情報が正しく設定されていない可能性があります。以下のコマンドで確認できます：

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## 📚 参考資料

- [Git公式ドキュメント](https://git-scm.com/doc)
- [GitHub公式ドキュメント](https://docs.github.com/)

---

**注意**: この手順は、Windows環境での操作を想定しています。LinuxやmacOSの場合は、パスの形式が異なる場合があります。

