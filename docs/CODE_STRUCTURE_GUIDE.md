# コード構造ガイド

このドキュメントでは、プロジェクトのコード構造と設計思想について説明します。

---

## 📁 プロジェクト構造

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

---

## 🎯 設計原則

### 1. **DRY原則（Don't Repeat Yourself）**

重複するコードは共通モジュールに集約します。

**例**: `get_mac_address()`関数
- ❌ 悪い例: `pi_client.py`と`win_client.py`でそれぞれ実装
- ✅ 良い例: `common_utils.py`に1つだけ実装し、両方からインポート

### 2. **定数の集約**

ハードコーディングされた値は`constants.py`に集約します。

**例**: サーバーURL
- ❌ 悪い例: `http://192.168.1.31:5000`を複数ファイルに直接記述
- ✅ 良い例: `constants.py`の`DEFAULT_SERVER_URL`を使用

### 3. **環境分離**

Windows用とRaspberry Pi用は完全に分離します。

**理由**: 
- 環境依存ライブラリの競合を避ける
- エラーハンドリングを簡潔にする
- 保守性を向上させる

詳細は [Windows用とRaspberry Pi用を分離した理由](WHY_SEPARATE_WINDOWS_AND_RASPBERRY_PI.md) を参照。

### 4. **オプション機能の安全な処理**

オプション機能（GPIO、LCD）の初期化失敗時は、プログラムをクラッシュさせずに機能を無効化します。

**例**: GPIO初期化
```python
try:
    self.gpio = GPIO_Control()
except Exception as e:
    print(f"[警告] GPIO初期化失敗: {e} - GPIO機能を無効化します")
    self.gpio = None  # プログラムは続行
```

---

## 📦 モジュールの役割

### `common_utils.py` - 共通ユーティリティ関数

**役割**: 複数のファイルで使用される共通関数を集約

**主要な関数**:
- `get_mac_address()` - MACアドレス取得
- `load_config()` - 設定ファイル読み込み
- `save_config()` - 設定ファイル保存
- `check_server_connection()` - サーバー接続チェック
- `send_attendance_to_server()` - サーバーへのデータ送信
- `get_pcsc_commands()` - PC/SCコマンド取得
- `is_valid_card_id()` - カードID検証
- `is_duplicate_attendance()` - 重複打刻チェック
- `setup_windows_encoding()` - Windows用エンコーディング設定

**使用例**:
```python
from common_utils import get_mac_address, load_config

terminal_id = get_mac_address()
config = load_config()
```

---

### `constants.py` - 定数定義

**役割**: ハードコーディングされた値を定数として定義

**主要な定数**:
- ネットワーク設定: `DEFAULT_SERVER_URL`, `API_HEALTH`, `API_ATTENDANCE`
- タイムアウト設定: `TIMEOUT_HEALTH_CHECK`, `TIMEOUT_SERVER_REQUEST`
- リトライ設定: `DEFAULT_RETRY_INTERVAL`, `MIN_RETRY_INTERVAL`
- カード読み取り設定: `CARD_DUPLICATE_THRESHOLD`, `CARD_DETECTION_SLEEP`
- データベース設定: `DB_PATH_ATTENDANCE`, `DB_PATH_CACHE`
- メッセージ設定: `MESSAGE_TOUCH_CARD`, `MESSAGE_READING`, etc.

**使用例**:
```python
from constants import DEFAULT_SERVER_URL, DEFAULT_RETRY_INTERVAL

server_url = config.get('server_url', DEFAULT_SERVER_URL)
retry_interval = config.get('retry_interval', DEFAULT_RETRY_INTERVAL)
```

---

### `gpio_config.py` - GPIO設定（Raspberry Pi用）

**役割**: GPIO関連の設定を集約

**主要な設定**:
- GPIOピン番号: `BUZZER_PIN`, `LED_RED_PIN`, `LED_GREEN_PIN`, `LED_BLUE_PIN`
- ブザーパターン: `BUZZER_PATTERNS`
- LED色設定: `LED_COLORS`
- I2C LCD設定: `LCD_I2C_ADDR`, `LCD_I2C_BUS`

**使用例**:
```python
from gpio_config import BUZZER_PIN, LED_RED_PIN, BUZZER_PATTERNS

GPIO.setup(BUZZER_PIN, GPIO.OUT)
GPIO.setup(LED_RED_PIN, GPIO.OUT)
```

---

## 🔄 データフロー

### カード読み取りからサーバー送信まで

