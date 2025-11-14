# 最終的な修正内容

## 問題

自動起動時にPC/SCサービスへのアクセス権限エラー（Access denied）が発生

## 修正内容

### 1. サービスファイルの修正

- `Group=pcscd`を追加（PC/SCサービスへのアクセス権限）
- `After=network.target pcscd.service`に変更（PC/SCサービスの起動を待つ）
- `RestartSec=300`に変更（無限ループを防ぐ）
- 環境変数を追加（手動起動時と同じ環境を再現）

### 2. ラズパイ側で実行するコマンド

```bash
cd ~/Desktop/attendance/card_reader_improved

# 1. ユーザーをpcscdグループに追加
sudo usermod -a -G pcscd raspberry

# 2. サービスファイルを更新
sudo cp attendance-client-fixed.service /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/attendance-client-fixed.service

# 3. systemdをリロード
sudo systemctl daemon-reload

# 4. サービスを再起動
sudo systemctl restart attendance-client-fixed.service

# 5. 確認
sudo journalctl -u attendance-client-fixed.service -f
```

## これで解決する理由

1. `Group=pcscd`により、サービスがpcscdグループで実行される
2. ユーザーをpcscdグループに追加することで、手動起動時と同じ権限になる
3. 環境変数を設定することで、手動起動時と同じ環境になる

