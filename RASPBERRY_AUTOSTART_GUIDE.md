# ラズパイ起動時の自動起動設定ガイド

## 概要

ラズパイ起動時に自動的にカードリーダーシステムを起動するように設定します。

## 前提条件

- ラズパイにSSH接続できること
- プロジェクトディレクトリに移動済みであること
- `attendance-client-fixed.service` ファイルが存在すること

## 設定手順

### 方法1: 自動設定スクリプトを使用（推奨）

```bash
cd ~/Desktop/attendance/card_reader_improved

# スクリプトに実行権限を付与
chmod +x setup_autostart_fixed.sh

# スクリプトを実行（sudoが必要）
sudo bash setup_autostart_fixed.sh
```

このスクリプトは以下を自動実行します：
1. サービスファイルを `/etc/systemd/system/` にコピー
2. パスとユーザー名を自動調整
3. `pcscd` グループの確認と作成
4. ユーザーを `pcscd` グループに追加
5. systemdをリロード
6. サービスを有効化

### 方法2: 手動で設定

#### ステップ1: サービスファイルをコピー

```bash
cd ~/Desktop/attendance/card_reader_improved

# サービスファイルをコピー
sudo cp attendance-client-fixed.service /etc/systemd/system/

# パスを確認・修正（必要に応じて）
sudo nano /etc/systemd/system/attendance-client-fixed.service
```

**重要**: サービスファイル内のパスを実際のプロジェクトパスに変更してください：
- `WorkingDirectory=/home/raspberry/Desktop/attendance/card_reader_improved`
- `ExecStart=/bin/bash /home/raspberry/Desktop/attendance/card_reader_improved/start_pi.sh`

#### ステップ2: pcscdグループの確認

```bash
# pcscdグループが存在するか確認
getent group pcscd

# 存在しない場合は作成
sudo groupadd pcscd

# ユーザーをpcscdグループに追加
sudo usermod -a -G pcscd raspberry

# 確認（ログアウト/ログイン後に反映）
groups | grep pcscd
```

#### ステップ3: systemdをリロードしてサービスを有効化

```bash
# systemdをリロード
sudo systemctl daemon-reload

# サービスを有効化（自動起動を有効にする）
sudo systemctl enable attendance-client-fixed.service

# 確認
sudo systemctl status attendance-client-fixed.service
```

#### ステップ4: サービスを起動（テスト）

```bash
# サービスを起動
sudo systemctl start attendance-client-fixed.service

# 状態を確認
sudo systemctl status attendance-client-fixed.service

# ログを確認
sudo journalctl -u attendance-client-fixed.service -f
```

## 確認方法

### サービスが有効化されているか確認

```bash
sudo systemctl is-enabled attendance-client-fixed.service
```

出力が `enabled` であれば、自動起動が有効になっています。

### サービスの状態を確認

```bash
sudo systemctl status attendance-client-fixed.service
```

### ログを確認

```bash
# リアルタイムでログを表示
sudo journalctl -u attendance-client-fixed.service -f

# 最新の100行を表示
sudo journalctl -u attendance-client-fixed.service -n 100
```

## よくある操作

### サービスを停止

```bash
sudo systemctl stop attendance-client-fixed.service
```

### サービスを再起動

```bash
sudo systemctl restart attendance-client-fixed.service
```

### 自動起動を無効化

```bash
sudo systemctl disable attendance-client-fixed.service
```

### 自動起動を再有効化

```bash
sudo systemctl enable attendance-client-fixed.service
```

## トラブルシューティング

### サービスが起動しない

1. **ログを確認**
   ```bash
   sudo journalctl -u attendance-client-fixed.service -n 50
   ```

2. **パスを確認**
   ```bash
   # サービスファイルのパスが正しいか確認
   cat /etc/systemd/system/attendance-client-fixed.service | grep -E "WorkingDirectory|ExecStart"
   
   # 実際のパスと一致しているか確認
   pwd
   ```

3. **権限を確認**
   ```bash
   # ユーザーがpcscdグループに属しているか確認
   groups | grep pcscd
   
   # 属していない場合は追加（ログアウト/ログイン後に反映）
   sudo usermod -a -G pcscd raspberry
   ```

### カードリーダーが認識されない

1. **PC/SCサービスが起動しているか確認**
   ```bash
   sudo systemctl status pcscd
   ```

2. **カードリーダーが接続されているか確認**
   ```bash
   pcsc_scan
   ```

3. **USBデバイスが認識されているか確認**
   ```bash
   lsusb | grep -i "card\|reader\|nfc"
   ```

### サービスが自動起動しない

1. **サービスが有効化されているか確認**
   ```bash
   sudo systemctl is-enabled attendance-client-fixed.service
   ```

2. **systemdをリロード**
   ```bash
   sudo systemctl daemon-reload
   ```

3. **サービスを再有効化**
   ```bash
   sudo systemctl disable attendance-client-fixed.service
   sudo systemctl enable attendance-client-fixed.service
   ```

## テスト方法

### ラズパイを再起動してテスト

```bash
sudo reboot
```

再起動後、以下でサービスが自動起動しているか確認：

```bash
sudo systemctl status attendance-client-fixed.service
```

### 手動でサービスを起動してテスト

```bash
sudo systemctl start attendance-client-fixed.service
sudo systemctl status attendance-client-fixed.service
```

## 注意事項

- サービスファイルのパスは実際のプロジェクトパスに合わせてください
- `pcscd` グループへの追加後、ログアウト/ログインが必要な場合があります
- サービスが起動しない場合は、ログを確認してください
- 手動起動で動作することを確認してから自動起動を設定してください

