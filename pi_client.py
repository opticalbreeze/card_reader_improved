#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi版クライアント（統合版）

このモジュールは、Raspberry Pi環境で動作するICカード打刻クライアントです。

主な機能:
    - LCD I2C 1602対応: I2C接続のLCDディスプレイに状態を表示
    - GPIO制御: RGB LEDと圧電ブザーで視覚・聴覚フィードバック
    - マルチリーダー対応: nfcpyとPC/SCの両方に対応
    - 端末ID自動取得: MACアドレスを端末IDとして使用
    - オフライン優先: ローカルDBに保存後、サーバーが利用可能な時に自動送信
    - メモリモニタリング: 長時間実行時のメモリ使用量を監視（オプション）

使用方法:
    python3 pi_client.py

依存関係:
    - common_utils.py: 共通ユーティリティ関数
    - constants.py: 定数定義
    - gpio_config.py: GPIO設定（オプション）
    - lcd_i2c.py: LCD制御（オプション）

注意事項:
    - GPIO機能を使用するには、ユーザーをgpioグループに追加する必要があります
    - LCD機能を使用するには、I2Cが有効になっている必要があります
    - PC/SC機能を使用するには、pcscdサービスが起動している必要があります
"""

import time
import sys
import sqlite3
from datetime import datetime
from pathlib import Path
import threading

# メモリモニタリング
try:
    from memory_monitor import MemoryMonitor
    MEMORY_MONITOR_AVAILABLE = True
except ImportError:
    MEMORY_MONITOR_AVAILABLE = False
    print("[情報] memory_monitor.py未検出 - メモリモニタリング無効")

# 共通モジュールをインポート
from common_utils import (
    get_mac_address,
    load_config,
    check_server_connection,
    send_attendance_to_server,
    get_pcsc_commands,
    is_valid_card_id
)
from constants import (
    DEFAULT_RETRY_INTERVAL,
    CARD_DUPLICATE_THRESHOLD,
    CARD_DETECTION_SLEEP,
    PCSC_POLL_INTERVAL,
    READER_DETECTION_MAX_WAIT,
    READER_DETECTION_CHECK_INTERVAL,
    DB_PATH_ATTENDANCE,
    DB_PENDING_LIMIT,
    TIMEOUT_CARD_DETECTION,
    MESSAGE_TOUCH_CARD,
    MESSAGE_READING,
    MESSAGE_SENDING,
    MESSAGE_SAVED_LOCAL,
    MESSAGE_SAVE_FAILED,
    MESSAGE_STARTING,
    MESSAGE_STOPPED,
    MESSAGE_WAIT_READER,
    MESSAGE_NO_READER,
    RETRY_CHECK_INTERVAL
)

# HTTP通信（サーバー送信用）
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("[警告] requests未インストール - サーバー送信機能は無効です")

# ============================================================================
# ライブラリ依存関係の確認
# ============================================================================

# LCD制御
try:
    from lcd_i2c import LCD_I2C
    LCD_AVAILABLE = True
except ImportError:
    try:
        from lcd_i2c import LCD_I2C
        LCD_AVAILABLE = True
    except ImportError:
        LCD_AVAILABLE = False
        print("[警告] LCD機能無効 - lcd_i2c.pyが見つかりません")

# GPIO制御
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("[警告] GPIO機能無効 - Raspberry Pi以外の環境")

# nfcpy（Sony RC-S380など）
try:
    import nfc
    NFCPY_AVAILABLE = True
except ImportError:
    NFCPY_AVAILABLE = False
    print("[情報] nfcpy未インストール - PC/SCのみで動作")

# pyscard（PC/SC対応リーダー）
try:
    from smartcard.System import readers as pcsc_readers
    from smartcard.Exceptions import CardConnectionException, NoCardException
    PYSCARD_AVAILABLE = True
except ImportError:
    PYSCARD_AVAILABLE = False
    print("[情報] pyscard未インストール - nfcpyのみで動作")

# GPIO設定をインポート
try:
    from gpio_config import (
        BUZZER_PIN,
        LED_RED_PIN,
        LED_GREEN_PIN,
        LED_BLUE_PIN,
        BUZZER_PATTERNS,
        LED_COLORS
    )
except ImportError:
    # デフォルト設定（gpio_config.pyが見つからない場合）
    from constants import (
        GPIO_BUZZER_PIN,
        GPIO_LED_RED_PIN,
        GPIO_LED_GREEN_PIN,
        GPIO_LED_BLUE_PIN
    )
    BUZZER_PIN = GPIO_BUZZER_PIN
    LED_RED_PIN = GPIO_LED_RED_PIN
    LED_GREEN_PIN = GPIO_LED_GREEN_PIN
    LED_BLUE_PIN = GPIO_LED_BLUE_PIN
    # デフォルトのブザーパターンとLED色
    BUZZER_PATTERNS = {
        "startup": [(0.2, 1000), (0.1, 1000), (0.2, 1000)],
        "connect": [(0.1, 1500), (0.1, 1500), (0.1, 1500)],
        "card_read": [(0.05, 2000)],
        "success": [(0.1, 2500), (0.05, 2500), (0.1, 2500)],
        "failure": [(0.3, 800), (0.1, 800), (0.3, 800)]
    }
    LED_COLORS = {
        "off": (0, 0, 0),
        "red": (100, 0, 0),
        "green": (0, 100, 0),
        "blue": (0, 0, 100),
        "orange": (100, 50, 0)
    }


# get_mac_address() は common_utils からインポート済み


# ============================================================================
# GPIO制御クラス
# ============================================================================

class GPIO_Control:
    """
    GPIO制御（LED + ブザー）
    Raspberry Pi上でLEDとブザーを制御
    """
    
    def __init__(self):
        """GPIO初期化"""
        self.available = GPIO_AVAILABLE
        self.blink_running = False
        
        if not self.available:
            print("[GPIO] RPi.GPIOがインポートできません - Raspberry Pi以外の環境か、RPi.GPIOがインストールされていません")
            return
        
        try:
            # GPIO設定
            print(f"[GPIO] 初期化開始 - ブザー:{BUZZER_PIN} 赤:{LED_RED_PIN} 緑:{LED_GREEN_PIN} 青:{LED_BLUE_PIN}")
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # ブザーピン設定
            GPIO.setup(BUZZER_PIN, GPIO.OUT)
            print(f"[GPIO] ブザーピン {BUZZER_PIN} 設定完了")
            
            # LEDピン設定
            GPIO.setup([LED_RED_PIN, LED_GREEN_PIN, LED_BLUE_PIN], GPIO.OUT)
            print(f"[GPIO] LEDピン設定完了 - 赤:{LED_RED_PIN} 緑:{LED_GREEN_PIN} 青:{LED_BLUE_PIN}")
            
            # PWM設定（LED用）
            self.pwms = [
                from constants import PWM_FREQUENCY
                GPIO.PWM(LED_RED_PIN, PWM_FREQUENCY),
                GPIO.PWM(LED_GREEN_PIN, PWM_FREQUENCY),
                GPIO.PWM(LED_BLUE_PIN, PWM_FREQUENCY)
            ]
            for i, pwm in enumerate(self.pwms):
                pwm.start(0)
                print(f"[PWM] LED {['赤','緑','青'][i]} PWM初期化完了")
            print("[GPIO] 初期化成功")
        except PermissionError as e:
            print(f"[エラー] GPIO権限エラー: {e}")
            print("[エラー] GPIOを使用するには、以下のいずれかが必要です:")
            print("  1. sudoで実行: sudo python3 client_card_reader_unified_improved.py")
            print("  2. gpioグループに追加: sudo usermod -a -G gpio $USER (再ログインが必要)")
            import traceback
            traceback.print_exc()
            self.available = False
            self.pwms = []
        except RuntimeError as e:
            print(f"[エラー] GPIO実行時エラー: {e}")
            print("[エラー] これは通常、GPIOピンが既に使用されているか、ハードウェアの問題です")
            import traceback
            traceback.print_exc()
            self.available = False
            self.pwms = []
        except Exception as e:
            print(f"[エラー] GPIO初期化失敗: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            self.available = False
            self.pwms = []
    
    def sound(self, pattern):
        """
        ブザーを鳴らす
        
        Args:
            pattern (str): 音パターン名（"startup", "card_read", "success", "failure"など）
        """
        if not self.available:
            print(f"[警告] GPIOが利用不可のため、ブザーをスキップ: {pattern}")
            return
        
        for duration, freq in BUZZER_PATTERNS.get(pattern, [(0.1, 1000)]):
            try:
                # PWMオブジェクトを作成
                from constants import PWM_DUTY_CYCLE
                pwm = GPIO.PWM(BUZZER_PIN, freq)
                pwm.start(PWM_DUTY_CYCLE)  # デューティ比
                time.sleep(duration)
                pwm.stop()
                # PWMオブジェクトを削除してリソースを解放
                del pwm
                from constants import CARD_DETECTION_SLEEP
                time.sleep(CARD_DETECTION_SLEEP)
            except RuntimeError as e:
                if "already exists" in str(e):
                    # 既存のPWMをクリーンアップして再試行
                    try:
                        GPIO.setup(BUZZER_PIN, GPIO.OUT)
                        pwm = GPIO.PWM(BUZZER_PIN, freq)
                        from constants import PWM_DUTY_CYCLE
                        pwm.start(PWM_DUTY_CYCLE)
                        time.sleep(duration)
                        pwm.stop()
                        del pwm
                        from constants import CARD_DETECTION_SLEEP
                time.sleep(CARD_DETECTION_SLEEP)
                    except:
                        pass
            except Exception as e:
                print(f"[エラー] ブザー制御失敗 ({pattern}, {freq}Hz): {e}")
    
    def led(self, color):
        """
        LEDの色を設定
        
        Args:
            color (str): 色名（"off", "red", "green", "blue", "orange"など）
        """
        if not self.available:
            print(f"[警告] GPIOが利用不可のため、LED制御をスキップ: {color}")
            return
        
        self.stop_blink()
        r, g, b = LED_COLORS.get(color, (0, 0, 0))
        try:
            if not hasattr(self, 'pwms') or not self.pwms:
                print(f"[エラー] PWMが初期化されていません")
                return
            
            self.pwms[0].ChangeDutyCycle(r)
            self.pwms[1].ChangeDutyCycle(g)
            self.pwms[2].ChangeDutyCycle(b)
            print(f"[LED] {color} - R={r} G={g} B={b}")
        except Exception as e:
            print(f"[エラー] LED制御失敗 ({color}): {e}")
            import traceback
            traceback.print_exc()
    
    def blink_orange(self):
        """
        オレンジ色で点滅（サーバー接続エラー時など）
        バックグラウンドスレッドで実行
        """
        if not self.available:
            return
        
        self.stop_blink()
        self.blink_running = True
        
        def worker():
            from constants import LED_BLINK_INTERVAL
            while self.blink_running:
                self.led("orange")
                time.sleep(LED_BLINK_INTERVAL)
                self.led("off")
                time.sleep(LED_BLINK_INTERVAL)
        
        threading.Thread(target=worker, daemon=True).start()
    
    def stop_blink(self):
        """点滅を停止"""
        self.blink_running = False
        time.sleep(0.1)
    
    def cleanup(self):
        """GPIOのクリーンアップ（終了時に呼び出し）"""
        if not self.available:
            return
        
        try:
            self.stop_blink()
            for pwm in self.pwms:
                pwm.stop()
            GPIO.cleanup()
        except Exception:
            pass


# ============================================================================
# ローカルキャッシュクラス
# ============================================================================

class LocalDatabase:
    """
    ローカルデータベース管理（スタンドアロン版）
    SQLiteを使用して打刻データを直接保存
    サーバー不要で動作可能
    """
    
    def __init__(self, db_path=None):
        """
        Args:
            db_path (str): データベースファイルのパス（Noneの場合はデフォルト値を使用）
        """
        if db_path is None:
            db_path = DB_PATH_ATTENDANCE
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """データベースの初期化（テーブル作成）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 打刻データテーブル（サーバーと同じ構造 + 送信済みフラグ）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                idm TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                terminal_id TEXT NOT NULL,
                received_at TEXT NOT NULL,
                sent_to_server INTEGER DEFAULT 0,
                retry_count INTEGER DEFAULT 0
            )
        """)
        
        # 既存テーブルのマイグレーション（カラム追加）
        try:
            # sent_to_serverカラムが存在するか確認
            cursor.execute("PRAGMA table_info(attendance)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'sent_to_server' not in columns:
                print("[データベース] sent_to_serverカラムを追加中...")
                cursor.execute("ALTER TABLE attendance ADD COLUMN sent_to_server INTEGER DEFAULT 0")
            
            if 'retry_count' not in columns:
                print("[データベース] retry_countカラムを追加中...")
                cursor.execute("ALTER TABLE attendance ADD COLUMN retry_count INTEGER DEFAULT 0")
            
            conn.commit()
        except Exception as e:
            print(f"[警告] データベースマイグレーションエラー: {e}")
            conn.rollback()
        
        # インデックスの作成（検索パフォーマンス向上）
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_idm ON attendance(idm)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON attendance(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_terminal_id ON attendance(terminal_id)
        """)
        
        conn.commit()
        conn.close()
        print(f"[データベース] 初期化完了: {self.db_path}")
    
    def save_attendance(self, idm, timestamp, terminal_id, sent_to_server=0):
        """
        打刻データをデータベースに保存
        
        Args:
            idm (str): カードID
            timestamp (str): タイムスタンプ（ISO8601形式）
            terminal_id (str): 端末ID
            sent_to_server (int): サーバー送信済みフラグ（0=未送信, 1=送信済み）
        
        Returns:
            int: 保存されたレコードID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO attendance (idm, timestamp, terminal_id, received_at, sent_to_server, retry_count)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (idm, timestamp, terminal_id, datetime.now().isoformat(), sent_to_server, 0))
        conn.commit()
        record_id = cursor.lastrowid
        conn.close()
        print(f"[保存完了] ID:{record_id} | IDm:{idm} | 端末:{terminal_id} | 時刻:{timestamp}")
        return record_id
    
    def get_pending_records(self, limit=None):
        """
        未送信のレコードを取得
        
        Args:
            limit (int): 取得件数の上限（Noneの場合はデフォルト値）
        
        Returns:
            list: (id, idm, timestamp, terminal_id, retry_count) のタプルのリスト
        """
        if limit is None:
            limit = DB_PENDING_LIMIT
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # カラムの存在確認
        try:
            cursor.execute("PRAGMA table_info(attendance)")
            columns = [row[1] for row in cursor.fetchall()]
            
            # カラムが存在しない場合はマイグレーション
            if 'sent_to_server' not in columns or 'retry_count' not in columns:
                print("[データベース] カラムが不足しています。マイグレーションを実行します...")
                if 'sent_to_server' not in columns:
                    cursor.execute("ALTER TABLE attendance ADD COLUMN sent_to_server INTEGER DEFAULT 0")
                if 'retry_count' not in columns:
                    cursor.execute("ALTER TABLE attendance ADD COLUMN retry_count INTEGER DEFAULT 0")
                conn.commit()
                # 既存レコードを未送信としてマーク
                cursor.execute("UPDATE attendance SET sent_to_server = 0 WHERE sent_to_server IS NULL")
                conn.commit()
        except Exception as e:
            print(f"[警告] マイグレーションエラー: {e}")
        
        try:
            cursor.execute("""
                SELECT id, idm, timestamp, terminal_id, retry_count
                FROM attendance
                WHERE sent_to_server = 0
                ORDER BY timestamp ASC
                LIMIT ?
            """, (limit,))
            records = cursor.fetchall()
        except sqlite3.OperationalError as e:
            print(f"[エラー] クエリ実行エラー: {e}")
            # フォールバック: カラムなしで取得
            cursor.execute("""
                SELECT id, idm, timestamp, terminal_id, 0
                FROM attendance
                ORDER BY timestamp ASC
                LIMIT ?
            """, (limit,))
            records = cursor.fetchall()
        
        conn.close()
        return records
    
    def mark_as_sent(self, record_id):
        """
        レコードを送信済みとしてマーク
        
        Args:
            record_id (int): レコードID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE attendance
            SET sent_to_server = 1
            WHERE id = ?
        """, (record_id,))
        conn.commit()
        conn.close()
    
    def increment_retry_count(self, record_id):
        """
        リトライ回数を増やす
        
        Args:
            record_id (int): レコードID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE attendance
            SET retry_count = retry_count + 1
            WHERE id = ?
        """, (record_id,))
        conn.commit()
        conn.close()
    
    def get_all_records(self, limit=100):
        """
        すべての打刻レコードを取得
        
        Args:
            limit (int): 取得件数の上限
        
        Returns:
            list: (id, idm, timestamp, terminal_id, received_at) のタプルのリスト
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, idm, timestamp, terminal_id, received_at
            FROM attendance
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        records = cursor.fetchall()
        conn.close()
        return records
    
    def search_records(self, idm=None, start_date=None, end_date=None, terminal_id=None, limit=100):
        """
        打刻データを検索
        
        Args:
            idm (str): カードID（部分一致）
            start_date (str): 開始日時
            end_date (str): 終了日時
            terminal_id (str): 端末ID（部分一致）
            limit (int): 最大件数
        
        Returns:
            list: 検索結果のリスト
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT id, idm, timestamp, terminal_id, received_at FROM attendance WHERE 1=1"
        params = []
        
        if idm:
            query += " AND idm LIKE ?"
            params.append(f"%{idm}%")
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date + " 23:59:59")
        
        if terminal_id:
            query += " AND terminal_id LIKE ?"
            params.append(f"%{terminal_id}%")
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        records = cursor.fetchall()
        conn.close()
        return records
    
    def get_stats(self):
        """
        統計情報を取得
        
        Returns:
            dict: 統計情報
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM attendance")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT idm) FROM attendance")
        unique_cards = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT terminal_id) FROM attendance")
        unique_terminals = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_records': total,
            'unique_cards': unique_cards,
            'unique_terminals': unique_terminals
        }


