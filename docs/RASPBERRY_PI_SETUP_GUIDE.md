# Raspberry Pi版セットアップガイド

このガイドでは、Raspberry Pi版のセットアップ方法を詳しく説明します。

---

## 📋 目次

1. [必要なもの](#必要なもの)
2. [事前準備](#事前準備)
3. [自動セットアップ（推奨）](#自動セットアップ推奨)
4. [手動セットアップ](#手動セットアップ)
5. [設定ファイルの編集](#設定ファイルの編集)
6. [起動方法](#起動方法)
7. [自動起動設定](#自動起動設定)
8. [トラブルシューティング](#トラブルシューティング)

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

## 🔧 事前準備

### 1. Raspberry Pi OSのインストール

1. [Raspberry Pi Imager](https://www.raspberrypi.com/software/)をダウンロード
2. microSDカードにRaspberry Pi OSを書き込み
3. microSDカードをRaspberry Piに挿入して起動

### 2. 初期設定

```bash
# システムを更新
sudo apt update
sudo apt upgrade -y

# 再起動
sudo reboot
```

### 3. I2CとGPIOの有効化

```bash
# raspi-configを起動
sudo raspi-config

# 以下の設定を有効化：
# - Interface Options → I2C → Enable
# - Interface Options → GPIO → Enable

# 再起動
sudo reboot
```

---

## 🚀 自動セットアップ（推奨）

### セットアップスクリプトの実行

```bash
# ファイルをダウンロード
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

2. **Python仮想環境の作成**
   - `venv`を使用して仮想環境を作成
   - 依存関係を自動インストール

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

### 4. Python仮想環境の作成

```bash
cd ~/card_reader_improved

# 仮想環境を作成
python3 -m venv venv

# 仮想環境を有効化
source venv/bin/activate

# 依存関係をインストール
pip install --upgrade pip
pip install -r requirements_unified.txt
```

### 5. カードリーダーの確認

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
  },
  "memory_monitor": {
    "enabled": false,
    "interval": 300,
    "tracemalloc": false
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
| `memory_monitor.enabled` | メモリモニタリングの有効/無効 | `false` |

### 保存方法

- `Ctrl+O` → `Enter`（保存）
- `Ctrl+X`（終了）

---

## 🚀 起動方法

### 手動起動

#### 統合版（推奨）

```bash
cd ~/card_reader_improved
source venv/bin/activate
python3 pi_client.py
```

#### シンプル版（軽量）

```bash
cd ~/card_reader_improved
source venv/bin/activate
python3 pi_client_simple.py
```

### 起動スクリプトを使用

```bash
# 統合版
chmod +x start_pi.sh
./start_pi.sh

# シンプル版
chmod +x start_pi_simple.sh
./start_pi_simple.sh
```

---

## 🔄 自動起動設定

### systemdサービスとして設定

```bash
# 自動起動設定スクリプトを実行
chmod +x setup_autostart_fixed.sh
sudo bash setup_autostart_fixed.sh
```

### サービスファイルの確認

```bash
# サービスファイルの場所
cat /etc/systemd/system/attendance-client-fixed.service
```

### サービスの操作

```bash
# サービスを開始
sudo systemctl start attendance-client-fixed.service

# サービスを有効化（自動起動）
sudo systemctl enable attendance-client-fixed.service

# サービス状態を確認
sudo systemctl status attendance-client-fixed.service

# ログを確認
sudo journalctl -u attendance-client-fixed.service -f

# サービスを停止
sudo systemctl stop attendance-client-fixed.service

# サービスを無効化
sudo systemctl disable attendance-client-fixed.service
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
sudo systemctl restart attendance-client-fixed.service
```

### 自動起動が動作しない

#### 確認事項

1. **サービスファイルの確認**
   ```bash
   sudo systemctl status attendance-client-fixed.service
   ```

2. **ログの確認**
   ```bash
   sudo journalctl -u attendance-client-fixed.service -n 100
   ```

3. **環境変数の確認**
   - 仮想環境のパスが正しいか
   - 作業ディレクトリが正しいか

#### 解決方法

詳細は [PC/SC自動起動問題分析](PCSC_AUTOSTART_ISSUE_ANALYSIS.md) を参照してください。

---

## 📚 関連ドキュメント

- [Windows用とRaspberry Pi用を分離した理由](WHY_SEPARATE_WINDOWS_AND_RASPBERRY_PI.md)
- [自動起動設定ガイド](AUTOSTART_GUIDE.md)
- [トラブルシューティング](TROUBLESHOOTING.md)
- [PC/SC自動起動問題分析](PCSC_AUTOSTART_ISSUE_ANALYSIS.md)
- [LED接続ガイド](LED_CONNECTION_GUIDE.md)
- [LCD接続ガイド](HARDWARE_BUZZER_READER_GUIDE.md)

---

## 🎯 まとめ

Raspberry Pi版のセットアップは以下の手順で完了します：

1. ✅ Raspberry Pi OSのインストール
2. ✅ I2CとGPIOの有効化
3. ✅ 自動セットアップスクリプトの実行
4. ✅ 設定ファイルの編集
5. ✅ 自動起動設定

問題が発生した場合は、[トラブルシューティング](#トラブルシューティング)セクションを参照してください。

