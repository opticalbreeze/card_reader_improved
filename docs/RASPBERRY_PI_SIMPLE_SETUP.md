# ラズパイシンプル版セットアップガイド

このガイドでは、Raspberry Pi版の**シンプル版**クライアントのセットアップ方法を説明します。

シンプル版は統合版（`pi_client.py`）よりも軽量で、最小限の機能のみを提供します。

---

## 📋 目次

1. [シンプル版の特徴](#シンプル版の特徴)
2. [必要なもの](#必要なもの)
3. [自動セットアップ（推奨）](#自動セットアップ推奨)
4. [手動セットアップ](#手動セットアップ)
5. [設定ファイルの編集](#設定ファイルの編集)
6. [起動方法](#起動方法)
7. [自動起動設定](#自動起動設定)
8. [トラブルシューティング](#トラブルシューティング)

---

## ✨ シンプル版の特徴

### 統合版との違い

| 機能 | 統合版 | シンプル版 |
|------|--------|------------|
| カード読み取り | ✅ | ✅ |
| サーバー送信 | ✅ | ✅ |
| ローカル保存 | ✅ | ✅ |
| GUI機能 | ✅ | ❌ |
| メモリモニタリング | ✅ | ❌ |
| メンテナンススレッド | ✅ | ❌ |
| スレッド数 | 10個以上 | 3-5個 |
| リソース使用量 | やや多め | 少なめ |

### 推奨用途

- ✅ リソースが限られた環境
- ✅ シンプルな動作が求められる環境
- ✅ デバッグやテスト用途
- ✅ メモリ使用量を抑えたい場合

---

## 🛠️ 必要なもの

### ハードウェア

- **Raspberry Pi 3以上**（推奨: Raspberry Pi 4）
- **microSDカード**（32GB以上推奨）
- **電源アダプター**（5V 3A以上推奨）
- **ICカードリーダー**（Sony RC-S380、Circle CIR315等）
- **USBケーブル**（カードリーダー用）
- **LCDディスプレイ（オプション）** - I2C 1602
- **RGB LED（オプション）** - 状態表示用
- **圧電ブザー（オプション）** - 音声フィードバック用

### ソフトウェア

- **Raspberry Pi OS**（Bullseye以上推奨）
- **Python 3.7以上**

---

## 🚀 自動セットアップ（推奨）

### セットアップスクリプトの実行

```bash
# ファイルをダウンロード（まだの場合）
cd ~
git clone https://github.com/opticalbreeze/card_reader_improved.git
cd card_reader_improved

# 自動セットアップスクリプトを実行
chmod +x auto_setup.sh
./auto_setup.sh
```

### 自動セットアップが行うこと

1. **システムパッケージのインストール**
   - Python 3、pip、git
   - PC/SCライブラリ（libpcsclite1、pcscd）
   - I2Cツール（i2c-tools）
   - その他必要なパッケージ

2. **Python仮想環境の作成（重要）**
   - `venv`ディレクトリに仮想環境を作成
   - 依存関係を自動インストール（`requirements_unified.txt`）
   - **注意**: 仮想環境は必須です。グローバル環境にインストールしないでください

3. **PC/SCサービスの設定**
   - `pcscd`サービスの起動と有効化
   - PC/SCグループへのユーザー追加

4. **GPIO権限の設定**
   - GPIOグループへのユーザー追加

5. **設定ファイルの作成**
   - `client_config.json`の初期化

**所要時間**: 約5-10分

### セットアップ後の再起動

```bash
sudo reboot
```

**重要**: 再起動後、仮想環境のパスが正しく反映されます。

---

## 📝 手動セットアップ

自動セットアップが失敗した場合や、手動で設定したい場合は以下の手順を実行してください。

### 1. システムパッケージのインストール

```bash
sudo apt update
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    libpcsclite1 \
    pcscd \
    pcsc-tools \
    i2c-tools \
    python3-dev \
    libusb-1.0-0-dev \
    swig
```

### 2. PC/SCサービスの起動

```bash
# pcscdサービスを起動
sudo systemctl start pcscd
sudo systemctl enable pcscd

# サービス状態を確認
sudo systemctl status pcscd
```

### 3. PC/SCグループへの追加

```bash
# pcscdグループを作成（存在しない場合）
sudo groupadd pcscd

# ユーザーをpcscdグループに追加
sudo usermod -a -G pcscd $USER

# GPIOグループに追加
sudo usermod -a -G gpio $USER

# 再ログイン（または再起動）
sudo reboot
```

### 4. Python仮想環境の作成（必須）

**重要**: 仮想環境は必須です。グローバル環境に直接インストールしないでください。

```bash
cd ~/card_reader_improved

# 仮想環境を作成
python3 -m venv venv

# 仮想環境を有効化（以後のコマンドで使用される）
source venv/bin/activate

# 仮想環境が有効化されたことを確認
# プロンプトに (venv) が表示されることを確認
which python3  # /home/pi/card_reader_improved/venv/bin/python3 と表示される

# pipを最新版に更新
pip install --upgrade pip

# 依存関係をインストール
pip install -r requirements_unified.txt

# インストールされたパッケージを確認（オプション）
pip list

# 仮想環境を無効化（作業終了時）
deactivate
```

**確認ポイント**:
- 仮想環境を有効化すると、プロンプトの先頭に `(venv)` が表示されます
- `which python3` で仮想環境内のPythonが使用されていることを確認できます
- ターミナルを閉じると仮想環境は自動的に無効化されます

### 5. I2CとGPIOの有効化

```bash
# raspi-configを起動
sudo raspi-config

# 以下の設定を有効化：
# - Interface Options → I2C → Enable
# - Interface Options → GPIO → Enable

# 再起動
sudo reboot
```

### 6. カードリーダーの確認

```bash
# USBデバイスを確認
lsusb

# PC/SCリーダーを確認
pcsc_scan
```

---

## ⚙️ 設定ファイルの編集

### 設定ファイルの場所

```bash
~/card_reader_improved/client_config.json
```

### 設定ファイルの編集

```bash
nano client_config.json
```

### 設定例

```json
{
  "server_url": "http://192.168.1.31:5000",
  "retry_interval": 600,
  "lcd_settings": {
    "i2c_addr": 0x27,
    "i2c_bus": 1,
    "backlight": true
  }
}
```

### 設定項目の説明

| 項目 | 説明 | デフォルト値 |
|------|------|-------------|
| `server_url` | サーバーのURL | `http://192.168.1.31:5000` |
| `retry_interval` | リトライ間隔（秒） | `600`（10分） |
| `lcd_settings.i2c_addr` | LCDのI2Cアドレス | `0x27` |
| `lcd_settings.i2c_bus` | I2Cバス番号 | `1` |
| `lcd_settings.backlight` | バックライトの有効/無効 | `true` |

### 保存方法

- `Ctrl+O` → `Enter`（保存）
- `Ctrl+X`（終了）

---

## 🚀 起動方法

### 手動起動

#### 方法1: 起動スクリプトを使用（推奨）

```bash
cd ~/card_reader_improved

# 実行権限を付与（初回のみ）
chmod +x start_pi_simple.sh

# 起動
./start_pi_simple.sh
```

#### 方法2: 直接実行

```bash
cd ~/card_reader_improved

# 仮想環境を有効化（必須）
source venv/bin/activate

# (venv) がプロンプトに表示されることを確認

# シンプル版を起動
python3 pi_client.py

# 終了時
# Ctrl+C でプログラムを終了
# その後、仮想環境を無効化（オプション）
deactivate
```

**重要**: `start_pi_simple.sh`を使う場合は、スクリプト内で自動的に仮想環境が有効化されるため、手動で`source venv/bin/activate`を実行する必要はありません。

### 起動時の表示

正常に起動すると、以下のような情報が表示されます：

```
======================================================================
[ラズパイ版シンプルクライアント]
======================================================================
端末ID: B8:27:EB:XX:XX:XX
DB: attendance.db
LCD: 有効（または無効）
GPIO: 有効（または無効）
nfcpy: 利用可能（または利用不可）
pyscard: 利用可能（または利用不可）

[検出] nfcpyリーダー: usb
（または PC/SCリーダー情報）

[待機] カードをかざしてください... (Ctrl+C で終了)
```

### 終了方法

```bash
Ctrl+C
```

---

## 🔄 自動起動設定

### systemdサービスとして設定

シンプル版用のsystemdサービスファイルを作成します。

#### サービスファイルの作成

```bash
cd ~/card_reader_improved

# サービスファイルを作成
sudo nano /etc/systemd/system/attendance-client-simple.service
```

以下の内容を入力します（`/home/pi` は実際のユーザーディレクトリに変更してください）：

```ini
[Unit]
Description=Attendance Client Service (Simple)
After=network.target pcscd.service
Wants=pcscd.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/card_reader_improved
Environment="PATH=/home/pi/card_reader_improved/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/home/raspberry/Desktop/card_reader_improved/venv/bin/python3 /home/raspberry/Desktop/card_reader_improved/pi_client.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

#### サービスの有効化

```bash
# サービスをリロード
sudo systemctl daemon-reload

# サービスを有効化（自動起動）
sudo systemctl enable attendance-client-simple.service

# サービスを起動
sudo systemctl start attendance-client-simple.service

# サービス状態を確認
sudo systemctl status attendance-client-simple.service
```

### サービスの操作

```bash
# サービスを開始
sudo systemctl start attendance-client-simple.service

# サービスを停止
sudo systemctl stop attendance-client-simple.service

# サービスを再起動
sudo systemctl restart attendance-client-simple.service

# ログを確認
sudo journalctl -u attendance-client-simple.service -f

# サービスの無効化（自動起動を停止）
sudo systemctl disable attendance-client-simple.service
```

---

## 🔧 トラブルシューティング

### カードリーダーが検出されない

#### 確認事項

1. **USB接続の確認**
   ```bash
   lsusb
   # カードリーダーが表示されるか確認
   ```

2. **PC/SCサービスの状態**
   ```bash
   sudo systemctl status pcscd
   # 起動しているか確認
   ```

3. **PC/SCリーダーの確認**
   ```bash
   pcsc_scan
   # リーダーが検出されるか確認
   ```

4. **権限の確認**
   ```bash
   groups
   # pcscdグループに含まれているか確認
   ```

#### 解決方法

```bash
# PC/SCサービスを再起動
sudo systemctl restart pcscd

# ユーザーをpcscdグループに追加（再ログインが必要）
sudo usermod -a -G pcscd $USER
sudo reboot
```

### GPIO権限エラー

#### 症状

```
PermissionError: [Errno 13] Permission denied: '/dev/gpiomem'
```

#### 解決方法

```bash
# GPIOグループに追加
sudo usermod -a -G gpio $USER

# 再ログイン
sudo reboot
```

### LCDが表示されない

#### 確認事項

1. **I2C接続の確認**
   ```bash
   sudo i2cdetect -y 1
   # LCDのI2Cアドレスが表示されるか確認（通常は0x27）
   ```

2. **設定ファイルの確認**
   ```bash
   cat client_config.json | grep i2c_addr
   # I2Cアドレスが正しいか確認
   ```

3. **配線の確認**
   - VCC → 5V
   - GND → GND
   - SDA → GPIO 2（Pin 3）
   - SCL → GPIO 3（Pin 5）

#### 解決方法

```bash
# I2Cを有効化
sudo raspi-config
# Interface Options → I2C → Enable

# 再起動
sudo reboot
```

### サーバーに接続できない

#### 確認事項

1. **サーバーが起動しているか確認**
   ```bash
   curl http://192.168.1.31:5000/api/health
   # 応答があるか確認
   ```

2. **ネットワーク接続の確認**
   ```bash
   ping 192.168.1.31
   # サーバーに到達できるか確認
   ```

3. **設定ファイルの確認**
   ```bash
   cat client_config.json | grep server_url
   # サーバーURLが正しいか確認
   ```

#### 解決方法

```bash
# 設定ファイルを編集
nano client_config.json
# server_urlを正しい値に変更

# クライアントを再起動
sudo systemctl restart attendance-client-simple.service
```

### メモリ不足エラー

シンプル版は統合版よりも軽量ですが、それでもメモリ不足が発生する場合：

1. **不要なプロセスを停止**
2. **仮想環境の再作成**
   ```bash
   rm -rf venv
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements_unified.txt
   ```

---

## 📚 関連ドキュメント

- [Raspberry Pi版セットアップガイド](RASPBERRY_PI_SETUP_GUIDE.md) - 統合版の詳細なセットアップ手順
- [Windows用とRaspberry Pi用を分離した理由](WHY_SEPARATE_WINDOWS_AND_RASPBERRY_PI.md) - 分離の理由と背景
- [自動起動設定ガイド](AUTOSTART_GUIDE.md)
- [トラブルシューティング](TROUBLESHOOTING.md)

---

## 💡 仮想環境について

### なぜ仮想環境が必要なのか？

1. **依存関係の分離**: システムのPython環境を汚染しない
2. **バージョン管理**: 必要なパッケージのバージョンを固定
3. **再現性**: 他のマシンでも同じ環境を再現可能
4. **クリーンアップ**: プロジェクト削除時に依存関係も簡単に削除

### 仮想環境の有効化

```bash
# プロジェクトディレクトリに移動
cd ~/card_reader_improved

# 仮想環境を有効化
source venv/bin/activate

# 確認: プロンプトに (venv) が表示される
# 確認: 仮想環境のPythonが使用される
which python3
```

### 仮想環境の無効化

```bash
# 仮想環境を無効化
deactivate

# プロンプトから (venv) が消える
```

### 仮想環境が作成されていない場合

```bash
cd ~/card_reader_improved

# 仮想環境を作成
python3 -m venv venv

# 有効化
source venv/bin/activate

# 依存関係をインストール
pip install -r requirements_unified.txt
```

---

## 🎯 まとめ

シンプル版のセットアップは以下の手順で完了します：

1. ✅ Raspberry Pi OSのインストール
2. ✅ I2CとGPIOの有効化
3. ✅ **仮想環境の作成（必須）**
4. ✅ 自動セットアップスクリプトの実行
5. ✅ 設定ファイルの編集
6. ✅ シンプル版の起動または自動起動設定

**重要なポイント**:
- ⚠️ 仮想環境は必須です。必ず`venv`ディレクトリに仮想環境を作成してください
- ⚠️ 手動起動時は`start_pi_simple.sh`を使用すると、自動的に仮想環境が有効化されます
- ⚠️ 直接実行する場合は、事前に`source venv/bin/activate`を実行してください

問題が発生した場合は、[トラブルシューティング](#トラブルシューティング)セクションを参照してください。

---

**シンプル版の特徴を活かして、軽量で安定した動作を実現しましょう！** 🚀
