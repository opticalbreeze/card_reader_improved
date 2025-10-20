#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
サーバー接続監視モジュール
"""

import time
import threading
import requests
from datetime import datetime


class ServerMonitor:
    """サーバー接続監視"""
    
    def __init__(self, server_url, lcd=None, gpio=None):
        self.server = server_url
        self.lcd = lcd
        self.gpio = gpio
        self.connected = False
        self.retry_count = 0
        self.max_retries = 2
        self.check_interval = 3600  # 1時間
        self.running = True
        
        # 監視スレッド開始
        threading.Thread(target=self._monitor_worker, daemon=True).start()
    
    def check_connection(self):
        """接続確認"""
        try:
            response = requests.get(f"{self.server}/api/health", timeout=5)
            if response.status_code == 200:
                self.connected = True
                self.retry_count = 0
                return True
            else:
                self.connected = False
                return False
        except Exception:
            self.connected = False
            return False
    
    def _monitor_worker(self):
        """監視ワーカー"""
        while self.running:
            # 接続確認
            if self.check_connection():
                if self.lcd:
                    self.lcd.show_with_time("サーバー カクニンズミ")
                    time.sleep(2)
                    self.lcd.show_with_time("カード ヲ タッチ")
                
                if self.gpio:
                    self.gpio.led("green")
            else:
                # 再接続試行
                for attempt in range(self.max_retries):
                    print(f"[再接続] 試行 {attempt + 1}/{self.max_retries}")
                    
                    if self.lcd:
                        self.lcd.show_with_time(f"サイセツゾク{attempt+1}/{self.max_retries}")
                    
                    time.sleep(5)
                    
                    if self.check_connection():
                        print("[OK] 再接続成功")
                        if self.lcd:
                            self.lcd.show_with_time("サーバー セツゾクOK")
                            time.sleep(2)
                        if self.gpio:
                            self.gpio.led("green")
                        break
                else:
                    # 再接続失敗
                    print("[NG] 再接続失敗 - 1時間後に再試行")
                    if self.lcd:
                        self.lcd.show_with_time("サーバー セツゾクNG")
                    
                    if self.gpio:
                        # オレンジ点滅スレッド開始
                        self._blink_orange()
            
            # 1時間待機
            time.sleep(self.check_interval)
    
    def _blink_orange(self):
        """オレンジ点滅"""
        def blink():
            while not self.connected and self.running:
                if self.gpio:
                    self.gpio.led("orange")
                time.sleep(0.5)
                if self.gpio:
                    self.gpio.led("off")
                time.sleep(0.5)
        
        threading.Thread(target=blink, daemon=True).start()
    
    def stop(self):
        """停止"""
        self.running = False