# ============================================================================
# 統合版クライアントクラス
# ============================================================================

class UnifiedClient:
    """
    ラズパイ統合版クライアント（ハイブリッド版）
    LCD + GPIO + nfcpy/PC/SC全てに対応
    オフライン優先：ローカルDBに保存 → サーバーが利用可能な時に自動送信
    """
    
    def __init__(self, server_url=None, retry_interval=None, lcd_settings=None):
        """
        ハイブリッド版：サーバーURLはオプション
        
        Args:
            server_url (str): サーバーURL（Noneの場合は設定ファイルから読み込み）
            retry_interval (int): リトライ間隔（秒、Noneの場合はデフォルト値）
            lcd_settings (dict): LCD設定（i2c_addr, i2c_bus, backlight）
        """
        # 設定ファイルから読み込み
        config = load_config()
        self.server_url = server_url or config.get('server_url')
        self.retry_interval = retry_interval or config.get('retry_interval', DEFAULT_RETRY_INTERVAL)
        self.lcd_settings = lcd_settings or {}
        self._init_components()
        self._led_startup_demo()  # 起動時LEDデモ
        # LEDデモ後、確実に通常状態（緑）に戻す
        self._init_server()
        self._init_lcd()
        self._start_background_threads()
    
    def _init_components(self):
        """基本コンポーネントの初期化"""
        try:
            self.terminal_id = get_mac_address()  # MACアドレスを端末IDとして使用
            self.database = LocalDatabase()  # ローカルデータベース
            self.gpio = GPIO_Control()
            # LCD設定を読み込んで初期化
            lcd_addr = self.lcd_settings.get('i2c_addr', 0x27)
            lcd_bus = self.lcd_settings.get('i2c_bus', 1)
            lcd_backlight = self.lcd_settings.get('backlight', True)
            self.lcd = LCD_I2C(addr=lcd_addr, bus=lcd_bus, backlight=lcd_backlight) if LCD_AVAILABLE else None
            self.count = 0
            self.history = {}  # {card_id: last_seen_time}
            self.lock = threading.Lock()
            self.running = True
            self.server_available = False
            self.server_check_running = False
            
            self.current_message = MESSAGE_TOUCH_CARD
            
            # 起動音
            self.gpio.sound("startup")
        except Exception as e:
            print(f"[エラー] コンポーネント初期化失敗: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _init_server(self):
        """サーバー接続チェックとエラー処理"""
        if not self.server_url:
            self.gpio.led("green")
            return
        
        self.check_server_connection()
        if not self.server_available:
            # サーバー接続失敗：LEDエラー表示+ブザー
            from constants import LED_DEMO_DELAY
            self.gpio.led("red")
            self.gpio.sound("failure")
            time.sleep(LED_DEMO_DELAY * 6)  # 3秒（0.5秒の6倍）
            # 10秒ごとの赤LEDフリッカ開始
            self.server_check_running = True
            threading.Thread(target=self.server_error_flicker, daemon=True).start()
        else:
            # サーバー接続成功：未送信データを送信
            self._send_pending_on_startup()
            self.gpio.led("green")
    
    def _led_startup_demo(self):
        """起動時LEDデモ（赤→青→緑を順番に点灯）"""
        from constants import LED_DEMO_DELAY
        self.gpio.led("red")
        time.sleep(LED_DEMO_DELAY)
        self.gpio.led("blue")
        time.sleep(LED_DEMO_DELAY)
        self.gpio.led("green")
        time.sleep(LED_DEMO_DELAY)
        # デモ後は確実に消灯（_init_server()で緑に設定される）
        self.gpio.led("off")
        time.sleep(0.1)  # 確実に消灯するための短い待機
    
    def _init_lcd(self):
        """LCD初期化と表示"""
        if not self.lcd:
            return
        
        from constants import LCD_UPDATE_INTERVAL
        self.lcd.show_with_time(MESSAGE_STARTING)
        time.sleep(LCD_UPDATE_INTERVAL)
        self.lcd.show_with_time(MESSAGE_TOUCH_CARD)
    
    def _start_background_threads(self):
        """バックグラウンドスレッド開始"""
        # LCD時刻更新スレッド
        threading.Thread(target=self.update_lcd_time, daemon=True).start()
        
        # サーバー送信リトライスレッド
        if self.server_url and REQUESTS_AVAILABLE:
            threading.Thread(target=self.retry_pending_records, daemon=True).start()
        
        # メンテナンススレッド（定期的なリソースクリーンアップ）
        threading.Thread(target=self._maintenance_worker, daemon=True).start()
    
    # ========================================================================
    # メンテナンス（定期的なリソースクリーンアップ）
    # ========================================================================
    
    def _maintenance_worker(self):
        """
        定期的なメンテナンス処理
        - LCDのリセット（文字化け対策）
        - 古いカード履歴のクリーンアップ
        - ガベージコレクション
        30分ごとに実行
        """
        import gc
        from constants import SERVER_CHECK_INTERVAL
        maintenance_interval = SERVER_CHECK_INTERVAL * 0.5  # サーバーチェック間隔の半分（30分）
        
        while self.running:
            time.sleep(maintenance_interval)
            
            if not self.running:
                break
            
            try:
                print("[メンテナンス] 定期メンテナンス実行中...")
                
                # 1. LCDリセット（文字化け対策）
                if self.lcd and self.lcd.available:
                    try:
                        self.lcd.reset()
                        print("[メンテナンス] LCD をリセットしました")
                    except Exception as e:
                        print(f"[メンテナンス] LCD リセット失敗: {e}")
                
                # 2. 古いカード履歴をクリーンアップ（1時間以上前のエントリを削除）
                current_time = time.time()
                old_entries = []
                with self.lock:
                    for card_id, last_seen in list(self.history.items()):
                        from constants import MAX_RETRY_INTERVAL
                        if current_time - last_seen > MAX_RETRY_INTERVAL:  # 1時間
                            old_entries.append(card_id)
                    
                    for card_id in old_entries:
                        del self.history[card_id]
                
                if old_entries:
                    print(f"[メンテナンス] 古いカード履歴を{len(old_entries)}件削除しました")
                
                # 3. ガベージコレクション
                collected = gc.collect()
                print(f"[メンテナンス] GC実行: {collected}個のオブジェクトを回収")
                
                print("[メンテナンス] メンテナンス完了")
            
            except Exception as e:
                print(f"[メンテナンス] エラー: {e}")
    
    # ========================================================================
    # サーバー通信
    # ========================================================================
    
    def _send_pending_on_startup(self):
        """
        起動時に未送信データを送信
        サーバー接続が確認できた場合のみ実行
        """
        if not self.server_url or not REQUESTS_AVAILABLE or not self.server_available:
            return
        
        records = self.database.get_pending_records()
        if not records:
            print("[起動時送信] 未送信データはありません")
            return
        
        print(f"\n[起動時送信] {len(records)}件の未送信データを送信します")
        
        success_count = 0
        fail_count = 0
        
        for record in records:
            record_id, idm, timestamp, terminal_id, retry_count = record
            
            if self.send_to_server(idm, timestamp):
                self.database.mark_as_sent(record_id)
                success_count += 1
                print(f"[起動時送信成功] IDm: {idm}")
            else:
                self.database.increment_retry_count(record_id)
                fail_count += 1
                print(f"[起動時送信失敗] IDm: {idm} (試行回数: {retry_count + 1})")
        
        print(f"[起動時送信完了] 成功: {success_count}件, 失敗: {fail_count}件")
    
    def check_server_connection(self):
        """
        サーバー接続をチェック
        
        Returns:
            bool: サーバーが利用可能かどうか
        """
        if not self.server_url or not REQUESTS_AVAILABLE:
            self.server_available = False
            return False
        
        self.server_available = check_server_connection(self.server_url)
        return self.server_available
    
    def send_to_server(self, idm, timestamp):
        """
        サーバーにデータを送信
        
        Args:
            idm (str): カードID
            timestamp (str): タイムスタンプ（ISO8601形式）
        
        Returns:
            bool: 送信成功したかどうか（重複の場合もTrueを返す）
        """
        if not self.server_url or not REQUESTS_AVAILABLE:
            return False
        
        success, error_msg = send_attendance_to_server(
            idm, timestamp, self.terminal_id, self.server_url
        )
        
        if success:
            self.server_available = True
            if error_msg:
                print(f"[送信済み] 重複データのためスキップ")
            else:
                print(f"[送信成功] サーバーに記録")
            return True
        else:
            print(f"[送信失敗] {error_msg}")
            self.server_available = False
            return False
    
    def server_error_flicker(self):
        """
        サーバーエラー時の赤LEDフリッカ（10秒ごと）
        """
        while self.running and self.server_check_running:
            if not self.server_available:
                # サーバー接続を再チェック
                if self.check_server_connection():
                    self.server_check_running = False
                    self.gpio.led("green")
                    return
                # 赤LEDフリッカ
                from constants import LED_DEMO_DELAY, SERVER_ERROR_FLICKER_INTERVAL
                self.gpio.led("red")
                time.sleep(LED_DEMO_DELAY)
                self.gpio.led("off")
            time.sleep(SERVER_ERROR_FLICKER_INTERVAL)
    
    def retry_pending_records(self):
        """
        未送信レコードを定期的にリトライ
        GUIで設定したリトライ間隔の変更に対応
        """
        last_retry_time = 0
        
        while self.running:
            # リトライ間隔の変更に対応するため、短い間隔でチェック
            time.sleep(RETRY_CHECK_INTERVAL)
            
            if not self.server_url or not REQUESTS_AVAILABLE:
                continue
            
            current_time = time.time()
            elapsed = current_time - last_retry_time
            
            # 設定されたリトライ間隔が経過したらリトライ実行
            if elapsed >= self.retry_interval:
                last_retry_time = current_time
                
                records = self.database.get_pending_records()
                if records:
                    print(f"\n[リトライ] {len(records)}件の未送信データを再送信します（間隔: {self.retry_interval}秒）")
                    
                    for record in records:
                        record_id, idm, timestamp, terminal_id, retry_count = record
                        
                        if self.send_to_server(idm, timestamp):
                            self.database.mark_as_sent(record_id)
                            print(f"[リトライ成功] IDm: {idm}")
                        else:
                            self.database.increment_retry_count(record_id)
                            print(f"[リトライ失敗] IDm: {idm} (試行回数: {retry_count + 1})")
                    
                    # すべて送信完了したかチェック
                    pending = self.database.get_pending_records()
                    if not pending:
                        self.gpio.led("green")  # 通常に戻す
                        self.server_check_running = False
                        print("[完了] すべての未送信データを送信しました")
    
    # ========================================================================
    # LCD制御
    # ========================================================================
    
    def update_lcd_time(self):
        """
        LCDに時刻を定期的に更新表示
        2秒ごとに更新
        """
        if not self.lcd:
            return
        
        from constants import LCD_UPDATE_INTERVAL
        while self.running:
            try:
                self.lcd.show_with_time(self.current_message)
            except Exception:
                pass
            time.sleep(LCD_UPDATE_INTERVAL)
    
    def set_lcd_message(self, message, duration=0):
        """
        LCDのメッセージを設定
        
        Args:
            message (str): 表示するメッセージ
            duration (int): 表示時間（秒）。0の場合は自動で戻らない
        """
        self.current_message = message
        if self.lcd:
            try:
                self.lcd.show_with_time(message)
            except Exception:
                pass
        
        if duration > 0:
            def reset():
                time.sleep(duration)
                self.current_message = MESSAGE_TOUCH_CARD
            
            threading.Thread(target=reset, daemon=True).start()
    
    # ========================================================================
    # データベース保存とサーバー送信
    # ========================================================================
    
    def save_to_database(self, idm, timestamp, sent_to_server=0):
        """
        データベースに保存
        
        Args:
            idm (str): カードID
            timestamp (str): タイムスタンプ（ISO8601形式）
            sent_to_server (int): サーバー送信済みフラグ（0=未送信, 1=送信済み）
        
        Returns:
            int: 保存されたレコードID（失敗時はNone）
        """
        try:
            record_id = self.database.save_attendance(idm, timestamp, self.terminal_id, sent_to_server)
            return record_id
        except Exception as e:
            print(f"[エラー] データベース保存失敗: {e}")
            return None
    
    def process_card(self, card_id, reader_index):
        """
        カードを処理（サーバー送信優先 → ローカルDB保存）

        Args:
            card_id (str): カードID
            reader_index (int): リーダー番号

        Returns:
            bool: 処理成功したかどうか
        """
        timestamp = datetime.now().isoformat()
        self._handle_card_read()

        # チャタリング防止: 同一時刻打刻チェック
        if not hasattr(self, 'attendance_history'):
            self.attendance_history = {}
        
        from common_utils import is_duplicate_attendance
        is_dup, dup_msg = is_duplicate_attendance(card_id, timestamp, self.attendance_history)
        
        if is_dup:
            # 重複打刻の場合、アラートを出してスキップ
            print(f"[重複打刻] {dup_msg} - スキップ")
            self.set_lcd_message("Already Punched", 2)
            self.gpio.sound("failure")
            self.gpio.led("orange")
            time.sleep(1)
            self.gpio.led("green")
            return False

        # サーバー送信を優先
        server_sent = False
        if self.server_url and REQUESTS_AVAILABLE:
            server_sent = self.send_to_server(card_id, timestamp)

        if server_sent:
            return self._handle_server_success(card_id, timestamp)
        else:
            return self._handle_server_failure(card_id, timestamp)
    
    def _handle_card_read(self):
        """カード読み込み時のフィードバック"""
        self.set_lcd_message(MESSAGE_READING, 1)
        self.gpio.sound("card_read")
        self.gpio.led("green")
    
    def _handle_server_success(self, card_id, timestamp):
        """サーバー送信成功時の処理"""
        record_id = self.save_to_database(card_id, timestamp, sent_to_server=1)
        if record_id:
            self.set_lcd_message(MESSAGE_SENDING, 1)
            self.gpio.sound("success")
            self.gpio.led("blue")
            return True
        return self._handle_save_failure()
    
    def _handle_server_failure(self, card_id, timestamp):
        """サーバー送信失敗時の処理"""
        record_id = self.save_to_database(card_id, timestamp, sent_to_server=0)
        if record_id:
            self.set_lcd_message(MESSAGE_SAVED_LOCAL, 1)
            self.gpio.sound("failure")
            # サーバー書き込みできない場合：オレンジLED表示
            from constants import ORANGE_LED_DISPLAY_TIME
            self.gpio.led("orange")
            time.sleep(ORANGE_LED_DISPLAY_TIME)
            # 未送信データがある場合はオレンジのまま、なければ緑に戻す
            pending = self.database.get_pending_records()
            if not pending:
                self.gpio.led("green")
            return True
        return self._handle_save_failure()
    
    def _handle_save_failure(self):
        """保存失敗時の処理"""
        self.set_lcd_message(MESSAGE_SAVE_FAILED, 1)
        self.gpio.sound("failure")
        self.gpio.led("red")
        return False
    
    # ========================================================================
    # リトライ機能は削除（スタンドアロン版では不要）
    # ========================================================================
    
    # ========================================================================
    # カードリーダー制御
    # ========================================================================
    
    def nfcpy_worker(self, path, idx):
        """
        nfcpy用リーダー監視ワーカー
        
        Args:
            path (str): nfcpyデバイスパス（例: 'usb:000'）
            idx (int): リーダー番号
        """
        last_id = None
        clf = None
        
        try:
            # ContactlessFrontendを1回だけ開く（再利用することで高速化）
            clf = nfc.ContactlessFrontend(path)
            if not clf:
                print(f"[エラー] nfcpyリーダー#{idx}を開けません")
                return
            
            while self.running:
                try:
                    # カード検出（短いタイムアウトで高速化）
                    tag = clf.connect(rdwr={
                        'on-connect': lambda tag: False,
                        'beep-on-connect': False
                    }, terminate=lambda: not self.running)
                    
                    if tag:
                        # IDm または identifier を取得
                        card_id = (tag.idm if hasattr(tag, 'idm') else tag.identifier).hex().upper()
                        
                        if card_id and card_id != last_id:
                            now = time.time()
                    # 重複チェック
                    if card_id not in self.history or now - self.history[card_id] >= CARD_DUPLICATE_THRESHOLD:
                                self.history[card_id] = now
                                self.count += 1
                                
                                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] [カード#{self.count}]")
                                print(f"IDm: {card_id} (リーダー{idx})")
                                
                                self.process_card(card_id, idx)
                                last_id = card_id
                
                except IOError:
                    # カードなし - 正常な状態
                    pass
                except Exception:
                    # その他のエラーは無視
                    pass
                
                # 短いスリープで応答性を向上
                time.sleep(CARD_DETECTION_SLEEP)
        
        finally:
            # 終了時にContactlessFrontendをクローズ
            if clf:
                try:
                    clf.close()
                except:
                    pass
    
    def pcsc_worker(self, reader, idx):
        """
        PC/SC用リーダー監視ワーカー
        
        Args:
            reader: smartcard.Readerオブジェクト
            idx (int): リーダー番号
        """
        last_id = None
        
        while self.running:
            try:
                connection = reader.createConnection()
                connection.connect()
                
                # 複数のコマンドを試してカードIDを取得
                card_id = None
                commands = get_pcsc_commands(str(reader))
                
                for cmd in commands:
                    try:
                        response, sw1, sw2 = connection.transmit(cmd)
                        # 成功応答（90 00）かつ有効なデータがある場合
                        if sw1 == 0x90 and sw2 == 0x00 and len(response) >= 4:
                            uid_len = min(len(response), 16)
                            card_id = ''.join([f'{b:02X}' for b in response[:uid_len]])
                            if len(card_id) >= 8:
                                break
                    except Exception:
                        continue
                
                if card_id and card_id != last_id:
                    now = time.time()
                    # 重複チェック
                    if card_id not in self.history or now - self.history[card_id] >= CARD_DUPLICATE_THRESHOLD:
                        self.history[card_id] = now
                        self.count += 1
                        
                        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] [カード#{self.count}]")
                        print(f"IDm: {card_id} (リーダー{idx})")
                        
                        self.process_card(card_id, idx)
                        last_id = card_id
                
                connection.disconnect()
            except (CardConnectionException, NoCardException):
                # カードなし、接続エラーは正常な状態
                pass
            except Exception:
                # その他のエラーは無視
                pass
            
            time.sleep(PCSC_POLL_INTERVAL)
    
    # ========================================================================
    # メイン処理
    # ========================================================================
    
    def run(self):
        """
        メイン処理
        リーダーを検出し、各リーダーで監視スレッドを起動
        """
        print("="*70)
        print("[ラズパイ統合版クライアント（スタンドアロン版）]")
        print("="*70)
        print(f"端末ID: {self.terminal_id}")
        print(f"データベース: attendance.db（ローカル保存）")
        print(f"LCD: {'有効' if LCD_AVAILABLE else '無効'}")
        print(f"GPIO: {'有効' if GPIO_AVAILABLE else '無効'}")
        print(f"nfcpy: {'利用可能' if NFCPY_AVAILABLE else '利用不可'}")
        print(f"pyscard: {'利用可能' if PYSCARD_AVAILABLE else '利用不可'}")
        print()
        
        # リーダー検出
        nfcpy_count = 0
        pcsc_count = 0
        nfcpy_devices = []
        
        # nfcpy検出
        if NFCPY_AVAILABLE:
            print("[検出] nfcpyリーダーを検索中...")
            
            # まず'usb'で自動検出を試す（最も確実）
            try:
                clf = nfc.ContactlessFrontend('usb')
                if clf:
                    nfcpy_devices.append('usb')
                    nfcpy_count += 1
                    print(f"  - 検出: usb ({clf})")
                    clf.close()
            except IOError as e:
                # デバイスなし
                pass
            except Exception as e:
                # その他のエラー
                print(f"  [警告] nfcpy検出エラー: {e}")
                pass
            
            # 見つからない場合、特定のベンダーID:プロダクトIDで試す
            if nfcpy_count == 0:
                # Sony RC-S380
                try:
                    # Sony RC-S380のベンダーID:プロダクトID
                    SONY_RCS380_VID_PID = 'usb:054c:06c1'
                    clf = nfc.ContactlessFrontend(SONY_RCS380_VID_PID)
                    if clf:
                        nfcpy_devices.append('usb:054c:06c1')
                        nfcpy_count += 1
                        print(f"  - 検出: usb:054c:06c1 ({clf})")
                        clf.close()
                except:
                    pass
        
        # PC/SC検出
        if PYSCARD_AVAILABLE:
            print("[検出] PC/SCリーダーを検索中...")
            try:
                readers_list = pcsc_readers()
                pcsc_count = len(readers_list)
                for idx, reader in enumerate(readers_list, 1):
                    print(f"  - 検出: {reader}")
            except Exception as e:
                print(f"  [警告] PC/SC検出エラー: {e}")
                pass
        
        # リーダーが見つからない場合、待機して再試行（自動起動時のため）
        if nfcpy_count == 0 and pcsc_count == 0:
            print("[警告] カードリーダーが見つかりません")
            print("[待機] リーダーの認識を待機中...（最大60秒、30秒間隔で再検出）")
            if self.lcd:
                self.lcd.show_with_time(MESSAGE_WAIT_READER)
            if self.gpio.available:
                self.gpio.led("red")
            
            # 最大待機時間とチェック間隔
            max_wait_seconds = READER_DETECTION_MAX_WAIT
            check_interval = READER_DETECTION_CHECK_INTERVAL
            waited_seconds = 0
            
            while waited_seconds < max_wait_seconds and self.running:
                time.sleep(check_interval)
                waited_seconds += check_interval
                
                print(f"[再検出] {waited_seconds}秒経過 - リーダーを再検出中...")
                
                # 再検出を試みる
                nfcpy_count = 0
                pcsc_count = 0
                nfcpy_devices = []
                
                # nfcpy再検出
                if NFCPY_AVAILABLE:
                    try:
                        clf = nfc.ContactlessFrontend('usb')
                        if clf:
                            nfcpy_devices.append('usb')
                            nfcpy_count += 1
                            print(f"  ✅ nfcpyリーダーを検出: usb")
                            clf.close()
                            break
                    except:
                        try:
                            # Sony RC-S380のベンダーID:プロダクトID
                    SONY_RCS380_VID_PID = 'usb:054c:06c1'
                    clf = nfc.ContactlessFrontend(SONY_RCS380_VID_PID)
                            if clf:
                                nfcpy_devices.append('usb:054c:06c1')
                                nfcpy_count += 1
                                print(f"  ✅ nfcpyリーダーを検出: usb:054c:06c1")
                                clf.close()
                                break
                        except:
                            pass
                
                # PC/SC再検出
                if PYSCARD_AVAILABLE and pcsc_count == 0:
                    try:
                        readers_list = pcsc_readers()
                        pcsc_count = len(readers_list)
                        if pcsc_count > 0:
                            print(f"  ✅ PC/SCリーダーを検出: {pcsc_count}台")
                            break
                    except:
                        pass
                
                if nfcpy_count > 0 or pcsc_count > 0:
                    print("[成功] リーダーを検出しました！")
                    break
            
            # それでも見つからない場合
            if nfcpy_count == 0 and pcsc_count == 0:
                print("[エラー] カードリーダーが見つかりません（60秒待機後も検出失敗）")
                print("[情報] プログラムを終了します。リーダーを接続してサービスを再起動してください。")
                if self.lcd:
                    self.lcd.show_with_time(MESSAGE_NO_READER)
                if self.gpio.available:
                    self.gpio.led("red")
                # 自動起動時の無限ループを防ぐため、正常終了（exit code 0）
                # systemdのRestart=alwaysを避けるため、長時間待機してから終了
                from constants import READER_DETECTION_MAX_WAIT
                wait_minutes = READER_DETECTION_MAX_WAIT // 60
                print(f"[待機] {wait_minutes}分間待機してから終了します（リーダー接続を待機）...")
                time.sleep(READER_DETECTION_MAX_WAIT // 2)  # 最大待機時間の半分
                return
        
        print(f"\n[検出] nfcpy:{nfcpy_count}台 / PC/SC:{pcsc_count}台")
        print()
        
        # nfcpy リーダーの監視開始
        if nfcpy_count > 0:
            for i, path in enumerate(nfcpy_devices, 1):
                threading.Thread(
                    target=self.nfcpy_worker, 
                    args=(path, i), 
                    daemon=True
                ).start()
                print(f"[起動] nfcpyリーダー#{i} ({path}) の監視を開始")
        
        # PC/SC リーダーの監視開始
        if pcsc_count > 0:
            try:
                reader_list = pcsc_readers()
                for i, reader in enumerate(reader_list, 1):
                    reader_idx = nfcpy_count + i
                    threading.Thread(
                        target=self.pcsc_worker, 
                        args=(reader, reader_idx), 
                        daemon=True
                    ).start()
                    print(f"[起動] PC/SCリーダー#{reader_idx}の監視を開始")
            except Exception as e:
                print(f"[エラー] PC/SCリーダー起動失敗: {e}")
        
        print("\n[待機] カードをかざしてください... (Ctrl+C で終了)\n")
        
        try:
            # メインスレッドは待機
            while self.running:
                from constants import MAIN_LOOP_SLEEP
                time.sleep(MAIN_LOOP_SLEEP)
        
        except KeyboardInterrupt:
            print("\n\n" + "="*70)
            print("[終了] プログラムを終了します...")
            print("="*70)
            
            self.running = False
            
            # 統計情報を表示
            print(f"\n[統計] 読み取り統計:")
            print(f"   合計読み取り数: {self.count} 枚")
            print(f"   ユニークカード数: {len(self.history)} 枚")
            print(f"\n[終了] 終了しました\n")
            
            # LCD表示
            if self.lcd:
                self.lcd.show_with_time(MESSAGE_STOPPED)
            
            # GPIOクリーンアップ
            self.gpio.cleanup()


# ============================================================================
# 設定ファイル管理
# ============================================================================

# load_config() は common_utils からインポート済み


# ============================================================================
# GUIクラス（VNC用）
# ============================================================================

try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    print("[警告] tkinter未インストール - GUI機能は無効です")

if TKINTER_AVAILABLE:
    class UnifiedClientGUI:
        """
        ラズパイ統合版クライアントGUI（VNC用）
        サーバー状況、WiFi情報、未送信データを表示
        """
        
        def __init__(self, client):
            """
            Args:
                client: UnifiedClientインスタンス
            """
            self.client = client
            self.root = tk.Tk()
            self.root.title("勤怠管理システム - ラズパイ版")
            from constants import GUI_WINDOW_WIDTH, GUI_WINDOW_HEIGHT
            self.root.geometry(f"{GUI_WINDOW_WIDTH}x{GUI_WINDOW_HEIGHT}")
            
            # 変数
            self.retry_interval_var = tk.IntVar(value=client.retry_interval)
            
            self.setup_ui()
            self.update_status()
            
            # 定期的な更新
            from constants import GUI_UPDATE_INTERVAL
            self.root.after(GUI_UPDATE_INTERVAL, self.update_status_loop)
        
        def setup_ui(self):
            """UIを構築"""
            # メインフレーム
            main_frame = ttk.Frame(self.root, padding="10")
            main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            # サーバー状況
            server_frame = ttk.LabelFrame(main_frame, text="サーバー接続状況", padding="10")
            server_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
            
            self.server_status_label = ttk.Label(server_frame, text="確認中...", font=("", 12))
            self.server_status_label.grid(row=0, column=0, sticky=tk.W)
            
            self.server_url_label = ttk.Label(server_frame, text="")
            self.server_url_label.grid(row=1, column=0, sticky=tk.W)
            
            # WiFi情報
            wifi_frame = ttk.LabelFrame(main_frame, text="WiFi接続情報", padding="10")
            wifi_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
            
            self.wifi_info_label = ttk.Label(wifi_frame, text="取得中...")
            self.wifi_info_label.grid(row=0, column=0, sticky=tk.W)
            
            # リトライ設定
            retry_frame = ttk.LabelFrame(main_frame, text="リトライ設定", padding="10")
            retry_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
            
            ttk.Label(retry_frame, text="リトライ間隔（秒）:").grid(row=0, column=0, sticky=tk.W)
            from constants import MIN_RETRY_INTERVAL, MAX_RETRY_INTERVAL
            retry_spinbox = ttk.Spinbox(retry_frame, from_=MIN_RETRY_INTERVAL, to=MAX_RETRY_INTERVAL, textvariable=self.retry_interval_var, width=10)
            retry_spinbox.grid(row=0, column=1, padx=5)
            retry_spinbox.bind("<Return>", self.update_retry_interval)
            
            ttk.Button(retry_frame, text="適用", command=self.update_retry_interval).grid(row=0, column=2, padx=5)
            
            # 未送信データ
            pending_frame = ttk.LabelFrame(main_frame, text="未送信データ", padding="10")
            pending_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
            
            # ツリービュー
            columns = ("ID", "IDm", "時刻", "端末ID", "リトライ回数")
            self.pending_tree = ttk.Treeview(pending_frame, columns=columns, show="headings", height=10)
            for col in columns:
                self.pending_tree.heading(col, text=col)
                self.pending_tree.column(col, width=100)
            
            scrollbar = ttk.Scrollbar(pending_frame, orient=tk.VERTICAL, command=self.pending_tree.yview)
            self.pending_tree.configure(yscrollcommand=scrollbar.set)
            
            self.pending_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
            
            # 統計情報
            stats_frame = ttk.LabelFrame(main_frame, text="統計情報", padding="10")
            stats_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
            
            self.stats_label = ttk.Label(stats_frame, text="")
            self.stats_label.grid(row=0, column=0, sticky=tk.W)
            
            # グリッドの重み設定
            self.root.columnconfigure(0, weight=1)
            self.root.rowconfigure(0, weight=1)
            main_frame.columnconfigure(0, weight=1)
            main_frame.rowconfigure(3, weight=1)
            pending_frame.columnconfigure(0, weight=1)
            pending_frame.rowconfigure(0, weight=1)
        
        def get_wifi_info(self):
            """WiFi接続情報を取得"""
            try:
                import subprocess
                result = subprocess.run(['iwconfig'], capture_output=True, text=True, timeout=2)
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'ESSID:' in line:
                        essid = line.split('ESSID:')[1].split()[0].strip('"')
                        return f"SSID: {essid}"
                return "WiFi情報取得失敗"
            except:
                return "WiFi情報取得失敗"
        
        def update_status(self):
            """ステータスを更新"""
            # サーバー状況
            if self.client.server_url:
                status = "接続中" if self.client.server_available else "切断"
                color = "green" if self.client.server_available else "red"
                self.server_status_label.config(text=f"状態: {status}", foreground=color)
                self.server_url_label.config(text=f"URL: {self.client.server_url}")
            else:
                self.server_status_label.config(text="状態: サーバー未設定", foreground="gray")
                self.server_url_label.config(text="")
            
            # WiFi情報
            wifi_info = self.get_wifi_info()
            self.wifi_info_label.config(text=wifi_info)
            
            # 未送信データ
            for item in self.pending_tree.get_children():
                self.pending_tree.delete(item)
            
            from constants import DB_SEARCH_LIMIT
            pending_records = self.client.database.get_pending_records(limit=DB_SEARCH_LIMIT)
            for record in pending_records:
                record_id, idm, timestamp, terminal_id, retry_count = record
                self.pending_tree.insert("", tk.END, values=(
                    record_id, idm, timestamp[:19], terminal_id, retry_count
                ))
            
            # 統計情報
            stats = self.client.database.get_stats()
            stats_text = f"総レコード数: {stats['total_records']} | "
            stats_text += f"ユニークカード数: {stats['unique_cards']} | "
            stats_text += f"未送信データ: {len(pending_records)}件"
            self.stats_label.config(text=stats_text)
        
        def update_status_loop(self):
            """ステータス更新ループ"""
            self.update_status()
            from constants import GUI_UPDATE_INTERVAL
            self.root.after(GUI_UPDATE_INTERVAL, self.update_status_loop)
        
        def update_retry_interval(self, event=None):
            """リトライ間隔を更新"""
            new_interval = self.retry_interval_var.get()
            self.client.retry_interval = new_interval
            print(f"[設定] リトライ間隔を{new_interval}秒に変更しました")
        
        def run(self):
            """GUIメインループを開始"""
            self.root.mainloop()


# ============================================================================
# エントリーポイント
# ============================================================================

def main():
    """メイン関数"""
    print("="*70)
    print("ラズパイ統合版クライアント（ハイブリッド版）")
    print("="*70)
    print()
    
    # 設定ファイル読み込み
    config = load_config()
    server_url = config.get('server_url')
    retry_interval = config.get('retry_interval', DEFAULT_RETRY_INTERVAL)
    lcd_settings = config.get('lcd_settings', {})
    
    # メモリモニタリング設定
    memory_monitor_enabled = config.get('memory_monitor', {}).get('enabled', False)
    from constants import PENDING_DATA_MIN_AGE
    memory_monitor_interval = config.get('memory_monitor', {}).get('interval', PENDING_DATA_MIN_AGE // 2)  # デフォルト5分（10分の半分）
    memory_monitor_tracemalloc = config.get('memory_monitor', {}).get('tracemalloc', False)
    
    print(f"端末ID: {get_mac_address()}")
    print(f"データベース: attendance.db（ローカル保存）")
    if server_url:
        print(f"サーバーURL: {server_url}")
    else:
        print("サーバーURL: 未設定（ローカルのみ）")
    if lcd_settings:
        print(f"LCD設定: I2Cアドレス=0x{lcd_settings.get('i2c_addr', 0x27):02X}, バス={lcd_settings.get('i2c_bus', 1)}, バックライト={'ON' if lcd_settings.get('backlight', True) else 'OFF'}")
    if memory_monitor_enabled:
        print(f"メモリモニタリング: 有効 (間隔: {memory_monitor_interval}秒, tracemalloc: {'有効' if memory_monitor_tracemalloc else '無効'})")
    print("="*70)
    print()
    
    # メモリモニタリング開始
    memory_monitor = None
    if memory_monitor_enabled and MEMORY_MONITOR_AVAILABLE:
        try:
            memory_monitor = MemoryMonitor(
                log_file="memory_usage.log",
                interval=memory_monitor_interval,
                enable_tracemalloc=memory_monitor_tracemalloc
            )
            memory_monitor.start()
            print("[メモリモニタリング] 開始しました")
        except Exception as e:
            print(f"[警告] メモリモニタリング開始失敗: {e}")
            memory_monitor = None
    
    # クライアント起動
    try:
        client = UnifiedClient(server_url=server_url, retry_interval=retry_interval, lcd_settings=lcd_settings)
        
        # GUI起動（VNC用）- メインスレッドで実行
        if TKINTER_AVAILABLE:
            gui = UnifiedClientGUI(client)
            # カードリーダー処理を別スレッドで実行
            client_thread = threading.Thread(target=client.run, daemon=True)
            client_thread.start()
            # GUIをメインスレッドで実行（ブロッキング）
            gui.run()
        else:
            # GUIなしの場合は通常通り実行
            client.run()
    except KeyboardInterrupt:
        print("\n[終了] プログラムを終了します")
    except Exception as e:
        print(f"[エラー] 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
        # エラー時は赤LEDを点灯してブザーを鳴らす
        try:
            gpio = GPIO_Control()
            gpio.led("red")
            gpio.sound("failure")
        except:
            pass
    finally:
        # メモリモニタリング停止
        if memory_monitor:
            try:
                memory_monitor.stop()
                print("[メモリモニタリング] 停止しました")
            except:
                pass


if __name__ == "__main__":
    main()

