# 🥧 ラズパイ完全自動セットアップガイド

このガイドでは、ラズパイでカードリーダーシステムを完全自動でセットアップする方法を説明します。

---

## 🚀 クイックスタート（初回のみ）

### ステップ1: リポジトリをクローン

```bash
cd ~
git clone https://github.com/opticalbreeze/card_reader_improved.git
cd card_reader_improved
```

### ステップ2: 完全自動セットアップを実行

```bash
# 実行権限を付与
chmod +x auto_setup.sh check_system.sh manage_service.sh

# 自動セットアップを実行（5-10分かかります）
./auto_setup.sh
```

**このスクリプトが自動的に行うこと：**
- ✅ システムパッケージのチェックとインストール
- ✅ Python仮想環境の作成
- ✅ 依存ライブラリの自動インストール
- ✅ pcscd（カードリーダーサービス）の起動
- ✅ I2C/GPIO権限の設定
- ✅ 設定ファイルの作成
- ✅ systemd自動起動サービスの登録

### ステップ3: 設定ファイルを編集

```bash
nano client_config.json
```

サーバーURLを変更：
```json
{
  "server_url": "http://192.168.1.31:5000"
}
```

保存：**Ctrl + O**, Enter  
終了：**Ctrl + X**

### ステップ4: 再起動

```bash
sudo reboot
```

**再起動後、サービスは自動的に起動します！**

---

## 📊 システム診断

セットアップ後、システムの状態を確認：

```bash
./check_system.sh
```

**診断内容：**
- システムパッケージのインストール状況
- Python仮想環境の状態
- 依存ライブラリのチェック
- ユーザー権限の確認
- カードリーダーの検出
- I2Cデバイスの確認
- systemdサービスの状態

---

## 🎮 サービス管理

### サービスの起動

```bash
./manage_service.sh start
```

### サービスの停止

```bash
./manage_service.sh stop
```

### サービスの再起動

```bash
./manage_service.sh restart
```

### サービスの状態確認

```bash
./manage_service.sh status
```

### ログをリアルタイム表示

```bash
./manage_service.sh log
```

**Ctrl + C** で終了

### 全てのログを表示

```bash
./manage_service.sh log-all
```

### 自動起動の有効化

```bash
./manage_service.sh enable
```

### 自動起動の無効化

```bash
./manage_service.sh disable
```

---

## 🔧 トラブルシューティング

### 問題1: サービスが起動しない

```bash
# 診断を実行
./check_system.sh

# ログを確認
./manage_service.sh log

# サービスを再起動
./manage_service.sh restart
```

### 問題2: カードリーダーが認識されない

```bash
# USBデバイスを確認
lsusb

# pcscdサービスを再起動
sudo systemctl restart pcscd

# カードリーダーをチェック
pcsc_scan
```

### 問題3: GPIO/I2C権限エラー

```bash
# 権限を再設定
sudo usermod -a -G gpio,i2c,dialout $USER

# 再起動
sudo reboot
```

### 問題4: 依存ライブラリのエラー

```bash
# 仮想環境を削除して再セットアップ
rm -rf venv
./auto_setup.sh
```

---

## 📝 手動起動（テスト用）

サービスを使わず、手動で起動してテストする場合：

```bash
cd ~/card_reader_improved

# 仮想環境を有効化
source venv/bin/activate

# プログラムを起動
python3 pi_client.py

# 終了: Ctrl + C
```

---

## 🔄 アップデート方法

新しいバージョンに更新する場合：

```bash
cd ~/card_reader_improved

# サービスを停止
./manage_service.sh stop

# 最新版を取得
git pull

# 依存関係を更新（必要に応じて）
source venv/bin/activate
pip install -r requirements_unified.txt
deactivate

# サービスを再起動
./manage_service.sh start
```

---

## 📋 よく使うコマンド一覧

| コマンド | 説明 |
|---|---|
| `./auto_setup.sh` | 完全自動セットアップ |
| `./check_system.sh` | システム診断 |
| `./manage_service.sh start` | サービス起動 |
| `./manage_service.sh stop` | サービス停止 |
| `./manage_service.sh restart` | サービス再起動 |
| `./manage_service.sh status` | サービス状態確認 |
| `./manage_service.sh log` | ログをリアルタイム表示 |
| `nano client_config.json` | 設定編集 |
| `sudo reboot` | 再起動 |

---

## 🌐 リモート接続（SSH）

別のPCからラズパイにSSH接続して管理する場合：

```bash
# SSHでラズパイに接続
ssh raspberry@192.168.1.100

# プロジェクトフォルダに移動
cd ~/card_reader_improved

# サービス状態を確認
./manage_service.sh status

# ログを確認
./manage_service.sh log
```

---

## 🎯 自動起動の仕組み

`auto_setup.sh` で作成されるsystemdサービスファイル：

**場所:** `/etc/systemd/system/card-reader.service`

**内容:**
```ini
[Unit]
Description=Card Reader Client Service
After=network.target pcscd.service
Wants=pcscd.service

[Service]
Type=simple
User=raspberry
WorkingDirectory=/home/raspberry/card_reader_improved
Environment="PATH=/home/raspberry/card_reader_improved/venv/bin:..."
ExecStart=/home/raspberry/card_reader_improved/venv/bin/python3 pi_client.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**機能:**
- 起動時に自動実行
- ネットワークとpcscdサービスの起動を待つ
- 異常終了時は10秒後に自動再起動
- ログはjournalctlで管理

---

## 💡 ヒント

### 起動時にメッセージを表示

ラズパイ起動時にIPアドレスを確認したい場合：

```bash
# ~/.bashrcに追加
echo 'echo "IPアドレス: $(hostname -I)"' >> ~/.bashrc
```

### VNC経由でGUIを使う

VNCで接続している場合、設定GUIも使えます：

```bash
cd ~/card_reader_improved
source venv/bin/activate
python3 config.py
```

### 複数のラズパイで使う

複数のラズパイに同じ設定を展開する場合：

```bash
# ラズパイ1でセットアップ
./auto_setup.sh

# 設定ファイルをコピー（他のラズパイへ）
scp client_config.json raspberry@192.168.1.101:~/card_reader_improved/
```

---

## 📞 サポート

問題が解決しない場合は、以下の情報を添えて報告してください：

```bash
# システム情報を取得
./check_system.sh > system_info.txt

# 最新のログを取得
sudo journalctl -u card-reader.service -n 100 > service_log.txt
```

---

**🎉 これで完璧！ラズパイでカードリーダーシステムが自動起動します！**

