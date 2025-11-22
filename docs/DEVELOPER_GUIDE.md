# 開発者ガイド

このガイドでは、プロジェクトの開発に参加する開発者向けに、コードの構造、規約、ベストプラクティスを説明します。

---

## 📋 目次

1. [プロジェクト構造](#プロジェクト構造)
2. [コーディング規約](#コーディング規約)
3. [定数の管理](#定数の管理)
4. [エラーハンドリング](#エラーハンドリング)
5. [テストとデバッグ](#テストとデバッグ)
6. [コードレビュー](#コードレビュー)

---

## 📁 プロジェクト構造

### ディレクトリ構成

```
card_reader_improved/
├── クライアントプログラム
│   ├── pi_client.py              # Raspberry Pi版（統合版）
│   ├── pi_client_simple.py       # Raspberry Pi版（シンプル版）
│   └── win_client.py             # Windows版
│
├── 共通モジュール
│   ├── common_utils.py           # 共通ユーティリティ関数
│   ├── constants.py              # 定数定義
│   ├── gpio_config.py            # GPIO設定（Raspberry Pi用）
│   └── lcd_i2c.py                # LCD制御（Raspberry Pi用）
│
├── 設定・ユーティリティ
│   ├── config.py                 # 設定GUI
│   ├── memory_monitor.py         # メモリモニタリング
│   └── client_config.json        # 設定ファイル
│
└── ドキュメント
    └── docs/                     # 各種ドキュメント
```

詳細は [コード構造ガイド](CODE_STRUCTURE_GUIDE.md) を参照してください。

---

## 📝 コーディング規約

### 1. **命名規則**

#### 変数名
- **スネークケース**を使用: `server_url`, `terminal_id`
- 定数は**大文字のスネークケース**: `DEFAULT_SERVER_URL`, `MAX_RETRY_INTERVAL`

#### 関数名
- **スネークケース**を使用: `get_mac_address()`, `send_attendance_to_server()`
- 動詞で始める: `check_`, `send_`, `load_`, `save_`

#### クラス名
- **パスカルケース**を使用: `UnifiedClient`, `GPIO_Control`, `LocalDatabase`

### 2. **型ヒント**

すべての関数に型ヒントを付けます：

```python
def send_attendance_to_server(
    idm: str,
    timestamp: str,
    terminal_id: str,
    server_url: Optional[str] = None
) -> tuple[bool, Optional[str]]:
    """サーバーに打刻データを送信"""
    # 実装...
```

### 3. **docstring**

すべての関数とクラスにdocstringを付けます：

```python
def get_mac_address() -> str:
    """
    端末のMACアドレスを取得
    
    Returns:
        str: MACアドレス（例: "AA:BB:CC:DD:EE:FF"）
    """
    # 実装...
```

### 4. **インポート順序**

1. 標準ライブラリ
2. サードパーティライブラリ
3. ローカルモジュール（共通モジュール）
4. ローカルモジュール（その他）

```python
# 標準ライブラリ
import time
import sys
from datetime import datetime

# サードパーティライブラリ
import requests

# ローカルモジュール（共通）
from common_utils import get_mac_address, load_config
from constants import DEFAULT_SERVER_URL
```

---

## 🔢 定数の管理

### 原則

**ハードコーディングは禁止**。すべての値は`constants.py`に定義します。

### 定数の定義場所

| 種類 | 定義場所 | 例 |
|------|---------|-----|
| ネットワーク設定 | `constants.py` | `DEFAULT_SERVER_URL`, `API_HEALTH` |
| タイムアウト設定 | `constants.py` | `TIMEOUT_HEALTH_CHECK` |
| GPIO設定 | `gpio_config.py` | `BUZZER_PIN`, `LED_RED_PIN` |
| メッセージ | `constants.py` | `MESSAGE_TOUCH_CARD` |

### 悪い例

```python
# ❌ 悪い例: ハードコーディング
response = requests.get("http://192.168.1.31:5000/api/health", timeout=3)
time.sleep(600)
```

### 良い例

```python
# ✅ 良い例: 定数を使用
from constants import DEFAULT_SERVER_URL, API_HEALTH, TIMEOUT_HEALTH_CHECK, DEFAULT_RETRY_INTERVAL

response = requests.get(f"{DEFAULT_SERVER_URL}{API_HEALTH}", timeout=TIMEOUT_HEALTH_CHECK)
time.sleep(DEFAULT_RETRY_INTERVAL)
```

---

## ⚠️ エラーハンドリング

### オプション機能の処理

オプション機能（GPIO、LCD）の初期化失敗時は、**例外を発生させず、機能を無効化して続行**します。

```python
# ✅ 良い例
try:
    self.gpio = GPIO_Control()
except Exception as e:
    print(f"[警告] GPIO初期化失敗: {e} - GPIO機能を無効化します")
    self.gpio = None  # プログラムは続行

# ❌ 悪い例
try:
    self.gpio = GPIO_Control()
except Exception as e:
    raise  # プログラムがクラッシュ
```

### エラーメッセージの形式

```
[レベル] メッセージ
```

**レベル**:
- `[情報]` - 通常の情報メッセージ
- `[警告]` - 警告（機能が無効化されたなど）
- `[エラー]` - エラー（処理が失敗したが続行可能）
- `[FATAL]` - 致命的エラー（プログラム終了）

**例**:
```python
print("[警告] GPIO初期化失敗: Permission denied - GPIO機能を無効化します")
print("[エラー] サーバー接続失敗: Connection refused")
print("[情報] カードを検出しました: IDm=01234567")
```

---

## 🧪 テストとデバッグ

### ログ出力

デバッグ情報は適切なレベルで出力します：

```python
# デバッグ情報（開発時のみ）
print(f"[DEBUG] カードID: {card_id}, タイムスタンプ: {timestamp}")

# 通常の情報
print(f"[情報] カードを検出しました: {card_id}")

# エラー情報
print(f"[エラー] サーバー送信失敗: {error_msg}")
```

### エラートレースバック

重要なエラーはトレースバックを出力します：

```python
except Exception as e:
    print(f"[エラー] 予期しないエラー: {e}")
    import traceback
    traceback.print_exc()  # 開発時のみ
```

---

## 🔍 コードレビュー

### チェックリスト

コードレビュー時は以下の項目を確認します：

#### 重複コード
- [ ] 同じ処理が複数ファイルに存在しないか
- [ ] 共通関数として`common_utils.py`に集約できるか

#### ハードコーディング
- [ ] 数値や文字列が直接記述されていないか
- [ ] 定数として`constants.py`に定義できるか

#### エラーハンドリング
- [ ] オプション機能の初期化失敗時にクラッシュしないか
- [ ] エラーメッセージが分かりやすいか

#### 型ヒントとdocstring
- [ ] 関数に型ヒントが付いているか
- [ ] docstringで引数と戻り値が説明されているか

#### 環境分離
- [ ] Windows用とRaspberry Pi用が適切に分離されているか
- [ ] 環境依存のコードが混在していないか

---

## 🎯 ベストプラクティス

### 1. **DRY原則（Don't Repeat Yourself）**

重複するコードは共通モジュールに集約します。

**例**: MACアドレス取得
- ❌ 悪い例: `pi_client.py`と`win_client.py`でそれぞれ実装
- ✅ 良い例: `common_utils.py`に1つだけ実装し、両方からインポート

### 2. **単一責任の原則**

1つの関数は1つの責任のみを持ちます。

**例**:
```python
# ❌ 悪い例: 複数の責任を持つ
def process_card_and_send(card_id):
    # カード処理
    # サーバー送信
    # データベース保存
    # ログ出力
    pass

# ✅ 良い例: 責任を分離
def process_card(card_id):
    # カード処理のみ
    pass

def send_to_server(card_id, timestamp):
    # サーバー送信のみ
    pass
```

### 3. **設定の外部化**

設定値は設定ファイルまたは定数として外部化します。

**例**:
```python
# ❌ 悪い例: コード内に直接記述
server_url = "http://192.168.1.31:5000"

# ✅ 良い例: 設定ファイルから読み込み
config = load_config()
server_url = config.get('server_url', DEFAULT_SERVER_URL)
```

---

## 📚 関連ドキュメント

- [コード構造ガイド](CODE_STRUCTURE_GUIDE.md) - コード構造の詳細
- [Windows用とRaspberry Pi用を分離した理由](WHY_SEPARATE_WINDOWS_AND_RASPBERRY_PI.md)
- [Raspberry Pi版クラッシュ原因の実際の分析](RASPBERRY_PI_CRASH_ANALYSIS.md)
- [セットアップガイド](SETUP_GUIDE.md)

---

## 🎯 まとめ

このプロジェクトでは、以下の原則に従ってコードを書きます：

1. ✅ **DRY原則**: 重複コードを避ける
2. ✅ **定数の集約**: ハードコーディングを避ける
3. ✅ **環境分離**: Windows用とRaspberry Pi用を分離
4. ✅ **安全なエラーハンドリング**: オプション機能の失敗時にクラッシュさせない
5. ✅ **明確なドキュメント**: 型ヒントとdocstringでコードを説明

これらの原則に従うことで、保守性が高く、理解しやすいコードを維持できます。

