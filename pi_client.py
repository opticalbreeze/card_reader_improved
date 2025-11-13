#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ラズパイ統合版クライアント（ハイブリッド版）
- LCD I2C 1602対応
- GPIO制御（LED + ブザー）
- nfcpy + PC/SC両対応
- MACアドレスベースの端末ID自動取得
- オフライン優先：ローカルDBに保存 → サーバーが利用可能な時に自動送信
"""

import time
import sys
import json
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import threading

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
    from gpio_config import *
except ImportError:
    # デフォルト設定
    BUZZER_PIN = 18
    LED_RED_PIN, LED_GREEN_PIN, LED_BLUE_PIN = 13, 19, 26
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


# ============================================================================
# ユーティリティ関数
# ============================================================================

def get_mac_address():
    """
    端末のMACアドレスを取得
    
    Returns:
        str: MACアドレス（例: "AA:BB:CC:DD:EE:FF"）
    """
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
    return ":".join([mac[i:i+2] for i in range(0, 12, 2)]).upper()


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
                GPIO.PWM(LED_RED_PIN, 1000),
                GPIO.PWM(LED_GREEN_PIN, 1000),
                GPIO.PWM(LED_BLUE_PIN, 1000)
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
                pwm = GPIO.PWM(BUZZER_PIN, freq)
                pwm.start(50)  # デューティ比50%
                time.sleep(duration)
                pwm.stop()
                time.sleep(0.05)
            except Exception as e:
                print(f"[エラー] ブザー制御失敗 ({pattern}, {freq}Hz): {e}")
                import traceback
                traceback.print_exc()
    
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
            while self.blink_running:
                self.led("orange")
                time.sleep(0.5)
                self.led("off")
                time.sleep(0.5)
        
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
    
    def __init__(self, db_path="attendance.db"):
        """
        Args:
            db_path (str): データベースファイルのパス
        """
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
    
    def get_pending_records(self, limit=50):
        """
        未送信のレコードを取得
        
        Args:
            limit (int): 取得件数の上限
        
        Returns:
            list: (id, idm, timestamp, terminal_id, retry_count) のタプルのリスト
        """
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
    
    def __init__(self, server_url=None, retry_interval=600, lcd_settings=None):
        """
        ハイブリッド版：サーバーURLはオプション
        
        Args:
            server_url (str): サーバーURL（Noneの場合はサーバー送信なし）
            retry_interval (int): リトライ間隔（秒、デフォルト600秒=10分）
            lcd_settings (dict): LCD設定（i2c_addr, i2c_bus, backlight）
        """
        self.server_url = server_url
        self.retry_interval = retry_interval
        self.lcd_settings = lcd_settings or {}
        self._init_components()
        self._led_startup_demo()  # 起動時LEDデモ
        self._init_server()
        self._init_lcd()
        self._start_background_threads()
    
    def _init_components(self):
        """基本コンポーネントの初期化"""
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
        
        # TODO: カタカナ表示は後日対応
        # self.current_message = f"カードタッチ {terminal_short}"
        self.current_message = "Touch Card"
        
        # 起動音
        self.gpio.sound("startup")
    
    def _init_server(self):
        """サーバー接続チェックとエラー処理"""
        if not self.server_url:
            self.gpio.led("green")
            return
        
        self.check_server_connection()
        if not self.server_available:
            # サーバー接続失敗：3秒LEDエラー表示+ブザー
            self.gpio.led("red")
            self.gpio.sound("failure")
            time.sleep(3)
            # 10秒ごとの赤LEDフリッカ開始
            self.server_check_running = True
            threading.Thread(target=self.server_error_flicker, daemon=True).start()
        else:
            self.gpio.led("green")
    
    def _led_startup_demo(self):
        """起動時LEDデモ（赤→青→緑を順番に点灯）"""
        self.gpio.led("red")
        time.sleep(0.5)
        self.gpio.led("blue")
        time.sleep(0.5)
        self.gpio.led("green")
        time.sleep(0.5)
        self.gpio.led("off")
    
    def _init_lcd(self):
        """LCD初期化と表示"""
        if not self.lcd:
            return
        
        # TODO: カタカナ表示は後日対応（文字コード調査が必要）
        # self.lcd.show_with_time("キドウチュウ")
        self.lcd.show_with_time("Starting...")
        time.sleep(2)
        # TODO: カタカナ表示は後日対応
        # self.lcd.show_with_time(f"カードタッチ {terminal_display}")
        self.lcd.show_with_time("Touch Card")
    
    def _start_background_threads(self):
        """バックグラウンドスレッド開始"""
        # LCD時刻更新スレッド
        threading.Thread(target=self.update_lcd_time, daemon=True).start()
        
        # サーバー送信リトライスレッド
        if self.server_url and REQUESTS_AVAILABLE:
            threading.Thread(target=self.retry_pending_records, daemon=True).start()
    
    # ========================================================================
    # サーバー通信
    # ========================================================================
    
    def check_server_connection(self):
        """
        サーバー接続をチェック
        
        Returns:
            bool: サーバーが利用可能かどうか
        """
        if not self.server_url or not REQUESTS_AVAILABLE:
            self.server_available = False
            return False
        
        try:
            response = requests.get(f"{self.server_url}/api/health", timeout=3)
            if response.status_code == 200:
                self.server_available = True
                return True
        except:
            pass
        
        self.server_available = False
        return False
    
    def send_to_server(self, idm, timestamp):
        """
        サーバーにデータを送信
        
        Args:
            idm (str): カードID
            timestamp (str): タイムスタンプ（ISO8601形式）
        
        Returns:
            bool: 送信成功したかどうか
        """
        if not self.server_url or not REQUESTS_AVAILABLE:
            return False
        
        data = {
            'idm': idm,
            'timestamp': timestamp,
            'terminal_id': self.terminal_id
        }
        
        try:
            response = requests.post(
                f"{self.server_url}/api/attendance",
                json=data,
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    print(f"[送信成功] {result.get('message', 'サーバーに記録')}")
                    self.server_available = True
                    return True
                else:
                    print(f"[送信失敗] サーバーエラー: {result.get('message')}")
                    return False
            else:
                print(f"[送信失敗] HTTP {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            print(f"[送信失敗] サーバー接続エラー: {self.server_url}")
            self.server_available = False
            return False
        except requests.exceptions.Timeout:
            print(f"[送信失敗] タイムアウト（5秒）")
            self.server_available = False
            return False
        except Exception as e:
            print(f"[送信失敗] 予期しないエラー: {e}")
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
                self.gpio.led("red")
                time.sleep(0.5)
                self.gpio.led("off")
            time.sleep(10)
    
    def retry_pending_records(self):
        """
        未送信レコードを定期的にリトライ
        GUIで設定したリトライ間隔の変更に対応
        """
        last_retry_time = 0
        
        while self.running:
            # リトライ間隔の変更に対応するため、短い間隔でチェック
            # 1秒ごとにチェックして、設定された間隔が経過したらリトライ実行
            time.sleep(1)
            
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
        
        while self.running:
            try:
                self.lcd.show_with_time(self.current_message)
            except Exception:
                pass
            time.sleep(2)
    
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
                # TODO: カタカナ表示は後日対応
                # self.current_message = f"カードタッチ {terminal_short}"
                self.current_message = "Touch Card"
            
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
        # TODO: カタカナ表示は後日対応
        # self.set_lcd_message("カード読取", 1)
        self.set_lcd_message("Reading...", 1)
        self.gpio.sound("card_read")
        self.gpio.led("green")
    
    def _handle_server_success(self, card_id, timestamp):
        """サーバー送信成功時の処理"""
        record_id = self.save_to_database(card_id, timestamp, sent_to_server=1)
        if record_id:
            # TODO: カタカナ表示は後日対応
            # self.set_lcd_message("サーバー送信", 1)
            self.set_lcd_message("Sending...", 1)
            self.gpio.sound("success")
            self.gpio.led("blue")
            return True
        return self._handle_save_failure()
    
    def _handle_server_failure(self, card_id, timestamp):
        """サーバー送信失敗時の処理"""
        record_id = self.save_to_database(card_id, timestamp, sent_to_server=0)
        if record_id:
            # TODO: カタカナ表示は後日対応
            # self.set_lcd_message("ローカル保存", 1)
            self.set_lcd_message("Saved Local", 1)
            self.gpio.sound("failure")
            # サーバー書き込みできない場合：0.5秒オレンジLED表示
            self.gpio.led("orange")
            time.sleep(0.5)
            # 未送信データがある場合はオレンジのまま、なければ緑に戻す
            pending = self.database.get_pending_records()
            if not pending:
                self.gpio.led("green")
            return True
        return self._handle_save_failure()
    
    def _handle_save_failure(self):
        """保存失敗時の処理"""
        # TODO: カタカナ表示は後日対応
        # self.set_lcd_message("保存失敗", 1)
        self.set_lcd_message("Save Failed", 1)
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
                            # 重複チェック（2秒以内は無視）
                            if card_id not in self.history or now - self.history[card_id] >= 2.0:
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
                time.sleep(0.05)
        
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
                commands = [
                    [0xFF, 0xCA, 0x00, 0x00, 0x00],  # UID（可変長）
                    [0xFF, 0xCA, 0x00, 0x00, 0x04],  # 4バイト UID
                    [0xFF, 0xCA, 0x00, 0x00, 0x07]   # 7バイト UID
                ]
                
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
                    # 重複チェック（2秒以内は無視）
                    if card_id not in self.history or now - self.history[card_id] >= 2.0:
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
            
            time.sleep(0.3)
    
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
                    clf = nfc.ContactlessFrontend('usb:054c:06c1')
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
        
        # リーダーが見つからない場合
        if nfcpy_count == 0 and pcsc_count == 0:
            print("[エラー] カードリーダーが見つかりません")
            print("[ヒント] リーダーを接続してプログラムを再起動してください")
            if self.lcd:
                # TODO: カタカナ表示は後日対応
                # self.lcd.show_with_time("リーダーなし")
                self.lcd.show_with_time("No Reader")
            self.gpio.led("red")
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
                time.sleep(0.5)
        
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
                # TODO: カタカナ表示は後日対応
                # self.lcd.show_with_time("停止")
                self.lcd.show_with_time("Stopped")
            
            # GPIOクリーンアップ
            self.gpio.cleanup()


# ============================================================================
# 設定ファイル管理
# ============================================================================

def load_config():
    """
    設定ファイルを読み込む
    
    Returns:
        dict: 設定辞書（server_url, retry_interval, lcd_settingsなど）
    """
    config_path = Path("client_config.json")
    default_config = {
        "lcd_settings": {
            "i2c_addr": 0x27,      # LCD I2Cアドレス（0x27または0x3F）
            "i2c_bus": 1,           # I2Cバス番号（Raspberry Pi 3/4は1、初期モデルは0）
            "backlight": True       # バックライトON/OFF
        }
    }
    
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # デフォルト設定をマージ（設定ファイルにない項目はデフォルト値を使用）
                if 'lcd_settings' not in config:
                    config['lcd_settings'] = default_config['lcd_settings']
                else:
                    # 部分的な設定がある場合、デフォルトとマージ
                    for key, value in default_config['lcd_settings'].items():
                        if key not in config['lcd_settings']:
                            config['lcd_settings'][key] = value
                return config
        except Exception as e:
            print(f"[警告] 設定ファイル読み込みエラー: {e}")
            return default_config
    return default_config


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
            self.root.geometry("800x600")
            
            # 変数
            self.retry_interval_var = tk.IntVar(value=client.retry_interval)
            
            self.setup_ui()
            self.update_status()
            
            # 定期的な更新（1秒ごと）
            self.root.after(1000, self.update_status_loop)
        
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
            retry_spinbox = ttk.Spinbox(retry_frame, from_=60, to=3600, textvariable=self.retry_interval_var, width=10)
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
            
            pending_records = self.client.database.get_pending_records(limit=100)
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
            self.root.after(1000, self.update_status_loop)
        
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
    retry_interval = config.get('retry_interval', 600)
    lcd_settings = config.get('lcd_settings', {})
    
    print(f"端末ID: {get_mac_address()}")
    print(f"データベース: attendance.db（ローカル保存）")
    if server_url:
        print(f"サーバーURL: {server_url}")
    else:
        print("サーバーURL: 未設定（ローカルのみ）")
    if lcd_settings:
        print(f"LCD設定: I2Cアドレス=0x{lcd_settings.get('i2c_addr', 0x27):02X}, バス={lcd_settings.get('i2c_bus', 1)}, バックライト={'ON' if lcd_settings.get('backlight', True) else 'OFF'}")
    print("="*70)
    print()
    
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


if __name__ == "__main__":
    main()

