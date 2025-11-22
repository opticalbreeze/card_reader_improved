# セットアップガイド

このガイドでは、Windows版とRaspberry Pi版のセットアップ方法を説明します。

---

## 📋 目次

1. [Windows版セットアップ](#windows版セットアップ)
2. [Raspberry Pi版セットアップ](#raspberry-pi版セットアップ)
3. [サーバー側セットアップ](#サーバー側セットアップ)
4. [トラブルシューティング](#トラブルシューティング)

---

## 🪟 Windows版セットアップ

### 必要なもの

- Windows 10/11
- Python 3.7以上
- ICカードリーダー（Sony RC-S380、Circle CIR315等）
- インターネット接続

### セットアップ手順

#### 1. ファイルのダウンロード

```cmd
cd C:\Users\YourName\Desktop
git clone https://github.com/opticalbreeze/card_reader_improved.git
cd card_reader_improved
```

または、ZIPファイルをダウンロードして解凍

#### 2. 依存パッケージのインストール

```cmd
pip install -r requirements_windows.txt
```

**注意**: `pyscard`のインストールでエラーが出る場合：
- Microsoft Visual C++ Build Toolsが必要な場合があります
- https://visualstudio.microsoft.com/ja/visual-cpp-build-tools/ からインストール

#### 3. カードリーダーの接続

- USBポートにカードリーダーを接続
- デバイスマネージャーで認識を確認

#### 4. 設定ファイルの作成

`config.py`を実行して設定GUIを起動：

```cmd
python config.py
```

または、`client_config.json`を直接編集：

```json
{
  "server_url": "http://192.168.1.31:5000",
  "retry_interval": 600,
  "beep_settings": {
    "enabled": true,
    "card_read": false,
    "success": true,
    "fail": true
  }
}
```

#### 5. クライアントの起動

**GUI版（推奨）:**
```cmd
python win_client.py
```

**CUI版:**
```cmd
python pi_client.py
```

---

## 🍓 Raspberry Pi版セットアップ

**詳細なセットアップガイドは [Raspberry Pi版セットアップガイド](RASPBERRY_PI_SETUP_GUIDE.md) を参照してください。**

### クイックスタート

#### 1. ファイルのダウンロード

```bash
cd ~
git clone https://github.com/opticalbreeze/card_reader_improved.git
cd card_reader_improved
```

#### 2. 自動セットアップの実行

```bash
chmod +x auto_setup.sh
./auto_setup.sh
```

**所要時間：約5-10分**

#### 3. 再起動

```bash
sudo reboot
```

#### 4. 設定ファイルの編集

```bash
nano client_config.json
```

サーバーURLを設定：
```json
{
  "server_url": "http://192.168.1.31:5000",
  "lcd_settings": {
    "i2c_addr": 0x27,
    "i2c_bus": 1,
    "backlight": true
  }
}
```

保存：`Ctrl+O` → `Enter` → `Ctrl+X`

#### 5. クライアントの起動

**手動起動:**
```bash
source venv/bin/activate
python3 pi_client.py
```

**自動起動設定:**
```bash
chmod +x setup_autostart_fixed.sh
sudo bash setup_autostart_fixed.sh
```

### 詳細情報

- [Raspberry Pi版セットアップガイド](RASPBERRY_PI_SETUP_GUIDE.md) - 詳細なセットアップ手順
- [Windows用とRaspberry Pi用を分離した理由](WHY_SEPARATE_WINDOWS_AND_RASPBERRY_PI.md) - 分離の理由と背景

---

## 🖥️ サーバー側セットアップ

### Windows版サーバー

#### 1. サーバーファイルの配置

サーバーファイルを配置：
```
C:\Users\YourName\Desktop\server\
├── server.py
├── start_server.bat
├── requirements_server.txt
└── templates/
    ├── index.html
    └── search.html
```

#### 2. 依存パッケージのインストール

```cmd
cd C:\Users\YourName\Desktop\server
pip install flask
```

#### 3. サーバーの起動

```cmd
python server.py
```

または、`start_server.bat`をダブルクリック

#### 4. 動作確認

ブラウザで `http://サーバーIP:5000` にアクセス

### Docker版サーバー（推奨）

```cmd
cd C:\Users\YourName\Desktop\server
docker-compose up -d
```

---

## 🔧 トラブルシューティング

詳細は [トラブルシューティングガイド](TROUBLESHOOTING.md) を参照してください。

### よくある問題

#### カードリーダーが検出されない

1. USBポートを確認
2. ドライバーのインストール確認
3. 別のUSBポートで試す

#### サーバーに接続できない

1. サーバーが起動しているか確認
2. ファイアウォール設定を確認
3. 同じネットワークに接続しているか確認
4. `client_config.json`のサーバーIPを確認

---

## 📚 関連ドキュメント

### Raspberry Pi版
- [Raspberry Pi版セットアップガイド](RASPBERRY_PI_SETUP_GUIDE.md) - 詳細なセットアップ手順
- [Windows用とRaspberry Pi用を分離した理由](WHY_SEPARATE_WINDOWS_AND_RASPBERRY_PI.md) - 分離の理由と背景
- [自動起動設定ガイド](AUTOSTART_GUIDE.md)
- [PC/SC自動起動問題分析](PCSC_AUTOSTART_ISSUE_ANALYSIS.md)

### 共通
- [更新ガイド](UPDATE_GUIDE.md)
- [トラブルシューティング](TROUBLESHOOTING.md)
- [Git操作ガイド](GIT_GUIDE.md)

