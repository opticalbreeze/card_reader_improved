# ラズパイ版セットアップガイド（初めてから）

このガイドでは、Raspberry Piを**ゼロからセットアップ**する手順を説明します。

**重要**: カードリーダーが正しく認識され動作するには、**仮想環境で実行する必要があります**。

---

## 📋 目次

1. [事前準備](#事前準備)
2. [自動セットアップ（推奨）](#自動セットアップ推奨)
3. [手動セットアップ](#手動セットアップ)
4. [設定ファイルの編集](#設定ファイルの編集)
5. [起動方法](#起動方法)
6. [トラブルシューティング](#トラブルシューティング)

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

### 3. SSHの有効化（リモート接続する場合）

```bash
sudo systemctl enable ssh
sudo systemctl start ssh
```

---

## 🚀 自動セットアップ（推奨）

### ステップ1: リポジトリのクローン

```bash
cd ~/Desktop
git clone https://github.com/opticalbreeze/card_reader_improved.git
cd card_reader_improved
```

### ステップ2: セットアップスクリプトの実行

```bash
# 実行権限を付与
chmod +x setup.sh

# セットアップスクリプトを実行
./setup.sh
```

### セットアップスクリプトが行うこと

1. **システムパッケージのインストール**
   - Python 3、pip、python3-venv
   - PC/SCライブラリ（pcscd、libccid）
   - I2Cツール（i2c-tools、python3-smbus）
   - USBデバイス用ライブラリ（libusb-1.0-0-dev）

2. **I2Cの有効化**
   - `/boot/config.txt`に`dtparam=i2c_arm=on`を追加
   - ユーザーを`i2c`グループに追加

3. **Python仮想環境の作成**
   - `venv`ディレクトリに仮想環境を作成
   - 仮想環境内に必要なライブラリをインストール

4. **カードリーダーのアクセス権限設定**
   - udevルールの設定（Sony RC-S380用）
   - ユーザーを`plugdev`グループに追加

5. **PC/SCサービスの設定**
   - pcscdサービスの有効化・起動
   - ユーザーを`pcscd`グループに追加

### ステップ3: 再起動（必須）

セットアップ後、**必ず再起動**してください：

```bash
sudo reboot
```

**重要**: グループ設定（i2c、plugdev、pcscd）を有効にするには、再起動が必要です。

---

## 🛠️ 手動セットアップ

自動セットアップがうまくいかない場合、手動でセットアップできます。

### ステップ1: システムパッケージのインストール

```bash
sudo apt update
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    python3-smbus \
    i2c-tools \
    libusb-1.0-0-dev \
    pcscd \
    libccid \
    pcsc-tools
```

### ステップ2: I2Cの有効化

```bash
# I2Cを有効化
sudo raspi-config
# Interface Options → I2C → Enable

# または直接編集
echo "dtparam=i2c_arm=on" | sudo tee -a /boot/config.txt

# ユーザーをi2cグループに追加
sudo usermod -a -G i2c $USER
```

### ステップ3: Python仮想環境の作成と有効化

```bash
cd ~/Desktop/card_reader_improved

# 仮想環境を作成
python3 -m venv venv

# 仮想環境を有効化
source venv/bin/activate

# pipをアップグレード
pip install --upgrade pip

# 依存関係をインストール
pip install -r requirements_pi.txt
```

**重要**: 仮想環境は**毎回起動時に有効化する必要があります**。

### ステップ4: カードリーダーのアクセス権限設定

```bash
# udevルールを作成
echo 'SUBSYSTEM=="usb", ACTION=="add", ATTRS{idVendor}=="054c", ATTRS{idProduct}=="06c1", GROUP="plugdev"' | sudo tee /etc/udev/rules.d/nfcdev.rules

# udevルールをリロード
sudo udevadm control --reload-rules

# ユーザーをplugdevグループに追加
sudo usermod -a -G plugdev $USER
```

### ステップ5: PC/SCサービスの設定

```bash
# pcscdサービスを有効化・起動
sudo systemctl enable pcscd
sudo systemctl start pcscd

# ユーザーをpcscdグループに追加
sudo usermod -a -G pcscd $USER
```

### ステップ6: 再起動

```bash
sudo reboot
```

---

## ⚙️ 設定ファイルの編集

セットアップ完了後、設定ファイルを編集します。

### 方法1: GUI設定ツールを使う（推奨）

```bash
cd ~/Desktop/card_reader_improved
source venv/bin/activate  # 仮想環境を有効化（必須）
python3 config.py
```

GUIで以下を設定：
- **サーバーURL**: 打刻データを送信するサーバーのIPアドレス
- **LCD設定**（オプション）: I2Cアドレス、バス番号

### 方法2: 直接編集

```bash
nano client_config.json
```

設定例：

```json
{
  "server_url": "http://192.168.1.31:5000",
  "retry_interval": 600,
  "lcd_settings": {
    "i2c_addr": 39,
    "i2c_bus": 1,
    "backlight": true
  }
}
```

---

## 🚀 起動方法

**重要**: カードリーダーが正しく認識されるには、**仮想環境で実行する必要があります**。

### 方法1: 起動スクリプトを使う（推奨）

起動スクリプトは自動的に仮想環境を有効化します。

```bash
cd ~/Desktop/card_reader_improved

# シンプル起動
./start_pi_simple.sh

# または詳細起動（USBデバイス確認、権限確認など）
./start_pi.sh
```

### 方法2: 手動で起動

```bash
cd ~/Desktop/card_reader_improved

# 仮想環境を有効化（必須）
source venv/bin/activate

# プログラムを起動
python3 pi_client.py
```

### 方法3: 設定GUIから起動

```bash
cd ~/Desktop/card_reader_improved
source venv/bin/activate  # 仮想環境を有効化（必須）
python3 config.py
```

GUIで「保存して起動」ボタンをクリックすると、自動的に`pi_client.py`が起動します。

---

## 🔍 トラブルシューティング

### 問題1: カードリーダーが認識されない

**原因**: 仮想環境で実行していない可能性があります。

**解決方法**:
```bash
# 仮想環境を有効化してから実行
source venv/bin/activate
python3 pi_client.py
```

### 問題2: PC/SCエラーが出る

**原因**: pcscdグループに所属していない、またはサービスが起動していない。

**解決方法**:
```bash
# pcscdグループに追加
sudo usermod -a -G pcscd $USER

# 再ログインまたは再起動
sudo reboot

# サービスが起動しているか確認
systemctl status pcscd
```

### 問題3: I2Cデバイスが認識されない

**原因**: I2Cが有効化されていない、またはi2cグループに所属していない。

**解決方法**:
```bash
# I2Cを有効化
sudo raspi-config
# Interface Options → I2C → Enable

# i2cグループに追加
sudo usermod -a -G i2c $USER

# 再起動
sudo reboot

# I2Cデバイスを確認
i2cdetect -y 1
```

### 問題4: GPIO（LED、ブザー）が動作しない

**原因**: 権限の問題、またはGPIOが正しく初期化されていない。

**確認方法**:
```bash
# 実行時にGPIO初期化ログを確認
source venv/bin/activate
python3 pi_client.py
```

ログに以下が表示されれば正常：
```
[GPIO] 初期化成功
[GPIO状態] available=True
```

### 問題5: 仮想環境が正しく作成されていない

**確認方法**:
```bash
# 仮想環境の存在を確認
ls -la venv/

# Pythonのバージョンを確認
source venv/bin/activate
python3 --version

# インストール済みパッケージを確認
pip list
```

**再作成方法**:
```bash
# 仮想環境を削除
rm -rf venv

# 再作成
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements_pi.txt
```

---

## ✅ 動作確認

セットアップ完了後、以下を確認してください：

1. **仮想環境が有効化されているか**
   ```bash
   which python3  # /home/raspberry/Desktop/card_reader_improved/venv/bin/python3 と表示されればOK
   ```

2. **カードリーダーが認識されているか**
   ```bash
   lsusb  # Sony RC-S380などのデバイスが表示されればOK
   ```

3. **PC/SCサービスが起動しているか**
   ```bash
   systemctl status pcscd  # active (running) と表示されればOK
   ```

4. **プログラムが起動するか**
   ```bash
   source venv/bin/activate
   python3 pi_client.py  # エラーなく起動すればOK
   ```

---

## 📝 まとめ

1. **セットアップ**: `./setup.sh`を実行
2. **再起動**: `sudo reboot`
3. **設定**: `python3 config.py`でサーバーURLを設定
4. **起動**: `./start_pi_simple.sh`で起動（仮想環境は自動有効化）

**重要**: カードリーダーが正しく動作するには、**必ず仮想環境で実行してください**。

