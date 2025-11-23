# プロジェクト構造と開発方針

このドキュメントでは、プロジェクトの構造と今後の開発方針を明確に定義します。

---

## 📋 基本方針

### 1. 環境分離の徹底

**Windows版とRaspberry Pi版は完全に分離して開発します。**

| 版 | ファイル | 説明 |
|---|---------|------|
| **Windows版** | `win_client.py` | Windows専用クライアント（GUI付き） |
| **Raspberry Pi版** | `pi_client.py` | Raspberry Pi専用クライアント |

**重要**: 共通コード化を避けることで、各環境での不動作を防ぎます。

### 2. Raspberry Pi版の統一

**Raspberry Pi版は1つのファイルのみ使用します。**

- ✅ **`pi_client.py`** - メインクライアント（使用中）
- ❌ **`pi_client_simple.py`** - 削除予定（既に`pi_client.py`に統合済み）
- 📦 **`pi_client_full_backup.py`** - 旧統合版（バックアップ・参考用）

---

## 📁 ファイル構成

### メインファイル

```
card_reader_improved/
├── win_client.py              # Windows版クライアント（GUI付き）
├── pi_client.py               # Raspberry Pi版クライアント（メイン）
│
├── config.py                  # 設定GUI（Windows/Raspberry Pi共通）
│
├── common_utils.py            # 共通ユーティリティ関数
├── constants.py               # 共通定数定義
├── gpio_config.py             # GPIO設定（Raspberry Pi用）
├── lcd_i2c.py                 # LCD制御（Raspberry Pi用）
│
├── client_config.json         # クライアント設定ファイル
├── client_config_sample.json  # 設定ファイルサンプル
│
├── start_win.bat              # Windows版起動スクリプト
├── start_pi.sh                # Raspberry Pi版起動スクリプト（メイン）
│
├── requirements_windows.txt   # Windows依存関係
└── requirements_unified.txt   # Raspberry Pi依存関係
```

### バックアップ・参考用ファイル

```
├── pi_client_full_backup.py   # 旧統合版（参考用・通常は使用しない）
├── pi_client_simple.py        # 旧シンプル版（削除予定）
└── start_pi_simple.sh         # 旧シンプル版起動（削除予定）
```

---

## 🎯 開発方針

### 原則

1. **Windows版とRaspberry Pi版は完全に分離**
   - 共通コード化による不動作を防止
   - 各環境に最適化されたコードを記述

2. **Raspberry Pi版は`pi_client.py`のみ**
   - シンプル版に統一（統合版の複雑さによる問題を回避）
   - 必要な機能のみを実装

3. **共通処理は`common_utils.py`に集約**
   - MACアドレス取得
   - 設定ファイル読み込み
   - サーバー通信
   - カードID検証

### 禁止事項

- ❌ Windows版とRaspberry Pi版のコードを混在させない
- ❌ 環境判定の`if`文を多用しない
- ❌ Raspberry Pi版を複数ファイルに分割しない

---

## 🔧 設定ファイル（client_config.json）

### 設定項目

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

### 設定方法

#### 方法1: config.pyを使用（推奨）

```bash
# Windows
python config.py

# Raspberry Pi
python3 config.py
```

#### 方法2: 直接編集

```bash
# Windows
notepad client_config.json

# Raspberry Pi
nano client_config.json
```

---

## 🚀 起動方法

### Windows版

```cmd
# 設定（初回のみ）
python config.py

# 起動
python win_client.py
```

### Raspberry Pi版

```bash
# 設定（初回のみ）
python3 config.py

# 起動（推奨）
./start_pi.sh

# または直接実行
source venv/bin/activate
python3 pi_client.py
```

---

## 📚 関連ドキュメント

- [ファイル構成ガイド](FILE_STRUCTURE.md)
- [Windows版とRaspberry Pi版を分離した理由](WHY_SEPARATE_WINDOWS_AND_RASPBERRY_PI.md)
- [セットアップガイド](SETUP_GUIDE.md)
- [Raspberry Pi版セットアップガイド](RASPBERRY_PI_SETUP_GUIDE.md)

---

## 🔄 今後の変更

### 削除予定ファイル

以下のファイルは削除予定です：

- `pi_client_simple.py` - `pi_client.py`に統合済み
- `start_pi_simple.sh` - `start_pi.sh`を使用

### バックアップファイル

以下のファイルは参考用に残していますが、通常は使用しません：

- `pi_client_full_backup.py` - 旧統合版（参考用）

