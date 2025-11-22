# 完全自動起動設定ガイド

このガイドでは、Raspberry Pi起動時に仮想環境を自動的に有効化してコードを実行する設定方法を説明します。

---

## 🚀 クイックスタート

### 1. 完全自動設定スクリプトを使用（推奨）

```bash
cd ~/card_reader_improved
sudo bash setup_autostart_complete.sh
```

このスクリプトは以下を自動で実施します：
- ✅ Python3の確認とインストール
- ✅ 仮想環境の作成（存在しない場合）
- ✅ 依存パッケージのインストール
- ✅ PC/SCサービスの設定
- ✅ ユーザーをpcscdグループに追加
- ✅ GPIOグループの設定（オプション）
- ✅ systemdサービスファイルの作成
- ✅ 自動起動の有効化

### 2. 再起動

```bash
sudo reboot
```

再起動後、自動的にサービスが起動します。

---

## 📋 詳細手順

### 方法1: 完全自動設定スクリプト（推奨）

#### 前提条件

- Raspberry Pi OSがインストールされていること
- インターネット接続があること
- sudo権限があること

#### 手順

1. **プロジェクトディレクトリに移動**
   ```bash
   cd ~/card_reader_improved
   ```

2. **スクリプトに実行権限を付与**
   ```bash
   chmod +x setup_autostart_complete.sh
   ```

3. **スクリプトを実行**
   ```bash
   sudo bash setup_autostart_complete.sh
   ```

4. **設定ファイルを編集（必要に応じて）**
   ```bash
   nano client_config.json
   ```

5. **再起動**
   ```bash
   sudo reboot
   ```

---

### 方法2: 手動設定

#### ステップ1: 仮想環境の作成

```bash
cd ~/card_reader_improved
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements_unified.txt
```

#### ステップ2: PC/SCサービスの設定

```bash
# pcscdのインストール（未インストールの場合）
sudo apt-get update
sudo apt-get install -y pcscd pcsc-tools

# pcscdサービスの起動と有効化
sudo systemctl enable pcscd.service
sudo systemctl start pcscd.service
```

#### ステップ3: ユーザーをpcscdグループに追加

```bash
sudo usermod -a -G pcscd $USER
```

**重要**: グループの変更を反映するには、再ログインまたは再起動が必要です。

#### ステップ4: systemdサービスファイルの作成

```bash
sudo nano /etc/systemd/system/attendance-client-fixed.service
```

以下の内容を記述（パスは実際の環境に合わせて変更）：

```ini
[Unit]
Description=ICカード勤怠管理システム - ラズパイクライアント
After=network.target pcscd.service
Wants=network.target pcscd.service

[Service]
Type=simple
User=raspberry
Group=pcscd
WorkingDirectory=/home/raspberry/card_reader_improved
ExecStartPre=/bin/sleep 5
ExecStartPre=/bin/bash -c 'until systemctl is-active --quiet pcscd; do sleep 1; done'
ExecStartPre=/bin/bash -c 'until [ -S /var/run/pcscd/pcscd.comm ]; do sleep 1; done'
ExecStart=/bin/bash /home/raspberry/card_reader_improved/start_pi.sh
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

Environment="PYTHONUNBUFFERED=1"
Environment="PYTHONIOENCODING=utf-8"
Environment="LANG=ja_JP.UTF-8"
Environment="LC_ALL=ja_JP.UTF-8"
Environment="PATH=/home/raspberry/card_reader_improved/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="VIRTUAL_ENV=/home/raspberry/card_reader_improved/venv"
Environment="PCSCLITE_CSOCK_NAME=/var/run/pcscd/pcscd.comm"

[Install]
WantedBy=multi-user.target
```

#### ステップ5: サービスの有効化

```bash
sudo systemctl daemon-reload
sudo systemctl enable attendance-client-fixed.service
sudo systemctl start attendance-client-fixed.service
```

---

## 🔍 動作確認

### サービスの状態確認

```bash
sudo systemctl status attendance-client-fixed.service
```

### ログの確認

```bash
# リアルタイムでログを表示
sudo journalctl -u attendance-client-fixed.service -f

# 最新のログを表示
sudo journalctl -u attendance-client-fixed.service -n 50
```

### 手動起動テスト

```bash
cd ~/card_reader_improved
./start_pi.sh
```

---

## 🛠️ トラブルシューティング

### サービスが起動しない

1. **ログを確認**
   ```bash
   sudo journalctl -u attendance-client-fixed.service -n 100
   ```

2. **仮想環境の確認**
   ```bash
   ls -la ~/card_reader_improved/venv/bin/python3
   ```

3. **パスの確認**
   ```bash
   # サービスファイルのパスが正しいか確認
   sudo cat /etc/systemd/system/attendance-client-fixed.service
   ```

### PC/SC接続エラー

1. **pcscdサービスの確認**
   ```bash
   sudo systemctl status pcscd
   ```

2. **グループメンバーシップの確認**
   ```bash
   groups
   # pcscdグループが表示されることを確認
   ```

3. **再ログイン**
   ```bash
   # グループの変更を反映するために再ログイン
   exit
   # 再度SSHでログイン
   ```

### 仮想環境が見つからない

1. **仮想環境の再作成**
   ```bash
   cd ~/card_reader_improved
   rm -rf venv
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements_unified.txt
   ```

2. **サービスファイルのパス確認**
   ```bash
   sudo nano /etc/systemd/system/attendance-client-fixed.service
   # VIRTUAL_ENVとPATHのパスが正しいか確認
   ```

---

## 📚 関連ドキュメント

- [セットアップガイド](SETUP_GUIDE.md)
- [Raspberry Pi版セットアップガイド](RASPBERRY_PI_SETUP_GUIDE.md)
- [トラブルシューティング](TROUBLESHOOTING.md)
- [自動起動設定ガイド](AUTOSTART_GUIDE.md)

---

## ✅ 確認チェックリスト

- [ ] Python3がインストールされている
- [ ] 仮想環境が作成されている
- [ ] 依存パッケージがインストールされている
- [ ] pcscdサービスが起動している
- [ ] ユーザーがpcscdグループに所属している
- [ ] systemdサービスファイルが作成されている
- [ ] サービスが有効化されている
- [ ] サービスが正常に起動している
- [ ] ログにエラーがない

---

## 🎯 まとめ

`setup_autostart_complete.sh`を使用することで、すべての設定を自動で実施できます。

手動で設定する場合は、上記の手順に従って、各ステップを順番に実行してください。

設定後は、再起動して動作を確認してください。

