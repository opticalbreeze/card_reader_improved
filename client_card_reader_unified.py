#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ICカードリーダー - ラズパイ統合版
メモリリーク対策版
"""

import sys
import os
import json
import time
import traceback
import gc
import psutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import threading
from collections import deque

# NFC関連
try:
    import nfc
    import nfc.clf
    NFC_AVAILABLE = True
except ImportError:
    NFC_AVAILABLE = False
    print("警告: nfcpyがインストールされていません")

# GPIO関連（ラズパイ用）
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("警告: RPi.GPIOがインストールされていません")

# LCD関連
try:
    from lcd_i2c import LCD_I2C
    LCD_AVAILABLE = True
except ImportError:
    LCD_AVAILABLE = False
    print("警告: LCD_I2Cモジュールが見つかりません")

# GPIO設定
try:
    from gpio_config import GPIOConfig
    GPIO_CONFIG_AVAILABLE = True
except ImportError:
    GPIO_CONFIG_AVAILABLE = False
    print("警告: gpio_configモジュールが見つかりません")

# 設定ファイル
CONFIG_FILE = "client_config.json"
CACHE_FILE = "attendance_cache.json"
LOG_FILE = "card_reader.log"

# デバッグ設定
DEBUG_MODE = True
MEMORY_CHECK_INTERVAL = 300  # 5分ごとにメモリチェック
MAX_MEMORY_MB = 200  # 最大メモリ使用量（MB）
MAX_CACHE_SIZE = 1000  # キャッシュの最大サイズ
MAX_LOG_HISTORY = 100  # ログ履歴の最大数

# ロギング設定
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class MemoryMonitor:
    """メモリ使用量を監視するクラス"""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.memory_history = deque(maxlen=MAX_LOG_HISTORY)
        self.peak_memory = 0
        
    def get_memory_mb(self) -> float:
        """現在のメモリ使用量をMBで取得"""
        try:
            memory_info = self.process.memory_info()
            return memory_info.rss / 1024 / 1024
        except Exception as e:
            logger.error(f"メモリ情報取得エラー: {e}")
            return 0.0
    
    def check_memory(self) -> Dict[str, Any]:
        """メモリ使用量をチェック"""
        current_memory = self.get_memory_mb()
        self.memory_history.append({
            'timestamp': datetime.now().isoformat(),
            'memory_mb': current_memory
        })
        
        if current_memory > self.peak_memory:
            self.peak_memory = current_memory
        
        return {
            'current_mb': current_memory,
            'peak_mb': self.peak_memory,
            'history_count': len(self.memory_history)
        }
    
    def force_gc(self):
        """ガベージコレクションを強制実行"""
        collected = gc.collect()
        logger.debug(f"ガベージコレクション実行: {collected}オブジェクト回収")
        return collected


class NFCReader:
    """NFCリーダー管理クラス（メモリリーク対策版）"""
    
    def __init__(self):
        self.clf: Optional[nfc.clf.ContactlessFrontend] = None
        self.is_connected = False
        self.connection_attempts = 0
        self.max_connection_attempts = 3
        self.last_connection_time = 0
        self.connection_interval = 5  # 接続試行間隔（秒）
        
    def connect(self) -> bool:
        """NFCリーダーに接続"""
        # 前回の接続を確実にクローズ
        self.disconnect()
        
        # 接続間隔チェック
        current_time = time.time()
        if current_time - self.last_connection_time < self.connection_interval:
            time.sleep(self.connection_interval - (current_time - self.last_connection_time))
        
        try:
            logger.info("NFCリーダーに接続中...")
            self.clf = nfc.ContactlessFrontend('usb')
            
            if self.clf is None:
                logger.error("NFCリーダーが見つかりません")
                return False
            
            self.is_connected = True
            self.connection_attempts = 0
            self.last_connection_time = time.time()
            logger.info("NFCリーダーに接続しました")
            return True
            
        except Exception as e:
            self.connection_attempts += 1
            logger.error(f"NFCリーダー接続エラー (試行 {self.connection_attempts}/{self.max_connection_attempts}): {e}")
            logger.debug(traceback.format_exc())
            self.is_connected = False
            return False
    
    def disconnect(self):
        """NFCリーダーから切断"""
        if self.clf is not None:
            try:
                logger.debug("NFCリーダーを切断中...")
                self.clf.close()
                logger.debug("NFCリーダーを切断しました")
            except Exception as e:
                logger.error(f"NFCリーダー切断エラー: {e}")
            finally:
                self.clf = None
                self.is_connected = False
    
    def check_connection(self) -> bool:
        """NFCリーダーの接続状態を確認"""
        if self.clf is None:
            return False
        try:
            # 接続状態を確認（簡単なテスト）
            return self.is_connected
        except Exception as e:
            logger.debug(f"接続確認エラー: {e}")
            return False
    
    def read_card(self, timeout: float = 0.5) -> Optional[str]:
        """カードを読み取る"""
        if not self.is_connected or self.clf is None:
            logger.warning("NFCリーダーが接続されていません")
            return None
        
        try:
            # カードを検出
            tag = self.clf.connect(rdwr={'on-connect': lambda tag: False}, timeout=timeout)
            
            if tag is None:
                return None
            
            # IDmを取得（FeliCa）
            if hasattr(tag, 'idm'):
                card_id = tag.idm.hex().upper()
                logger.debug(f"カード検出: {card_id}")
                return card_id
            
            # UIDを取得（Mifare等）
            if hasattr(tag, 'identifier'):
                card_id = tag.identifier.hex().upper()
                logger.debug(f"カード検出: {card_id}")
                return card_id
            
            logger.warning("カードIDを取得できませんでした")
            return None
            
        except nfc.clf.TimeoutError:
            # タイムアウトは正常な動作
            return None
        except nfc.clf.CommunicationError as e:
            logger.warning(f"NFC通信エラー: {e} - 接続をリセットします")
            self.disconnect()
            return None
        except Exception as e:
            logger.error(f"カード読み取りエラー: {e}")
            logger.debug(traceback.format_exc())
            # エラーが発生した場合、接続をリセット
            self.disconnect()
            return None
    
    def __enter__(self):
        """コンテキストマネージャー: エントリ"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー: エグジット（確実にクローズ）"""
        self.disconnect()
        return False


