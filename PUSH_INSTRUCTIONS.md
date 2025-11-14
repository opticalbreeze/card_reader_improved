# プッシュ手順

## PowerShellで実行

```powershell
cd \\nas\nas_1\card_reader_improved
.\\push_sleep_fix.ps1
```

## または、手動で実行

```powershell
cd \\nas\nas_1\card_reader_improved

# ファイルを追加
git add win_client.py

# コミット
git commit -m "Fix Windows sleep recovery - Improve card reader detection after sleep/wake"

# プッシュ
git push origin main
```

## コミットメッセージ

```
Fix Windows sleep recovery - Improve card reader detection after sleep/wake
```

## 変更内容

- `win_client.py`: スリープ復帰時のカードリーダー認識問題を改善
  - 定期的なリーダー再検出機能の強化
  - nfcpyリーダーのエラーハンドリング改善（連続エラー時の再初期化）
  - PC/SCリーダーのエラーハンドリング改善（スリープ復帰時のreaderオブジェクト再取得）
  - リーダー監視の再起動機能追加

