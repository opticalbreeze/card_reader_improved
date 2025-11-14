# GitHubへのpush手順（スタンドアロン版）

## 変更内容
- `client_card_reader_unified_improved.py`: スタンドアロン版に再構成
  - LocalCache → LocalDatabase に変更
  - サーバー通信機能を削除（requests不要）
  - データベースに直接保存する方式に変更
  - サーバー監視・リトライ機能を削除

## 実行コマンド（PowerShell）

```powershell
# 1. 変更をステージング
git add client_card_reader_unified_improved.py

# 2. コミット
git commit -m "Refactor to standalone version - remove server dependency

- Change LocalCache to LocalDatabase (direct database save)
- Remove server communication (send_to_server, monitor_server, retry)
- Remove requests dependency
- Save attendance data directly to local SQLite database
- Server folder no longer required for basic operation"

# 3. GitHubにpush
git push origin main
```

