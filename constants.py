#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
共通定数定義

このモジュールには、プロジェクト全体で使用される定数が定義されています。
ハードコーディングを避けるため、すべての設定値はここに集約されています。

定数の種類:
    - ネットワーク設定: サーバーURL、APIエンドポイント
    - タイムアウト設定: 各種タイムアウト値
    - リトライ設定: リトライ間隔、最大試行回数
    - カード読み取り設定: 重複チェック時間、ポーリング間隔
    - データベース設定: データベースパス、取得上限
    - メッセージ設定: LCD表示メッセージ
    - GPIO設定: デフォルトピン番号（詳細はgpio_config.pyを参照）

使用例:
    from constants import DEFAULT_SERVER_URL, DEFAULT_RETRY_INTERVAL
    
    server_url = config.get('server_url', DEFAULT_SERVER_URL)
    retry_interval = config.get('retry_interval', DEFAULT_RETRY_INTERVAL)
"""

# ============================================================================
# ネットワーク設定
# ============================================================================
DEFAULT_SERVER_PORT = 5000
DEFAULT_SERVER_IP = "192.168.1.31"
DEFAULT_SERVER_URL = f"http://{DEFAULT_SERVER_IP}:{DEFAULT_SERVER_PORT}"

# API エンドポイント
API_HEALTH = "/api/health"
API_ATTENDANCE = "/api/attendance"
API_SEARCH = "/api/search"
API_STATS = "/api/stats"

# ============================================================================
# タイムアウト設定（秒）
# ============================================================================
TIMEOUT_HEALTH_CHECK = 3      # ヘルスチェックタイムアウト
TIMEOUT_SERVER_REQUEST = 5    # サーバーリクエストタイムアウト
TIMEOUT_CARD_DETECTION = 0.5  # カード検出タイムアウト（nfcpy）

# ============================================================================
# リトライ設定
# ============================================================================
DEFAULT_RETRY_INTERVAL = 600  # デフォルトリトライ間隔（秒）= 10分
MIN_RETRY_INTERVAL = 60        # 最小リトライ間隔（秒）
MAX_RETRY_INTERVAL = 3600      # 最大リトライ間隔（秒）= 1時間
RETRY_CHECK_INTERVAL = 1       # リトライチェック間隔（秒）

# ============================================================================
# カード読み取り設定
# ============================================================================
CARD_DUPLICATE_THRESHOLD = 2.0  # 重複チェック時間（秒）
CARD_DETECTION_SLEEP = 0.05     # カード検出スリープ（秒）
PCSC_POLL_INTERVAL = 0.3        # PC/SCポーリング間隔（秒）

# チャタリング防止設定（同一時刻打刻防止）
ENABLE_SAME_MINUTE_CHECK = True  # 同一分チェックを有効にする
SAME_MINUTE_THRESHOLD = 60       # 同一分と判定する時間（秒）

# ============================================================================
# リーダー検出設定
# ============================================================================
READER_DETECTION_MAX_WAIT = 60      # リーダー検出最大待機時間（秒）
READER_DETECTION_CHECK_INTERVAL = 30  # リーダー検出チェック間隔（秒）
READER_RECONNECT_WAIT = 5          # リーダー再接続待機時間（秒）
MAX_CONSECUTIVE_ERRORS = 10        # 最大連続エラー数

# ============================================================================
# データベース設定
# ============================================================================
DB_PATH_ATTENDANCE = "attendance.db"      # 打刻データベース
DB_PATH_CACHE = "local_cache.db"          # ローカルキャッシュ
DB_PENDING_LIMIT = 50                     # 未送信データ取得上限
DB_SEARCH_LIMIT = 100                     # 検索結果上限

# ============================================================================
# ファイルパス設定
# ============================================================================
CONFIG_FILE = "client_config.json"        # 設定ファイル
CONFIG_FILE_SAMPLE = "client_config_sample.json"  # 設定ファイルサンプル

# ============================================================================
# GPIO設定（Raspberry Pi用）
# ============================================================================
# これらの値はgpio_config.pyからインポートすることを推奨
# ここではデフォルト値のみ定義
GPIO_BUZZER_PIN = 18
GPIO_LED_RED_PIN = 13
GPIO_LED_GREEN_PIN = 19
GPIO_LED_BLUE_PIN = 26

# ============================================================================
# LCD設定（Raspberry Pi用）
# ============================================================================
LCD_I2C_ADDR_DEFAULT = 0x27    # デフォルトI2Cアドレス
LCD_I2C_ADDR_ALTERNATIVE = 0x3F  # 代替I2Cアドレス
LCD_I2C_BUS_DEFAULT = 1         # デフォルトI2Cバス番号

# ============================================================================
# メッセージ設定
# ============================================================================
MESSAGE_TOUCH_CARD = "Touch Card"
MESSAGE_READING = "Reading..."
MESSAGE_SENDING = "Sending..."
MESSAGE_SAVED_LOCAL = "Saved Local"
MESSAGE_SAVE_FAILED = "Save Failed"
MESSAGE_STARTING = "Starting..."
MESSAGE_STOPPED = "Stopped"
MESSAGE_WAIT_READER = "Wait Reader"
MESSAGE_NO_READER = "No Reader"

# ============================================================================
# 無効なカードID（フィルタリング用）
# ============================================================================
INVALID_CARD_IDS = [
    "00000000",
    "FFFFFFFF",
    "0000000000000000"
]

# ============================================================================
# PC/SCコマンド設定
# ============================================================================
# 汎用UID取得コマンド
PCSC_CMD_UID_VARIABLE = [0xFF, 0xCA, 0x00, 0x00, 0x00]  # UID（可変長）
PCSC_CMD_UID_4BYTE = [0xFF, 0xCA, 0x00, 0x00, 0x04]     # 4バイト UID
PCSC_CMD_UID_7BYTE = [0xFF, 0xCA, 0x00, 0x00, 0x07]     # 7バイト UID
PCSC_CMD_UID_10BYTE = [0xFF, 0xCA, 0x00, 0x00, 0x0A]    # 10バイト UID
PCSC_CMD_GET_DATA = [0xFF, 0xCA, 0x01, 0x00, 0x00]      # Get Data
PCSC_CMD_FELICA_IDM = [0xFF, 0xB0, 0x00, 0x00, 0x09, 0x06, 0x00, 0xFF, 0xFF, 0x01, 0x00]  # FeliCa IDm

# PC/SC成功応答コード
PCSC_SUCCESS_SW1 = 0x90
PCSC_SUCCESS_SW2 = 0x00

# ============================================================================
# 環境変数設定
# ============================================================================
ENV_PYTHON_UNBUFFERED = "1"
ENV_PYTHON_IO_ENCODING = "utf-8"
ENV_LANG = "ja_JP.UTF-8"
ENV_LC_ALL = "ja_JP.UTF-8"

# ============================================================================
# その他の設定
# ============================================================================
LCD_UPDATE_INTERVAL = 2        # LCD更新間隔（秒）
LED_BLINK_INTERVAL = 0.5       # LED点滅間隔（秒）
SERVER_CHECK_INTERVAL = 3600   # サーバー接続チェック間隔（秒）= 1時間
PENDING_DATA_MIN_AGE = 600     # 未送信データの最小経過時間（秒）= 10分

# メンテナンス設定
MAINTENANCE_INTERVAL = 1800    # メンテナンス実行間隔（秒）= 30分
HISTORY_CLEANUP_THRESHOLD = 3600  # カード履歴クリーンアップ閾値（秒）= 1時間

# 待機時間設定
LED_DEMO_DELAY = 0.5           # LEDデモ表示間隔（秒）
SERVER_ERROR_FLICKER_INTERVAL = 10  # サーバーエラー時のLEDフリッカ間隔（秒）
ORANGE_LED_DISPLAY_TIME = 0.5  # オレンジLED表示時間（秒）
READER_WAIT_BEFORE_EXIT = 300  # リーダー待機後の終了待機時間（秒）= 5分

# PWM設定
PWM_FREQUENCY = 1000           # PWM周波数（Hz）
PWM_DUTY_CYCLE = 50            # PWMデューティ比（%）

# GUI設定
GUI_UPDATE_INTERVAL = 1000     # GUI更新間隔（ミリ秒）
GUI_WINDOW_WIDTH = 800         # GUIウィンドウ幅（ピクセル）
GUI_WINDOW_HEIGHT = 600        # GUIウィンドウ高さ（ピクセル）

# Sony RC-S380設定
SONY_RCS380_VID_PID = 'usb:054c:06c1'  # Sony RC-S380のベンダーID:プロダクトID

