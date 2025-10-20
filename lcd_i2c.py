#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
I2C接続 1602 LCDディスプレイ制御
"""

import time
from datetime import datetime

try:
    import smbus2 as smbus
    I2C_AVAILABLE = True
except ImportError:
    try:
        import smbus
        I2C_AVAILABLE = True
    except ImportError:
        I2C_AVAILABLE = False
        print("[警告] smbus未インストール - LCD機能無効")


class LCD_I2C:
    """I2C 1602 LCDディスプレイ"""
    
    def __init__(self, addr=0x27, bus=1):
        self.available = I2C_AVAILABLE
        self.addr = addr
        
        if not self.available:
            return
        
        try:
            self.bus = smbus.SMBus(bus)
            self._init_lcd()
        except Exception as e:
            print(f"[警告] LCD初期化失敗: {e} - LCD機能無効")
            self.available = False
    
    def _write_byte(self, data):
        """バイト書き込み"""
        if not self.available:
            return
        
        try:
            self.bus.write_byte(self.addr, data)
        except:
            pass
    
    def _send(self, data, mode):
        """データ送信"""
        if not self.available:
            return
        
        try:
            high = mode | (data & 0xF0) | 0x08
            low = mode | ((data << 4) & 0xF0) | 0x08
            
            self._write_byte(high)
            self._write_byte(high | 0x04)
            time.sleep(0.001)
            self._write_byte(high & ~0x04)
            
            self._write_byte(low)
            self._write_byte(low | 0x04)
            time.sleep(0.001)
            self._write_byte(low & ~0x04)
        except:
            pass
    
    def _init_lcd(self):
        """LCD初期化"""
        if not self.available:
            return
        
        try:
            self._send(0x33, 0x00)
            self._send(0x32, 0x00)
            self._send(0x28, 0x00)
            self._send(0x0C, 0x00)
            self._send(0x06, 0x00)
            self._send(0x01, 0x00)
            time.sleep(0.2)
        except:
            self.available = False
    
    def clear(self):
        """画面クリア"""
        if not self.available:
            return
        
        try:
            self._send(0x01, 0x00)
            time.sleep(0.002)
        except:
            pass
    
    def set_cursor(self, row, col):
        """カーソル位置設定"""
        if not self.available:
            return
        
        try:
            addr = 0x80 if row == 0 else 0xC0
            self._send(addr + col, 0x00)
        except:
            pass
    
    def write(self, text):
        """テキスト書き込み"""
        if not self.available:
            return
        
        try:
            for char in text:
                self._send(ord(char), 0x01)
        except:
            pass
    
    def show(self, line1, line2):
        """2行表示"""
        if not self.available:
            return
        
        try:
            self.clear()
            self.set_cursor(0, 0)
            self.write(line1[:16])
            self.set_cursor(1, 0)
            self.write(line2[:16])
        except:
            pass
    
    def show_with_time(self, line2):
        """1行目:時刻、2行目:メッセージ"""
        if not self.available:
            return
        
        try:
            line1 = datetime.now().strftime("%Y/%m/%d %H:%M")
            self.show(line1, line2)
        except:
            pass

