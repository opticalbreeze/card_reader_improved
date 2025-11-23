#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi版クライアント

このモジュールは、Raspberry Pi環境で動作するICカード打刻クライアントです。
Windows版（win_client.py）とは完全に分離されています。

主な特徴:
    - カード読み取り: nfcpyとPC/SCの両方に対応
    - サーバー送信: 打刻データをサーバーに送信
    - ローカル保存: SQLiteデータベースに保存
    - 自動リトライ: 未送信データを定期的に再送信
    - LCD表示: I2C接続のLCDディスプレイに状態を表示（オプション）
    - GPIO制御: RGB LEDと圧電ブザーで視覚・聴覚フィードバック（オプション）
    - エラー耐性: LCD/GPIOはエラー時は自動的に無効化

使用方法:
    python3 pi_client.py

依存関係:
    - common_utils.py: 共通ユーティリティ関数
    - constants.py: 定数定義
    - gpio_config.py: GPIO設定（オプション）
    - lcd_i2c.py: LCD制御（オプション）
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
    # デフォルトのブザーパターンとLED色（最小限）
    BUZZER_PATTERNS = {
        "card_read": [(0.05, 2000)],
        "success": [(0.1, 2500), (0.05, 2500), (0.1, 2500)],
        "failure": [(0.3, 800), (0.1, 800), (0.3, 800)]
    }
    LED_COLORS = {
        "off": (0, 0, 0),
        "green": (0, 100, 0),
        "blue": (0, 0, 100),
        "cyan": (0, 100, 100),
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
            print(f"[GPIO] ピン設定完了: BUZZER={BUZZER_PIN}, LED={LED_RED_PIN},{LED_GREEN_PIN},{LED_BLUE_PIN}")
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
            import traceback
            print(f"[GPIO] 初期化失敗: {e}")
            print(f"[GPIO] エラー詳細:")
            traceback.print_exc()
            self.available = False
    
    def sound(self, pattern):
        """ブザーを鳴らす"""
        if not self.available:
            print(f"[GPIO] ブザー無効: pattern={pattern}")
            return
        try:
            patterns = BUZZER_PATTERNS.get(pattern, [])
            if not patterns:
                print(f"[GPIO] ブザーパターン未定義: {pattern}")
                return
            for duration, freq in patterns:
                pwm = GPIO.PWM(BUZZER_PIN, freq)
                pwm.start(50)
                time.sleep(duration)
                pwm.stop()
                del pwm
        except Exception as e:
            print(f"[GPIO] ブザーエラー: {e}")
    
    def led(self, color):
        """LEDの色を設定"""
        if not self.available:
            print(f"[GPIO] LED無効: color={color}")
            return
        try:
            rgb = LED_COLORS.get(color)
            if rgb is None:
                print(f"[GPIO] LED色未定義: {color}")
                return
            r, g, b = rgb
            self.pwms[0].ChangeDutyCycle(r)
            self.pwms[1].ChangeDutyCycle(g)
            self.pwms[2].ChangeDutyCycle(b)
        except Exception as e:
            print(f"[GPIO] LEDエラー: color={color}, error={e}")
    
    def led_blink(self, color, times=3, duration=0.15, interval=0.1):
        """LEDを点滅させる"""
        if not self.available:
            return
        for _ in range(times):
            self.led(color)
            time.sleep(duration)
            self.led("off")
            time.sleep(interval)
    
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
        self.processing_cards = set()  # 処理中のカードIDを追跡
        self.lock = threading.Lock()
        self.running = True
        self.server_available = False
        
        # LCD初期表示
        if self.lcd:
            try:
                self.lcd.show_with_time(MESSAGE_TOUCH_CARD)
            except Exception:
                self.lcd = None
        
        # GPIO状態確認
        print(f"[GPIO状態] available={self.gpio.available}")
        if not self.gpio.available:
            print("[警告] GPIO機能が無効です - LEDとブザーは動作しません")
        
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
        while self.running:
            try:
                if hasattr(self, '_lcd_message'):
                    current_message = self._lcd_message
                self.lcd.show_with_time(current_message)
            except Exception:
                pass
            time.sleep(2)
    
    def set_lcd_message(self, message, duration=0):
        """LCDメッセージ設定"""
        if self.lcd:
            if len(message) > 16:
                message = message[:16]
            self._lcd_message = message
            try:
                self.lcd.show_with_time(message)
            except Exception:
                pass
        if duration > 0:
            def reset():
                time.sleep(duration)
                self._lcd_message = MESSAGE_TOUCH_CARD
            threading.Thread(target=reset, daemon=True).start()
    
    def process_card(self, card_id, reader_idx):
        """カード処理（シンプル版）"""
        # 処理中の重複チェック（ロック内で行う）
        with self.lock:
            if card_id in self.processing_cards:
                return False  # 既に処理中
            self.processing_cards.add(card_id)
        
        try:
            timestamp = datetime.now().isoformat()
            
            # フィードバック
            self.gpio.sound("card_read")
            self.gpio.led("green")
            self.set_lcd_message(MESSAGE_READING, 1)
            
            # 重複チェック（同じhh:mmでなければOK）
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
                # 成功時はシアン色で3回点滅
                self.gpio.led_blink("cyan", times=3, duration=0.15, interval=0.1)
                self.gpio.led("cyan")
                self.set_lcd_message(MESSAGE_SENDING, 1)
                print(f"[送信成功] {card_id}")
                time.sleep(1.0)
            else:
                self.database.save(card_id, timestamp, self.terminal_id, sent_to_server=0)
                self.gpio.sound("failure")
                self.gpio.led("red")
                self.set_lcd_message(MESSAGE_SAVED_LOCAL, 1)
                print(f"[保存] {card_id} (オフライン)")
                time.sleep(0.5)
            
            self.gpio.led("green")
            return True
        finally:
            # 処理完了後、processing_cardsから削除
            with self.lock:
                self.processing_cards.discard(card_id)
    
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
                                    last_id = card_id
                                    # process_cardは重複チェックを内蔵しているので、直接呼び出す
                                    self.process_card(card_id, idx)
                        else:
                            # カードが離れた場合、last_idをリセット
                            if not tag:
                                last_id = None
                except IOError:
                    last_id = None
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
                            last_id = card_id
                            # process_cardは重複チェックを内蔵しているので、直接呼び出す
                            self.process_card(card_id, idx)
                else:
                    if not card_id:
                        last_id = None
                
                connection.disconnect()
            except (CardConnectionException, NoCardException):
                last_id = None
                pass
            except Exception as e:
                print(f"[PC/SCエラー] {e}")
            
            time.sleep(PCSC_POLL_INTERVAL)
    
    def run(self):
        """メイン処理（シンプル版）"""
        print("="*70)
        print("[ラズパイ版クライアント]")
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
