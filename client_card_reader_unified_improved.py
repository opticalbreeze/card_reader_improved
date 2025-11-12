#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ラズパイ統合版クライアント（スタンドアロン版）
- LCD I2C 1602対応
- GPIO制御（LED + ブザー）
- nfcpy + PC/SC両対応
- MACアドレスベースの端末ID自動取得
- ローカルデータベースに直接保存（サーバー不要）
"""

import time
import sys
import json
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import threading

# ============================================================================
# ライブラリ依存関係の確認
# ============================================================================

# LCD制御
try:
    from lcd_i2c_improved import LCD_I2C
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
            return
        
        try:
            # GPIO設定
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            GPIO.setup(BUZZER_PIN, GPIO.OUT)
            GPIO.setup([LED_RED_PIN, LED_GREEN_PIN, LED_BLUE_PIN], GPIO.OUT)
            print(f"[GPIO] ピン設定完了 - 赤:{LED_RED_PIN} 緑:{LED_GREEN_PIN} 青:{LED_BLUE_PIN}")
            
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
        except Exception as e:
            print(f"[警告] GPIO初期化失敗: {e}")
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
            return
        
        for duration, freq in BUZZER_PATTERNS.get(pattern, [(0.1, 1000)]):
            try:
                pwm = GPIO.PWM(BUZZER_PIN, freq)
                pwm.start(50)  # デューティ比50%
                time.sleep(duration)
                pwm.stop()
                time.sleep(0.05)
            except Exception:
                pass
    
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
        
        # 打刻データテーブル（サーバーと同じ構造）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                idm TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                terminal_id TEXT NOT NULL,
                received_at TEXT NOT NULL
            )
        """)
        
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
    
    def save_attendance(self, idm, timestamp, terminal_id):
        """
        打刻データをデータベースに保存
        
        Args:
            idm (str): カードID
            timestamp (str): タイムスタンプ（ISO8601形式）
            terminal_id (str): 端末ID
        
        Returns:
            int: 保存されたレコードID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO attendance (idm, timestamp, terminal_id, received_at)
            VALUES (?, ?, ?, ?)
        """, (idm, timestamp, terminal_id, datetime.now().isoformat()))
        conn.commit()
        record_id = cursor.lastrowid
        conn.close()
        print(f"[保存完了] ID:{record_id} | IDm:{idm} | 端末:{terminal_id} | 時刻:{timestamp}")
        return record_id
    
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
    ラズパイ統合版クライアント（スタンドアロン版）
    LCD + GPIO + nfcpy/PC/SC全てに対応
    サーバー不要で直接データベースに保存
    """
    
    def __init__(self):
        """
        スタンドアロン版：サーバーURL不要
        """
        self.terminal_id = get_mac_address()  # MACアドレスを端末IDとして使用
        self.database = LocalDatabase()  # ローカルデータベース
        self.gpio = GPIO_Control()
        self.lcd = LCD_I2C() if LCD_AVAILABLE else None
        self.count = 0
        self.history = {}  # {card_id: last_seen_time}
        self.lock = threading.Lock()
        self.running = True
        self.current_message = "カードタッチ"
        
        # 起動処理
        self.gpio.sound("startup")
        self.gpio.led("green")  # スタンドアロン版は常に緑
        if self.lcd:
            self.lcd.show_with_time("キドウチュウ")
            time.sleep(2)
            self.lcd.show_with_time("カードタッチ")
        
        # バックグラウンドスレッド開始
        threading.Thread(target=self.update_lcd_time, daemon=True).start()
    
    # ========================================================================
    # サーバー監視機能は削除（スタンドアロン版では不要）
    # ========================================================================
    
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
                self.current_message = "カードタッチ"
            threading.Thread(target=reset, daemon=True).start()
    
    # ========================================================================
    # データベース保存（スタンドアロン版）
    # ========================================================================
    
    def save_to_database(self, idm, timestamp):
        """
        データベースに直接保存（スタンドアロン版）
        
        Args:
            idm (str): カードID
            timestamp (str): タイムスタンプ（ISO8601形式）
        
        Returns:
            bool: 保存成功したかどうか
        """
        try:
            record_id = self.database.save_attendance(idm, timestamp, self.terminal_id)
            self.set_lcd_message("保存完了", 1)
            self.gpio.sound("success")
            self.gpio.led("blue")
            return True
        except Exception as e:
            print(f"[エラー] データベース保存失敗: {e}")
            self.set_lcd_message("保存失敗", 1)
            self.gpio.sound("failure")
            self.gpio.led("orange")
            return False
    
    def process_card(self, card_id, reader_index):
        """
        カードを処理（データベースに直接保存）
        
        Args:
            card_id (str): カードID
            reader_index (int): リーダー番号
        
        Returns:
            bool: 処理成功したかどうか
        """
        timestamp = datetime.now().isoformat()
        
        # カード読み込みフィードバック
        self.set_lcd_message("カード読取", 1)
        self.gpio.sound("card_read")
        self.gpio.led("green")
        
        # データベースに直接保存
        return self.save_to_database(card_id, timestamp)
    
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
                self.lcd.show_with_time("リーダーなし")
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
                self.lcd.show_with_time("停止")
            
            # GPIOクリーンアップ
            self.gpio.cleanup()


# ============================================================================
# 設定ファイル管理（スタンドアロン版では不要）
# ============================================================================

# スタンドアロン版では設定ファイル不要
# 以前のバージョンとの互換性のため、関数は残すが使用しない


# ============================================================================
# エントリーポイント
# ============================================================================

def main():
    """メイン関数"""
    print("="*70)
    print("ラズパイ統合版クライアント（スタンドアロン版）")
    print("="*70)
    print()
    
    print(f"端末ID: {get_mac_address()}")
    print(f"データベース: attendance.db（ローカル保存）")
    print("="*70)
    print()
    
    # クライアント起動（スタンドアロン版：サーバーURL不要）
    try:
        client = UnifiedClient()
        client.run()
    except KeyboardInterrupt:
        print("\n[終了] プログラムを終了します")
    except Exception as e:
        print(f"[エラー] 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

