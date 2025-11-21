#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ラズパイ版シンプルクライアント
- 最小限の機能のみ（カード読み取り、サーバー送信、ローカル保存）
- スレッド数を削減（3-5個）
- エラーハンドリングを簡素化
- LCD/GPIOはオプション（エラー時は無効化）
"""

import time
import sys
import sqlite3
from datetime import datetime
from pathlib import Path
import threading

# 共通モジュールをインポート
from common_utils import (
    get_mac_address,
    load_config,
    check_server_connection,
    send_attendance_to_server,
    get_pcsc_commands,
    is_valid_card_id,
    is_duplicate_attendance
)
from constants import (
    DEFAULT_RETRY_INTERVAL,
    CARD_DUPLICATE_THRESHOLD,
    CARD_DETECTION_SLEEP,
    PCSC_POLL_INTERVAL,
    DB_PATH_ATTENDANCE,
    DB_PENDING_LIMIT,
    MESSAGE_TOUCH_CARD,
    MESSAGE_READING,
    MESSAGE_SENDING,
    MESSAGE_SAVED_LOCAL,
    RETRY_CHECK_INTERVAL
)

# HTTP通信（サーバー送信用）
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("[警告] requests未インストール - サーバー送信機能は無効です")

# LCD制御（オプション）
try:
    from lcd_i2c import LCD_I2C
    LCD_AVAILABLE = True
except ImportError:
    LCD_AVAILABLE = False
    print("[情報] LCD機能無効")

# GPIO制御（オプション）
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("[情報] GPIO機能無効")

# GPIO設定（オプション）
try:
    from gpio_config import BUZZER_PIN, LED_RED_PIN, LED_GREEN_PIN, LED_BLUE_PIN, BUZZER_PATTERNS, LED_COLORS
except ImportError:
    BUZZER_PIN = 18
    LED_RED_PIN, LED_GREEN_PIN, LED_BLUE_PIN = 13, 19, 26
    BUZZER_PATTERNS = {
        "card_read": [(0.05, 2000)],
        "success": [(0.1, 2500), (0.05, 2500), (0.1, 2500)],
        "failure": [(0.3, 800), (0.1, 800), (0.3, 800)]
    }
    LED_COLORS = {
        "off": (0, 0, 0),
        "green": (0, 100, 0),
        "blue": (0, 0, 100),
        "orange": (100, 50, 0),
        "red": (100, 0, 0)
    }

# nfcpy（オプション）
try:
    import nfc
    NFCPY_AVAILABLE = True
except ImportError:
    NFCPY_AVAILABLE = False
    print("[情報] nfcpy未インストール - PC/SCのみで動作")

# pyscard（オプション）
try:
    from smartcard.System import readers as pcsc_readers
    from smartcard.Exceptions import CardConnectionException, NoCardException
    PYSCARD_AVAILABLE = True
except ImportError:
    PYSCARD_AVAILABLE = False
    print("[情報] pyscard未インストール - nfcpyのみで動作")


# ============================================================================
# データベース管理（シンプル版）
# ============================================================================

class SimpleDatabase:
    """シンプルなデータベース管理"""
    
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = DB_PATH_ATTENDANCE
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """データベースの初期化"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
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
        conn.commit()
        conn.close()
        print(f"[DB] 初期化完了: {self.db_path}")
    
    def save(self, idm, timestamp, terminal_id, sent_to_server=0):
        """保存"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO attendance (idm, timestamp, terminal_id, received_at, sent_to_server, retry_count)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (idm, timestamp, terminal_id, datetime.now().isoformat(), sent_to_server, 0))
        conn.commit()
        record_id = cursor.lastrowid
        conn.close()
        return record_id
    
    def get_pending(self, limit=None):
        """未送信レコードを取得"""
        if limit is None:
            limit = DB_PENDING_LIMIT
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, idm, timestamp, terminal_id, retry_count
            FROM attendance
            WHERE sent_to_server = 0
            ORDER BY timestamp ASC
            LIMIT ?
        """, (limit,))
        records = cursor.fetchall()
        conn.close()
        return records
    
    def mark_sent(self, record_id):
        """送信済みマーク"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE attendance SET sent_to_server = 1 WHERE id = ?", (record_id,))
        conn.commit()
        conn.close()


# ============================================================================
# GPIO制御（シンプル版、エラー時は無効化）
# ============================================================================

class SimpleGPIO:
    """シンプルなGPIO制御"""
    
    def __init__(self):
        self.available = False
        self.pwms = []
        
        if not GPIO_AVAILABLE:
            return
        
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            GPIO.setup(BUZZER_PIN, GPIO.OUT)
            GPIO.setup([LED_RED_PIN, LED_GREEN_PIN, LED_BLUE_PIN], GPIO.OUT)
            self.pwms = [
                GPIO.PWM(LED_RED_PIN, 1000),
                GPIO.PWM(LED_GREEN_PIN, 1000),
                GPIO.PWM(LED_BLUE_PIN, 1000)
            ]
            for pwm in self.pwms:
                pwm.start(0)
            self.available = True
            print("[GPIO] 初期化成功")
        except Exception as e:
            print(f"[GPIO] 初期化失敗: {e} - GPIO機能を無効化")
            self.available = False
    
    def sound(self, pattern):
        """ブザーを鳴らす"""
        if not self.available:
            return
        try:
            for duration, freq in BUZZER_PATTERNS.get(pattern, []):
                pwm = GPIO.PWM(BUZZER_PIN, freq)
                pwm.start(50)
                time.sleep(duration)
                pwm.stop()
                del pwm
        except Exception:
            pass
    
    def led(self, color):
        """LEDの色を設定"""
        if not self.available:
            return
        try:
            r, g, b = LED_COLORS.get(color, (0, 0, 0))
            self.pwms[0].ChangeDutyCycle(r)
            self.pwms[1].ChangeDutyCycle(g)
            self.pwms[2].ChangeDutyCycle(b)
        except Exception:
            pass
    
    def cleanup(self):
        """クリーンアップ"""
        if not self.available:
            return
        try:
            for pwm in self.pwms:
                pwm.stop()
            GPIO.cleanup()
        except Exception:
            pass


# ============================================================================
# シンプルクライアント
# ============================================================================

class SimpleClient:
    """シンプルなクライアント（最小限の機能のみ）"""
    
    def __init__(self, server_url=None, retry_interval=None, lcd_settings=None):
        # 設定読み込み
        config = load_config()
        self.server_url = server_url or config.get('server_url')
        self.retry_interval = retry_interval or config.get('retry_interval', DEFAULT_RETRY_INTERVAL)
        
        # 基本コンポーネント
        self.terminal_id = get_mac_address()
        self.database = SimpleDatabase()
        self.gpio = SimpleGPIO()
        
        # LCD（オプション）
        self.lcd = None
        if LCD_AVAILABLE and lcd_settings:
            try:
                self.lcd = LCD_I2C(
                    addr=lcd_settings.get('i2c_addr', 0x27),
                    bus=lcd_settings.get('i2c_bus', 1),
                    backlight=lcd_settings.get('backlight', True)
                )
                if not self.lcd.available:
                    self.lcd = None
            except Exception as e:
                print(f"[LCD] 初期化失敗: {e} - LCD機能を無効化")
                self.lcd = None
        
        # 状態管理
        self.count = 0
        self.history = {}
        self.attendance_history = {}
        self.lock = threading.Lock()
        self.running = True
        self.server_available = False
        
        # LCD初期表示
        if self.lcd:
            try:
                self.lcd.show_with_time(MESSAGE_TOUCH_CARD)
            except Exception:
                self.lcd = None
        
        # サーバー接続チェック
        if self.server_url:
            self.server_available = check_server_connection(self.server_url)
            if self.server_available:
                print("[サーバー] 接続成功")
                self.gpio.led("green")
            else:
                print("[サーバー] 接続失敗 - オフラインモード")
                self.gpio.led("orange")
        
        # バックグラウンドスレッド開始（最小限）
        if self.server_url and REQUESTS_AVAILABLE:
            threading.Thread(target=self._retry_worker, daemon=True).start()
        
        if self.lcd:
            threading.Thread(target=self._lcd_worker, daemon=True).start()
    
    def _retry_worker(self):
        """リトライワーカー（シンプル版）"""
        last_retry_time = 0
        while self.running:
            time.sleep(RETRY_CHECK_INTERVAL)
            if not self.server_url or not REQUESTS_AVAILABLE:
                continue
            
            current_time = time.time()
            if current_time - last_retry_time >= self.retry_interval:
                last_retry_time = current_time
                records = self.database.get_pending()
                if records:
                    print(f"[リトライ] {len(records)}件の未送信データを送信")
                    for record in records:
                        record_id, idm, timestamp, terminal_id, retry_count = record
                        success, _ = send_attendance_to_server(idm, timestamp, terminal_id, self.server_url)
                        if success:
                            self.database.mark_sent(record_id)
                        else:
                            print(f"[リトライ失敗] IDm: {idm}")
    
    def _lcd_worker(self):
        """LCD更新ワーカー（シンプル版）"""
        if not self.lcd:
            return
        current_message = MESSAGE_TOUCH_CARD
        update_count = 0
        error_count = 0
        while self.running:
            try:
                if hasattr(self, '_lcd_message'):
                    current_message = self._lcd_message
                
                # デバッグ出力（10回ごと）
                if update_count % 10 == 0:
                    print(f"[LCD DEBUG] 更新回数: {update_count}, メッセージ: '{current_message}', LCD状態: available={self.lcd.available if self.lcd else False}")
                
                # メッセージの長さチェック
                if len(current_message) > 16:
                    print(f"[LCD WARN] メッセージが長すぎます: {len(current_message)}文字 - '{current_message}'")
                    current_message = current_message[:16]
                
                self.lcd.show_with_time(current_message)
                update_count += 1
                error_count = 0  # 成功したらエラーカウントをリセット
                
            except Exception as e:
                error_count += 1
                import traceback
                print(f"[LCD ERROR #{error_count}] 更新回数: {update_count}, エラー: {e}")
                print(f"[LCD ERROR] トレースバック:")
                traceback.print_exc()
                
                # エラーが5回連続したら無効化
                if error_count >= 5:
                    print(f"[LCD FATAL] エラーが{error_count}回連続 - LCD機能を無効化")
                    self.lcd = None
                    break
                
                # エラー時は少し待機してから再試行
                time.sleep(0.5)
            time.sleep(2)
    
    def set_lcd_message(self, message, duration=0):
        """LCDメッセージ設定"""
        if self.lcd:
            # デバッグ出力
            print(f"[LCD SET] メッセージ設定: '{message}' (長さ: {len(message)})")
            
            # メッセージを16文字に制限
            if len(message) > 16:
                print(f"[LCD WARN] メッセージを16文字に切り詰め: '{message}' -> '{message[:16]}'")
                message = message[:16]
            
            self._lcd_message = message
            try:
                self.lcd.show_with_time(message)
                print(f"[LCD SET] 表示成功")
            except Exception as e:
                import traceback
                print(f"[LCD SET ERROR] エラー: {e}")
                traceback.print_exc()
                # エラー時はリセットを試みる
                try:
                    print(f"[LCD SET] リセットを試行...")
                    self.lcd.reset()
                    time.sleep(0.1)
                    print(f"[LCD SET] リセット成功")
                except Exception as reset_error:
                    print(f"[LCD SET FATAL] リセット失敗: {reset_error} - LCD機能を無効化")
                    self.lcd = None
        if duration > 0:
            def reset():
                time.sleep(duration)
                self._lcd_message = MESSAGE_TOUCH_CARD
            threading.Thread(target=reset, daemon=True).start()
    
    def process_card(self, card_id, reader_idx):
        """カード処理（シンプル版）"""
        timestamp = datetime.now().isoformat()
        
        # デバッグ出力（15回ごと）
        if self.count % 15 == 0:
            import sys
            import gc
            print(f"[CARD PROCESS #{self.count}] カードID: {card_id}")
            print(f"[CARD PROCESS] メモリ使用量: {sys.getsizeof(self.history)} bytes (history), {sys.getsizeof(self.attendance_history)} bytes (attendance_history)")
            print(f"[CARD PROCESS] オブジェクト数: {len(gc.get_objects())}")
            if self.lcd:
                print(f"[CARD PROCESS] LCD状態: available={self.lcd.available}, _error_count={getattr(self.lcd, '_error_count', 'N/A')}")
        
        # フィードバック
        self.gpio.sound("card_read")
        self.gpio.led("green")
        self.set_lcd_message(MESSAGE_READING, 1)
        
        # 重複チェック
        is_dup, _ = is_duplicate_attendance(card_id, timestamp, self.attendance_history)
        if is_dup:
            print(f"[重複] {card_id} - スキップ")
            self.gpio.sound("failure")
            self.gpio.led("orange")
            time.sleep(1)
            self.gpio.led("green")
            return False
        
        # サーバー送信
        server_sent = False
        if self.server_url and REQUESTS_AVAILABLE:
            success, _ = send_attendance_to_server(card_id, timestamp, self.terminal_id, self.server_url)
            server_sent = success
        
        # 保存
        if server_sent:
            self.database.save(card_id, timestamp, self.terminal_id, sent_to_server=1)
            self.gpio.sound("success")
            self.gpio.led("blue")
            self.set_lcd_message(MESSAGE_SENDING, 1)
            print(f"[送信成功] {card_id}")
        else:
            self.database.save(card_id, timestamp, self.terminal_id, sent_to_server=0)
            self.gpio.sound("failure")
            self.gpio.led("orange")
            self.set_lcd_message(MESSAGE_SAVED_LOCAL, 1)
            print(f"[保存] {card_id} (オフライン)")
        
        time.sleep(0.5)
        self.gpio.led("green")
        return True
    
    def nfcpy_worker(self, path, idx):
        """nfcpyワーカー（シンプル版）"""
        last_id = None
        clf = None
        
        try:
            clf = nfc.ContactlessFrontend(path)
            if not clf:
                return
            
            while self.running:
                try:
                    tag = clf.connect(rdwr={
                        'on-connect': lambda tag: False,
                        'beep-on-connect': False
                    }, terminate=lambda: not self.running)
                    
                    if tag:
                        card_id = (tag.idm if hasattr(tag, 'idm') else tag.identifier).hex().upper()
                        if card_id and card_id != last_id:
                            now = time.time()
                            with self.lock:
                                if card_id not in self.history or now - self.history[card_id] >= CARD_DUPLICATE_THRESHOLD:
                                    self.history[card_id] = now
                                    self.count += 1
                                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] [カード#{self.count}] IDm: {card_id}")
                                    self.process_card(card_id, idx)
                                    last_id = card_id
                except IOError:
                    pass
                except Exception as e:
                    print(f"[nfcpyエラー] {e}")
                
                time.sleep(CARD_DETECTION_SLEEP)
        finally:
            if clf:
                try:
                    clf.close()
                except Exception:
                    pass
    
    def pcsc_worker(self, reader, idx):
        """PC/SCワーカー（シンプル版）"""
        last_id = None
        
        while self.running:
            try:
                connection = reader.createConnection()
                connection.connect()
                
                card_id = None
                commands = get_pcsc_commands(str(reader))
                
                for cmd in commands:
                    try:
                        response, sw1, sw2 = connection.transmit(cmd)
                        if sw1 == 0x90 and sw2 == 0x00 and len(response) >= 4:
                            uid_len = min(len(response), 16)
                            card_id = ''.join([f'{b:02X}' for b in response[:uid_len]])
                            if len(card_id) >= 8 and is_valid_card_id(card_id):
                                break
                    except Exception:
                        continue
                
                if card_id and card_id != last_id:
                    now = time.time()
                    with self.lock:
                        if card_id not in self.history or now - self.history[card_id] >= CARD_DUPLICATE_THRESHOLD:
                            self.history[card_id] = now
                            self.count += 1
                            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] [カード#{self.count}] IDm: {card_id}")
                            self.process_card(card_id, idx)
                            last_id = card_id
                
                connection.disconnect()
            except (CardConnectionException, NoCardException):
                pass
            except Exception as e:
                print(f"[PC/SCエラー] {e}")
            
            time.sleep(PCSC_POLL_INTERVAL)
    
    def run(self):
        """メイン処理（シンプル版）"""
        print("="*70)
        print("[ラズパイ版シンプルクライアント]")
        print("="*70)
        print(f"端末ID: {self.terminal_id}")
        print(f"DB: {self.database.db_path}")
        print(f"LCD: {'有効' if self.lcd else '無効'}")
        print(f"GPIO: {'有効' if self.gpio.available else '無効'}")
        print(f"nfcpy: {'利用可能' if NFCPY_AVAILABLE else '利用不可'}")
        print(f"pyscard: {'利用可能' if PYSCARD_AVAILABLE else '利用不可'}")
        print()
        
        # リーダー検出（シンプル版：1回のみ）
        nfcpy_paths = []
        pcsc_readers_list = []
        
        # nfcpy検出
        if NFCPY_AVAILABLE:
            try:
                clf = nfc.ContactlessFrontend('usb')
                if clf:
                    nfcpy_paths.append(('usb', 1))
                    clf.close()
                    print("[検出] nfcpyリーダー: usb")
            except Exception:
                try:
                    clf = nfc.ContactlessFrontend('usb:054c:06c1')
                    if clf:
                        nfcpy_paths.append(('usb:054c:06c1', 1))
                        clf.close()
                        print("[検出] nfcpyリーダー: usb:054c:06c1")
                except Exception:
                    pass
        
        # PC/SC検出
        if PYSCARD_AVAILABLE:
            try:
                readers_list = pcsc_readers()
                for i, reader in enumerate(readers_list, 1):
                    pcsc_readers_list.append((reader, len(nfcpy_paths) + i))
                    print(f"[検出] PC/SCリーダー: {reader}")
            except Exception:
                pass
        
        # リーダーが見つからない場合
        if not nfcpy_paths and not pcsc_readers_list:
            print("[エラー] カードリーダーが見つかりません")
            print("[情報] リーダーを接続して再起動してください")
            if self.lcd:
                try:
                    self.lcd.show_with_time("No Reader")
                except Exception:
                    pass
            self.gpio.led("red")
            return
        
        print(f"\n[起動] nfcpy:{len(nfcpy_paths)}台 / PC/SC:{len(pcsc_readers_list)}台\n")
        
        # リーダーワーカー起動
        for path, idx in nfcpy_paths:
            threading.Thread(target=self.nfcpy_worker, args=(path, idx), daemon=True).start()
            print(f"[起動] nfcpyリーダー#{idx}")
        
        for reader, idx in pcsc_readers_list:
            threading.Thread(target=self.pcsc_worker, args=(reader, idx), daemon=True).start()
            print(f"[起動] PC/SCリーダー#{idx}")
        
        print("\n[待機] カードをかざしてください... (Ctrl+C で終了)\n")
        
        # メインループ
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[終了] プログラムを終了します...")
            self.running = False
            print(f"[統計] 読み取り数: {self.count} 枚")
            if self.lcd:
                try:
                    self.lcd.show_with_time("Stopped")
                except Exception:
                    pass
            self.gpio.cleanup()


# ============================================================================
# エントリーポイント
# ============================================================================

def main():
    """メイン関数"""
    config = load_config()
    server_url = config.get('server_url')
    retry_interval = config.get('retry_interval', DEFAULT_RETRY_INTERVAL)
    lcd_settings = config.get('lcd_settings', {})
    
    try:
        client = SimpleClient(
            server_url=server_url,
            retry_interval=retry_interval,
            lcd_settings=lcd_settings
        )
        client.run()
    except KeyboardInterrupt:
        print("\n[終了] プログラムを終了します")
    except Exception as e:
        print(f"[エラー] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

