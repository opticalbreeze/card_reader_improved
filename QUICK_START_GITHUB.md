# 🚀 GitHubへのプッシュ - クイックスタート

## 簡単な手順（コピー&ペーストで実行）

### 1. Gitリポジトリの初期化

```bash
cd C:\Users\optic\Desktop\クライアント
git init
```

### 2. リモートリポジトリの設定

```bash
git remote add origin https://github.com/opticalbreeze/card_reader_improved.git
```

**注意**: 既にリモートが設定されている場合は、このステップをスキップしてください。

### 3. すべてのファイルを追加

```bash
git add .
```

### 4. コミット

```bash
git commit -m "メモリリーク対策版を追加 - 長時間動作時の問題を解決"
```

### 5. GitHubにプッシュ

```bash
git push -u origin main
```

**注意**: ブランチ名が `master` の場合は、以下のコマンドを使用してください：

```bash
git push -u origin master
```

## ✅ 完了！

これで、変更内容がGitHubにプッシュされました。

## 📋 プッシュされたファイル

- ✅ `client_card_reader_unified.py` - メモリリーク対策版のメインコード
- ✅ `requirements_unified.txt` - 依存関係（psutilを追加）
- ✅ `README.md` - メインのREADME
- ✅ `README_メモリリーク対策版.md` - 初心者向けガイド
- ✅ `MEMORY_LEAK_FIX.md` - 技術的な詳細説明
- ✅ `CHANGELOG.md` - 変更履歴
- ✅ `.gitignore` - Git除外設定

## 🔍 確認方法

GitHubのリポジトリページ（https://github.com/opticalbreeze/card_reader_improved）にアクセスして、ファイルが追加されているか確認してください。

## ❓ エラーが出た場合

詳細な手順とトラブルシューティングは、`PUSH_TO_GITHUB.md` を参照してください。

