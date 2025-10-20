# nfcpy版クライアント - Sony RC-S380専用

## 📋 概要

Sony RC-S380/RC-S330/PaSoRi専用のnfcpyライブラリを使用したクライアント。
ラズパイではGPIO制御（圧電ブザー + カラーLED + LCD I2C 1602）に対応。

## 🎯 バージョン一覧

### 1. PCSC版（標準）
**ファイル**: `client_card_reader.py`
- Circle CIR315 CL等対応
- Windows/Linux両対応
- 標準的なPC/SCドライバー

### 2. 統合版（ラズパイ推奨）★
**ファイル**: `client_card_reader_unified.py`
- nfcpy + PCSC両対応
- LCD I2C 1602対応
- GPIO制御（ブザー + カラーLED）
- サーバー監視（1時間ごと）
- 自動再接続

### 3. Windows GUI版
**ファイル**: `client_card_reader_windows_gui.py`
- Tkinter GUI
- PCスピーカー対応
- nfcpy + PCSC両対応
- リアルタイムステータス表示

## 🔧 GPIO配線図（ラズパイ）

### 圧電ブザー
```
GPIO 18 ──────┐
              ├─ 圧電ブザー
GND ──────────┘
```

### カラーLED（共通カソード）
```
GPIO 13 ─── 抵抗(330Ω) ─── 赤LED
GPIO 19 ─── 抵抗(330Ω) ─── 緑LED  
GPIO 26 ─── 抵抗(330Ω) ─── 青LED
                           │
GND ───────────────────────┘
```

### LCD I2C 1602
```
GPIO 2 (SDA) ─── LCD SDA
GPIO 3 (SCL) ─── LCD SCL
5V ──────────── LCD VCC
GND ─────────── LCD GND
```

## 📦 インストール

### ラズパイ
```bash
# 統合版の依存関係
pip3 install -r requirements_unified.txt

# システムパッケージ
sudo apt install -y python3-smbus i2c-tools
sudo apt install -y libusb-1.0-0-dev

# I2Cを有効化
sudo raspi-config
# 3 Interface Options > I5 I2C > Yes

# 再起動
sudo reboot
```

### Windows
```bash
# Windows版の依存関係
pip install -r requirements_windows.txt
```

## 🚀 使用方法

### ラズパイ統合版
```bash
cd ~/simple_card_reader
source venv/bin/activate
python3 client_card_reader_unified.py
```

### Windows GUI版
```cmd
cd D:\devfolder\simple_card_reader
python client_card_reader_windows_gui.py
```

## 🎨 LED色の意味

| 色 | 状態 |
|----|------|
| 🔴 赤 | コード開始 |
| 🟢 緑 | サーバー接続成功 |
| 🔵 青 | カード読み取り・送信成功 |
| 🟠 オレンジ | 送信失敗 |
| 🟠 オレンジ点滅 | サーバー未接続 |

## 🔊 ブザー音の意味

| パターン | タイミング |
|----------|-----------|
| 長-短-長 | 起動時 |
| 短-短-短 | サーバー接続時 |
| 短 | カード読み込み時 |
| 高音・短-短-短 | 送信成功時 |
| 低音・長-短-長 | 送信失敗時 |

## 📺 LCD表示（1602 I2C）

### 1行目
```
2025/10/20 15:30
```
リアルタイムで日時を表示

### 2行目（状態に応じて変化）
```
サーバー カクニンズミ   (2秒表示)
カード ヲ タッチ        (待機中)
カード ヲ ヨミマシタ    (1秒表示)
サーバー ニ キロク      (1秒表示)
ローカル ニ キロク      (1秒表示)
サイセツゾク1/2         (再接続中)
サーバー セツゾクNG     (接続失敗)
```

## ⚙️ サーバー監視機能

- **監視間隔**: 1時間ごと
- **自動再接続**: 2回まで試行
- **失敗時**: 1時間後に再試行
- **LED表示**: オレンジ点滅で通知

## 🔄 対応リーダー

### nfcpy対応
- Sony RC-S380/S ✅
- Sony RC-S330 ✅
- Sony PaSoRi RC-S320 ✅

### PCSC対応
- Circle CIR315 CL ✅
- ACS ACR122U ✅
- その他PC/SC互換リーダー ✅

## 📝 設定ファイル

`client_config.json`
```json
{
  "server_url": "http://192.168.11.24:5000"
}
```

## 🐛 トラブルシューティング

### LCDが表示されない
```bash
# I2Cアドレス確認
i2cdetect -y 1

# 0x27が表示されればOK
# 表示されない場合は配線を確認
```

### GPIOが動作しない
```bash
# GPIO権限
sudo usermod -a -G gpio $USER
# 再ログイン
```

### カードリーダーが検出されない
```bash
# USB確認
lsusb

# nfcpy確認
python3 -c "import nfc; clf=nfc.ContactlessFrontend('usb'); print(clf.device if clf else 'Not found')"

# PCSC確認
python3 -c "from smartcard.System import readers; print(len(readers()))"
```

## 🎉 まとめ

2つのバージョンで、すべてのカードリーダーに対応：

- **ラズパイ**: 統合版（LCD + GPIO + nfcpy/PCSC）
- **Windows**: GUI版（PCスピーカー + nfcpy/PCSC）

Sony RC-S380の在庫を有効活用しながら、Circle CIR315等も並列使用可能！

