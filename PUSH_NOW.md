# GitHubへのプッシュ手順

## 方法1: バッチファイルを実行（簡単）

`push_to_github.bat` をダブルクリックして実行してください。

## 方法2: コマンドプロンプトで手動実行

コマンドプロンプトを開いて、以下のコマンドを順番に実行してください：

```bash
cd C:\Users\optic\Desktop\クライアント

# 1. Gitリポジトリの初期化（初回のみ）
git init

# 2. リモートリポジトリの設定（初回のみ、既に設定されている場合はスキップ）
git remote add origin https://github.com/opticalbreeze/card_reader_improved.git

# 3. すべてのファイルをステージング
git add .

# 4. コミット
git commit -m "自動復旧機能を追加: ハートビート、接続チェック、自動リセット、エラーハンドリング強化、詳細ログ出力"

# 5. GitHubにプッシュ
git push -u origin main
```

**注意**: ブランチ名が `master` の場合は、最後のコマンドを以下に変更してください：
```bash
git push -u origin master
```

## プッシュされるファイル

- ✅ `client_card_reader_unified.py` - 自動復旧機能を追加したメインコード
- ✅ `CHANGELOG_自動復旧機能.md` - 自動復旧機能の詳細説明
- ✅ `README.md` - メインのREADME
- ✅ `README_メモリリーク対策版.md` - 初心者向けガイド
- ✅ `MEMORY_LEAK_FIX.md` - 技術的な詳細説明
- ✅ `CHANGELOG.md` - 変更履歴
- ✅ その他のドキュメントファイル

## エラーが発生した場合

### 認証エラー

GitHubの認証情報を設定してください：
- Personal Access Tokenを使用
- または、Git Credential Managerを使用

### リモートが既に存在する

以下のコマンドで確認：
```bash
git remote -v
```

既に設定されている場合は、ステップ2をスキップしてください。

---

**準備完了！** `push_to_github.bat` をダブルクリックするか、上記のコマンドを実行してください。

