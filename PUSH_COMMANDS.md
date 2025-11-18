# GitHubへのプッシュ - 実行コマンド

以下のコマンドをコマンドプロンプトで実行してください：

```bash
cd C:\Users\optic\Desktop\クライアント

# 1. すべてのファイルをステージング
git add .

# 2. コミット
git commit -m "LCD文字化け対策を追加: パディング強化、クリア機能、バッファ残存防止"

# 3. GitHubにプッシュ
git push -u origin main
```

**注意**: ブランチ名が `master` の場合は、最後のコマンドを以下に変更してください：
```bash
git push -u origin master
```

## プッシュされる主な変更

- ✅ `client_card_reader_unified.py` - LCD文字化け対策を追加
- ✅ `LCD文字化け対策_追加修正.md` - 追加修正の詳細説明
- ✅ その他のドキュメントファイル