class AttendanceCache:
    """出勤記録キャッシュ管理（メモリリーク対策版）"""
    
    def __init__(self, cache_file: str = CACHE_FILE):
        self.cache_file = cache_file
        self.cache: deque = deque(maxlen=MAX_CACHE_SIZE)  # 最大サイズ制限
        self.lock = threading.Lock()
        self.load_cache()
    
    def load_cache(self):
        """キャッシュをファイルから読み込み"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.cache = deque(data[:MAX_CACHE_SIZE], maxlen=MAX_CACHE_SIZE)
                logger.info(f"キャッシュを読み込みました: {len(self.cache)}件")
        except Exception as e:
            logger.error(f"キャッシュ読み込みエラー: {e}")
            self.cache = deque(maxlen=MAX_CACHE_SIZE)
    
    def save_cache(self):
        """キャッシュをファイルに保存"""
        try:
            with self.lock:
                with open(self.cache_file, 'w', encoding='utf-8') as f:
                    json.dump(list(self.cache), f, ensure_ascii=False, indent=2)
                logger.debug(f"キャッシュを保存しました: {len(self.cache)}件")
        except Exception as e:
            logger.error(f"キャッシュ保存エラー: {e}")
    
    def add(self, card_id: str, timestamp: str):
        """キャッシュに追加"""
        with self.lock:
            self.cache.append({
                'card_id': card_id,
                'timestamp': timestamp
            })
            # 定期的に保存（100件ごと）
            if len(self.cache) % 100 == 0:
                self.save_cache()
    
    def get_all(self) -> list:
        """全キャッシュを取得"""
        with self.lock:
            return list(self.cache)
    
    def clear(self):
        """キャッシュをクリア"""
        with self.lock:
            self.cache.clear()
            self.save_cache()


class AttendanceClient:
    """出勤管理クライアント（メモリリーク対策版）"""
    
    def __init__(self, config_file: str = CONFIG_FILE):
        self.config = self.load_config(config_file)
        self.nfc_reader = NFCReader()
        self.cache = AttendanceCache()
        self.memory_monitor = MemoryMonitor()
        self.last_memory_check = 0
        self.last_card_id = None
        self.last_card_time = 0
        self.card_interval = 2  # 同じカードの読み取り間隔（秒）
        self.read_count = 0
        self.error_count = 0
        self.running = False
        self.last_card_detection_time = 0  # 最後にカードが検出された時刻
        self.last_heartbeat_time = time.time()  # 最後のハートビート時刻
        self.connection_check_interval = 60  # 接続チェック間隔（秒）
        self.last_connection_check = time.time()  # 最後の接続チェック時刻
        self.no_card_detection_timeout = 300  # カードが検出されない場合のタイムアウト（秒）
        
        # GPIO初期化
        if GPIO_AVAILABLE and GPIO_CONFIG_AVAILABLE:
            try:
                self.gpio_config = GPIOConfig()
                self.init_gpio()
            except Exception as e:
                logger.error(f"GPIO初期化エラー: {e}")
                self.gpio_config = None
        else:
            self.gpio_config = None
        
        # LCD初期化
        if LCD_AVAILABLE:
            try:
                self.lcd = LCD_I2C()
                # 初期化メッセージ（ASCII文字のみ）
                self.lcd.display("Card Reader", "Initializing...")
            except Exception as e:
                logger.error(f"LCD初期化エラー: {e}")
                logger.debug(traceback.format_exc())
                self.lcd = None
        else:
            self.lcd = None
    
    def load_config(self, config_file: str) -> Dict[str, Any]:
        """設定ファイルを読み込み"""
        default_config = {
            "server_url": "http://localhost:5000",
            "device_id": "raspberry_pi_01",
            "retry_interval": 600
        }
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    default_config.update(config)
                logger.info(f"設定ファイルを読み込みました: {config_file}")
            else:
                logger.warning(f"設定ファイルが見つかりません: {config_file}")
                # デフォルト設定で作成
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, ensure_ascii=False, indent=2)
                logger.info(f"デフォルト設定ファイルを作成しました: {config_file}")
        except Exception as e:
            logger.error(f"設定ファイル読み込みエラー: {e}")
        
        return default_config
    
    def init_gpio(self):
        """GPIOを初期化"""
        if not GPIO_AVAILABLE or self.gpio_config is None:
            return
        
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # LED設定
            if hasattr(self.gpio_config, 'led_red'):
                GPIO.setup(self.gpio_config.led_red, GPIO.OUT)
            if hasattr(self.gpio_config, 'led_green'):
                GPIO.setup(self.gpio_config.led_green, GPIO.OUT)
            if hasattr(self.gpio_config, 'led_blue'):
                GPIO.setup(self.gpio_config.led_blue, GPIO.OUT)
            
            # ブザー設定
            if hasattr(self.gpio_config, 'buzzer'):
                GPIO.setup(self.gpio_config.buzzer, GPIO.OUT)
            
            logger.info("GPIOを初期化しました")
        except Exception as e:
            logger.error(f"GPIO初期化エラー: {e}")
    
    def cleanup_gpio(self):
        """GPIOをクリーンアップ"""
        if GPIO_AVAILABLE:
            try:
                GPIO.cleanup()
                logger.debug("GPIOをクリーンアップしました")
            except Exception as e:
                logger.error(f"GPIOクリーンアップエラー: {e}")
    
    def set_led(self, color: str, state: bool):
        """LEDを制御"""
        if not GPIO_AVAILABLE or self.gpio_config is None:
            return
        
        try:
            pin = None
            if color == 'red' and hasattr(self.gpio_config, 'led_red'):
                pin = self.gpio_config.led_red
            elif color == 'green' and hasattr(self.gpio_config, 'led_green'):
                pin = self.gpio_config.led_green
            elif color == 'blue' and hasattr(self.gpio_config, 'led_blue'):
                pin = self.gpio_config.led_blue
            
            if pin is not None:
                GPIO.output(pin, GPIO.HIGH if state else GPIO.LOW)
        except Exception as e:
            logger.error(f"LED制御エラー: {e}")
    
    def beep(self, duration: float = 0.1):
        """ブザーを鳴らす"""
        if not GPIO_AVAILABLE or self.gpio_config is None:
            return
        
        try:
            if hasattr(self.gpio_config, 'buzzer'):
                GPIO.output(self.gpio_config.buzzer, GPIO.HIGH)
                time.sleep(duration)
                GPIO.output(self.gpio_config.buzzer, GPIO.LOW)
        except Exception as e:
            logger.error(f"ブザー制御エラー: {e}")
    
    def sanitize_lcd_text(self, text: str, max_length: int = 16) -> str:
        """LCD表示用に文字列をサニタイズ（ASCII互換文字のみ）"""
        if not text:
            return " " * max_length  # 空文字列の場合は空白で埋める
        
        # 日本語や特殊文字をASCII互換文字に変換
        result = ""
        for char in text:
            # ASCII文字（0x20-0x7E）はそのまま
            if 0x20 <= ord(char) <= 0x7E:
                result += char
            # 改行やタブは空白に変換
            elif char in ['\n', '\r', '\t']:
                result += ' '
            # その他の文字は空白に変換
            else:
                result += ' '
        
        # 先頭・末尾の空白を削除
        result = result.strip()
        
        # 最大長に制限
        if len(result) > max_length:
            result = result[:max_length]
        
        # 空文字列の場合は空白を返す
        if not result:
            result = " " * max_length
        
        # 必ずmax_length文字になるように空白でパディング（前の文字列の残りを消すため）
        result = result.ljust(max_length, ' ')
        
        return result
    
    def clear_lcd(self):
        """LCD画面をクリア"""
        if self.lcd is not None:
            try:
                # LCD_I2Cモジュールにclearメソッドがある場合
                if hasattr(self.lcd, 'clear'):
                    self.lcd.clear()
                # clearメソッドがない場合、空白で埋める
                else:
                    self.lcd.display(" " * 16, " " * 16)
            except Exception as e:
                logger.debug(f"LCDクリアエラー（無視）: {e}")
    
    def update_lcd(self, line1: str, line2: str):
        """LCDを更新（文字化け対策版・バッファクリア対応）"""
        if self.lcd is not None:
            try:
                # 文字列をサニタイズ（ASCII互換文字のみ）
                safe_line1 = self.sanitize_lcd_text(line1, 16)
                safe_line2 = self.sanitize_lcd_text(line2, 16)
                
                # デバッグログ（文字化けが発生している場合の確認用）
                if DEBUG_MODE:
                    logger.debug(f"LCD表示: '{safe_line1}' / '{safe_line2}' (長さ: {len(safe_line1)}/{len(safe_line2)})")
                
                # LCDに表示（必ず16文字でパディングされているので、前の文字列の残りは消える）
                self.lcd.display(safe_line1, safe_line2)
                
            except Exception as e:
                logger.error(f"LCD更新エラー: {e}")
                logger.debug(traceback.format_exc())
                # エラーが発生した場合、LCDをクリアして再試行
                try:
                    self.clear_lcd()
                    time.sleep(0.1)
                    self.lcd.display(safe_line1, safe_line2)
                except Exception as e2:
                    logger.error(f"LCD再試行エラー: {e2}")
    
    def send_attendance(self, card_id: str, timestamp: str) -> bool:
        """サーバーに打刻データを送信"""
        import requests
        
        url = f"{self.config['server_url']}/api/attendance"
        data = {
            'card_id': card_id,
            'timestamp': timestamp,
            'device_id': self.config.get('device_id', 'raspberry_pi_01')
        }
        
        try:
            response = requests.post(url, json=data, timeout=5)
            if response.status_code == 200:
                logger.info(f"打刻データを送信しました: {card_id}")
                return True
            else:
                logger.warning(f"サーバー応答エラー: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"サーバー送信エラー: {e}")
            return False
    
    def process_cache(self):
        """キャッシュされたデータを送信"""
        cache_data = self.cache.get_all()
        if not cache_data:
            return
        
        logger.info(f"キャッシュされたデータを送信します: {len(cache_data)}件")
        success_count = 0
        
        for item in cache_data:
            if self.send_attendance(item['card_id'], item['timestamp']):
                success_count += 1
                time.sleep(0.1)  # サーバー負荷軽減
        
        # 送信成功した分だけキャッシュから削除
        if success_count > 0:
            # 成功した分だけ先頭から削除
            for _ in range(success_count):
                if self.cache.cache:
                    self.cache.cache.popleft()
            self.cache.save_cache()
            logger.info(f"キャッシュ送信完了: {success_count}件送信")
    
    def check_memory_and_cleanup(self):
        """メモリをチェックして必要に応じてクリーンアップ"""
        current_time = time.time()
        
        # 定期的にメモリチェック
        if current_time - self.last_memory_check >= MEMORY_CHECK_INTERVAL:
            self.last_memory_check = current_time
            
            memory_info = self.memory_monitor.check_memory()
            logger.info(f"メモリ使用量: {memory_info['current_mb']:.2f}MB "
                       f"(ピーク: {memory_info['peak_mb']:.2f}MB)")
            
            # メモリ使用量が上限を超えた場合
            if memory_info['current_mb'] > MAX_MEMORY_MB:
                logger.warning(f"メモリ使用量が上限を超えました: {memory_info['current_mb']:.2f}MB")
                # ガベージコレクションを強制実行
                collected = self.memory_monitor.force_gc()
                logger.info(f"ガベージコレクション実行: {collected}オブジェクト回収")
                
                # NFCリーダーを再接続（リソースをリセット）
                if self.nfc_reader.is_connected:
                    logger.info("メモリリーク対策: NFCリーダーを再接続します")
                    self.nfc_reader.disconnect()
                    time.sleep(1)
                    self.nfc_reader.connect()
    
    def read_card_loop(self):
        """カード読み取りループ（メモリリーク対策版・自動復旧機能強化）"""
        logger.info("カード読み取りループを開始します")
        self.running = True
        
        # NFCリーダーに接続
        if not self.nfc_reader.connect():
            logger.error("NFCリーダーに接続できませんでした")
            return
        
        self.set_led('blue', True)  # 待機中は青LED
        self.update_lcd("Card Reader", "Ready")
        
        consecutive_errors = 0
        max_consecutive_errors = 10
        loop_count = 0
        start_time = time.time()
        
        try:
            while self.running:
                try:
                    current_time = time.time()
                    loop_count += 1
                    
                    # メモリチェックとクリーンアップ
                    self.check_memory_and_cleanup()
                    
                    # ハートビート（5分ごと）
                    if current_time - self.last_heartbeat_time >= 300:
                        self.last_heartbeat_time = current_time
                        uptime = int(current_time - start_time)
                        logger.info(f"[ハートビート] 動作中 - 稼働時間: {uptime}秒, "
                                   f"読み取り回数: {self.read_count}, "
                                   f"エラー回数: {self.error_count}, "
                                   f"ループ回数: {loop_count}")
                    
                    # NFCリーダーの接続状態を定期的にチェック（1分ごと）
                    if current_time - self.last_connection_check >= self.connection_check_interval:
                        self.last_connection_check = current_time
                        if not self.nfc_reader.check_connection() or not self.nfc_reader.is_connected:
                            logger.warning("NFCリーダーの接続が切れています。再接続します")
                            self.nfc_reader.disconnect()
                            time.sleep(2)
                            if not self.nfc_reader.connect():
                                logger.error("NFCリーダーの再接続に失敗しました。再試行します...")
                                time.sleep(5)
                                if not self.nfc_reader.connect():
                                    logger.error("NFCリーダーの再接続に2回失敗しました")
                                    break
                            else:
                                logger.info("NFCリーダーを再接続しました")
                                self.set_led('blue', True)
                                # LCDをクリアしてから表示（文字化け防止）
                                self.clear_lcd()
                                time.sleep(0.05)
                                self.update_lcd("Card Reader", "Reconnected")
                    
                    # カードが長時間検出されない場合、接続をリセット（5分ごと）
                    if (self.last_card_detection_time > 0 and 
                        current_time - self.last_card_detection_time >= self.no_card_detection_timeout):
                        logger.info("長時間カードが検出されていません。接続をリセットします")
                        self.nfc_reader.disconnect()
                        time.sleep(1)
                        if not self.nfc_reader.connect():
                            logger.error("接続リセット後の再接続に失敗しました")
                            break
                        self.last_card_detection_time = current_time  # リセット
                    
                    # カードを読み取る
                    card_id = self.nfc_reader.read_card(timeout=0.5)
                    
                    if card_id is not None:
                        # 同じカードの連続読み取りを防止
                        if (card_id == self.last_card_id and 
                            current_time - self.last_card_time < self.card_interval):
                            time.sleep(0.1)
                            continue
                        
                        self.last_card_id = card_id
                        self.last_card_time = current_time
                        self.last_card_detection_time = current_time  # カード検出時刻を更新
                        self.read_count += 1
                        consecutive_errors = 0
                        
                        timestamp = datetime.now().isoformat()
                        logger.info(f"カード検出: {card_id} (読み取り回数: {self.read_count})")
                        
                        # LEDとブザーでフィードバック
                        self.set_led('green', True)
                        self.beep(0.1)
                        # カードIDを表示（16進数のみなので文字化けしない）
                        self.update_lcd("Card Detected", card_id[:16])
                        
                        # サーバーに送信
                        if self.send_attendance(card_id, timestamp):
                            self.set_led('green', False)
                            time.sleep(0.5)
                        else:
                            # 送信失敗時はキャッシュに保存
                            self.cache.add(card_id, timestamp)
                            self.set_led('red', True)
                            time.sleep(0.5)
                            self.set_led('red', False)
                        
                        # キャッシュ処理（定期的に）
                        if self.read_count % 10 == 0:
                            self.process_cache()
                        
                        # 状態表示をリセット
                        time.sleep(1)
                        self.set_led('blue', True)
                        # LCDをクリアしてから表示（文字化け防止）
                        self.clear_lcd()
                        time.sleep(0.05)  # クリア処理の待機時間
                        self.update_lcd("Card Reader", "Ready")
                    
                    else:
                        # カードが検出されない場合
                        time.sleep(0.1)
                    
                    # エラーカウントをリセット
                    consecutive_errors = 0
                    
                except KeyboardInterrupt:
                    logger.info("ユーザーによる中断")
                    break
                except Exception as e:
                    self.error_count += 1
                    consecutive_errors += 1
                    logger.error(f"ループ内エラー (エラー回数: {self.error_count}, 連続エラー: {consecutive_errors}): {e}")
                    logger.debug(traceback.format_exc())
                    
                    # 連続エラーが多すぎる場合、NFCリーダーを再接続
                    if consecutive_errors >= max_consecutive_errors:
                        logger.warning(f"連続エラーが{max_consecutive_errors}回発生しました。NFCリーダーを再接続します")
                        self.nfc_reader.disconnect()
                        time.sleep(2)
                        if not self.nfc_reader.connect():
                            logger.error("NFCリーダーの再接続に失敗しました。5秒後に再試行します...")
                            time.sleep(5)
                            if not self.nfc_reader.connect():
                                logger.error("NFCリーダーの再接続に2回失敗しました")
                                break
                        else:
                            logger.info("NFCリーダーを再接続しました")
                            consecutive_errors = 0
                            self.set_led('blue', True)
                            # LCDをクリアしてから表示（文字化け防止）
                            self.clear_lcd()
                            time.sleep(0.05)
                            self.update_lcd("Card Reader", "Reconnected")
                    
                    time.sleep(1)
        
        finally:
            # クリーンアップ処理
            logger.info("クリーンアップ処理を開始します")
            self.running = False
            self.nfc_reader.disconnect()
            self.cache.save_cache()
            self.cleanup_gpio()
            
            # 最終メモリチェック
            memory_info = self.memory_monitor.check_memory()
            logger.info(f"最終メモリ使用量: {memory_info['current_mb']:.2f}MB "
                       f"(ピーク: {memory_info['peak_mb']:.2f}MB)")
            logger.info(f"読み取り回数: {self.read_count}, エラー回数: {self.error_count}")
    
    def run(self):
        """メイン実行"""
        logger.info("=" * 50)
        logger.info("ICカードリーダー - ラズパイ統合版（メモリリーク対策版）")
        logger.info("=" * 50)
        
        # 初期メモリチェック
        memory_info = self.memory_monitor.check_memory()
        logger.info(f"初期メモリ使用量: {memory_info['current_mb']:.2f}MB")
        
        # キャッシュ処理（起動時）
        self.process_cache()
        
        # カード読み取りループ
        try:
            self.read_card_loop()
        except KeyboardInterrupt:
            logger.info("プログラムを終了します")
        except Exception as e:
            logger.error(f"予期しないエラー: {e}")
            logger.debug(traceback.format_exc())
        finally:
            logger.info("プログラムを終了しました")


def main():
    """メイン関数"""
    if not NFC_AVAILABLE:
        print("エラー: nfcpyがインストールされていません")
        print("インストール方法: pip3 install nfcpy")
        sys.exit(1)
    
    client = AttendanceClient()
    client.run()


if __name__ == "__main__":
    main()

