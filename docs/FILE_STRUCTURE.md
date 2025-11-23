# ファイル構成ガイド

このドキュメントでは、プロジェクトのファイル構成と各ファイルの役割を説明します。

---

## 📁 プロジェクト構成

```
card_reader_improved/
├── クライアント（クライアント側プログラム）
│   ├── win_client.py              # Windows版クライアント
│   ├── pi_client.py               # Raspberry Pi版クライアント（メイン）
│   ├── pi_client_full_backup.py   # 旧統合版（バックアップ・参考用）
│   ├── pi_client_simple.py        # 旧シンプル版（削除予定）
│   ├── config.py                  # 設定GUI（サーバーURL・LCD設定）
│   │
│   ├── 共通モジュール
│   ├── common_utils.py            # 共通ユーティリティ関数
│   ├── constants.py               # 共通定数定義
│   ├── gpio_config.py             # GPIO設定（Raspberry Pi用）
│   ├── lcd_i2c.py                 # LCD制御（Raspberry Pi用）
│   │
│   ├── 設定ファイル
│   ├── client_config.json         # クライアント設定（サーバーURL等）
│   ├── client_config_sample.json  # 設定ファイルサンプル
│   │
│   ├── 起動スクリプト（Windows）
│   ├── start_win.bat              # Windows版起動
│   ├── start_venv.bat             # Windows仮想環境起動
│   │
│   ├── 起動スクリプト（Raspberry Pi）
│   ├── start_pi.sh                # Raspberry Pi版起動（メイン）
│   ├── start_pi_simple.sh         # 旧シンプル版起動（削除予定）
│   │
│   ├── セットアップスクリプト（Raspberry Pi）
│   ├── auto_setup.sh              # 自動セットアップ
│   ├── setup.sh                   # セットアップスクリプト
│   ├── setup_autostart_fixed.sh   # 自動起動設定
│   │
│   └── その他
│       ├── memory_monitor.py      # メモリモニタリング（オプション）
│       └── requirements_unified.txt  # Raspberry Pi依存関係
│       └── requirements_windows.txt  # Windows依存関係
│
└── docs/                          # ドキュメント
    ├── SETUP_GUIDE.md             # セットアップガイド
    ├── RASPBERRY_PI_SETUP_GUIDE.md  # Raspberry Pi詳細セットアップ
    ├── FILE_STRUCTURE.md          # このファイル
    └── ...
```

---

## 🔑 主要ファイルの説明

### Windows版

| ファイル | 説明 | 環境 |
|---------|------|------|
| `win_client.py` | Windows版クライアント（GUI付き） | Windows専用 |
| `config.py` | 設定GUI（Windows/Raspberry Pi共通） | 両方 |

### Raspberry Pi版

| ファイル | 説明 | 環境 |
|---------|------|------|
| `pi_client.py` | **Raspberry Pi版クライアント（メイン）** | Raspberry Pi専用 |
| `pi_client_full_backup.py` | 旧統合版（バックアップ・参考用） | Raspberry Pi専用 |
| `pi_client_simple.py` | **削除予定**（pi_client.pyに統合済み） | Raspberry Pi専用 |

**重要**: Raspberry Pi版は`pi_client.py`のみを使用します。`pi_client_simple.py`は削除予定です。

### 共通モジュール

| ファイル | 説明 | 環境 |
|---------|------|------|
| `common_utils.py` | 共通ユーティリティ関数（MAC取得、設定読み込み、サーバー通信等） | 両方 |
| `constants.py` | 共通定数定義 | 両方 |
| `gpio_config.py` | GPIO設定（LEDピン、ブザーピン等） | Raspberry Pi専用 |
| `lcd_i2c.py` | LCD制御（I2C 1602） | Raspberry Pi専用 |

### 設定ファイル

| ファイル | 説明 |
|---------|------|
| `client_config.json` | クライアント設定（サーバーURL、LCD設定、リトライ間隔等） |
| `client_config_sample.json` | 設定ファイルサンプル |

### 起動スクリプト

| ファイル | 説明 | 環境 |
|---------|------|------|
| `start_win.bat` | Windows版起動 | Windows |
| `start_pi.sh` | Raspberry Pi版起動（メイン） | Raspberry Pi |
| `start_pi_simple.sh` | **削除予定**（start_pi.shに統合済み） | Raspberry Pi |

---

## 🎯 環境分離の原則

### なぜWindows版とRaspberry Pi版を分離しているのか？

1. **環境依存ライブラリの競合を避ける**
   - Windows: `winsound`（PCスピーカー）
   - Raspberry Pi: `RPi.GPIO`（GPIO制御）

2. **コードの簡潔化**
   - 各環境専用のコードのみを記述
   - 環境判定の`if`文が不要

3. **保守性の向上**
   - バグ修正時に、該当環境のみを修正
   - テストが容易

詳細は [WHY_SEPARATE_WINDOWS_AND_RASPBERRY_PI.md](WHY_SEPARATE_WINDOWS_AND_RASPBERRY_PI.md) を参照してください。

---

## 📝 共通処理の管理

### `common_utils.py`に集約した処理

以下の処理は両環境で共通なので、`common_utils.py`に集約されています：

- `get_mac_address()` - MACアドレス取得
- `load_config()` - 設定ファイル読み込み
- `save_config()` - 設定ファイル保存
- `check_server_connection()` - サーバー接続チェック
- `send_attendance_to_server()` - サーバーへのデータ送信
- `get_pcsc_commands()` - PC/SCコマンド取得
- `is_valid_card_id()` - カードID検証
- `is_duplicate_attendance()` - 重複打刻チェック

### 各環境専用の処理

| 環境 | 専用処理 |
|------|---------|
| **Windows** | PCスピーカー制御、GUI表示 |
| **Raspberry Pi** | GPIO制御、LCD表示、ブザー制御 |

---

## 🔄 今後の開発方針

### 統一方針

- ✅ **Raspberry Pi版は`pi_client.py`のみ**（シンプル版に統一）
- ✅ **Windows版とRaspberry Pi版は完全に分離**
- ✅ **共通処理は`common_utils.py`に集約**

### 削除予定ファイル

以下のファイルは削除予定です：

- `pi_client_simple.py` - `pi_client.py`に統合済み
- `start_pi_simple.sh` - `start_pi.sh`を使用

### バックアップファイル

以下のファイルは参考用に残していますが、通常は使用しません：

- `pi_client_full_backup.py` - 旧統合版（参考用）

---

## 🚀 使い方

### Windows版の起動

```cmd
# 設定GUIで設定
python config.py

# クライアント起動
python win_client.py
```

### Raspberry Pi版の起動

```bash
# 設定GUIで設定（オプション）
python3 config.py

# クライアント起動
./start_pi.sh

# または直接実行
source venv/bin/activate
python3 pi_client.py
```

---

## 📚 関連ドキュメント

- [セットアップガイド](SETUP_GUIDE.md)
- [Raspberry Pi版セットアップガイド](RASPBERRY_PI_SETUP_GUIDE.md)
- [Windows版とRaspberry Pi版を分離した理由](WHY_SEPARATE_WINDOWS_AND_RASPBERRY_PI.md)
- [開発者向けREADME](README_FOR_DEVELOPERS.md)