```
1. カード検出
   ↓
2. カードID取得（nfcpy または PC/SC）
   ↓
3. 重複チェック（is_duplicate_attendance()）
   ↓
4. サーバー送信試行（send_attendance_to_server()）
   ↓
5. 成功 → データベースに保存（sent_to_server=1）
   失敗 → データベースに保存（sent_to_server=0）
   ↓
6. バックグラウンドでリトライ（retry_pending_records()）
```

---

## 🛠️ コードの書き方

### 関数の定義

**良い例**:
```python
def send_attendance_to_server(
    idm: str,
    timestamp: str,
    terminal_id: str,
    server_url: Optional[str] = None
) -> tuple[bool, Optional[str]]:
    """
    サーバーに打刻データを送信
    
    Args:
        idm: カードID
        timestamp: タイムスタンプ（ISO8601形式）
        terminal_id: 端末ID
        server_url: サーバーURL（Noneの場合は設定ファイルから読み込み）
    
    Returns:
        tuple: (成功したかどうか, エラーメッセージまたはNone)
    """
    # 実装...
```

**ポイント**:
- 型ヒントを付ける
- docstringで引数と戻り値を説明
- デフォルト値を使用して柔軟性を持たせる

---

### エラーハンドリング

**良い例**:
```python
try:
    self.gpio = GPIO_Control()
except PermissionError as e:
    print(f"[警告] GPIO権限エラー: {e} - GPIO機能を無効化します")
    self.gpio = None
except Exception as e:
    print(f"[警告] GPIO初期化失敗: {e} - GPIO機能を無効化します")
    self.gpio = None
```

**ポイント**:
- オプション機能は例外を発生させず、無効化して続行
- エラーメッセージは分かりやすく
- ログレベルを適切に設定（[警告]、[エラー]など）

---

### 定数の使用

**悪い例**:
```python
response = requests.get("http://192.168.1.31:5000/api/health", timeout=3)
```

**良い例**:
```python
from constants import DEFAULT_SERVER_URL, API_HEALTH, TIMEOUT_HEALTH_CHECK

response = requests.get(f"{DEFAULT_SERVER_URL}{API_HEALTH}", timeout=TIMEOUT_HEALTH_CHECK)
```

**ポイント**:
- ハードコーディングを避ける
- 定数は`constants.py`に集約
- 設定ファイルから読み込む値は`load_config()`を使用

---

## 📝 コメントの書き方

### セクション分け

```python
# ============================================================================
# サーバー通信
# ============================================================================

def check_server_connection(server_url: Optional[str] = None) -> bool:
    """サーバー接続をチェック"""
    # 実装...
```

### 処理の意図を説明

```python
# 重複チェック: 同じカードIDで同じ分（YYYY-MM-DD HH:MM）の打刻を防ぐ
is_dup, dup_msg = is_duplicate_attendance(card_id, timestamp, self.attendance_history)
if is_dup:
    print(f"[重複打刻] {dup_msg} - スキップ")
    return False
```

---

## 🔍 コードレビューのチェックリスト

### 重複コード
- [ ] 同じ処理が複数ファイルに存在しないか
- [ ] 共通関数として`common_utils.py`に集約できるか

### ハードコーディング
- [ ] 数値や文字列が直接記述されていないか
- [ ] 定数として`constants.py`に定義できるか

### エラーハンドリング
- [ ] オプション機能の初期化失敗時にクラッシュしないか
- [ ] エラーメッセージが分かりやすいか

### 型ヒントとdocstring
- [ ] 関数に型ヒントが付いているか
- [ ] docstringで引数と戻り値が説明されているか

### 環境分離
- [ ] Windows用とRaspberry Pi用が適切に分離されているか
- [ ] 環境依存のコードが混在していないか

---

## 📚 関連ドキュメント

- [Windows用とRaspberry Pi用を分離した理由](WHY_SEPARATE_WINDOWS_AND_RASPBERRY_PI.md)
- [Raspberry Pi版クラッシュ原因の実際の分析](RASPBERRY_PI_CRASH_ANALYSIS.md)
- [セットアップガイド](SETUP_GUIDE.md)

---

## 🎯 まとめ

このプロジェクトでは、以下の原則に従ってコードを書いています：

1. ✅ **DRY原則**: 重複コードを避ける
2. ✅ **定数の集約**: ハードコーディングを避ける
3. ✅ **環境分離**: Windows用とRaspberry Pi用を分離
4. ✅ **安全なエラーハンドリング**: オプション機能の失敗時にクラッシュさせない
5. ✅ **明確なドキュメント**: 型ヒントとdocstringでコードを説明

これらの原則に従うことで、保守性が高く、理解しやすいコードを維持できます。

