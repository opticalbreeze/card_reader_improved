#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
I2C接続 1602 LCDディスプレイ制御
16文字×2行のLCDを制御

対応LCD:
- HD44780互換のI2C LCDモジュール
- PCF8574T I2Cバックパック搭載モデル

使用方法:
    from lcd_i2c import LCD_I2C
    
    lcd = LCD_I2C(addr=0x27, bus=1)
    lcd.show("Hello", "World!")
"""

import time
import sys
from datetime import datetime

# smbus2またはsmbusをインポート
try:
    import smbus2 as smbus
    I2C_AVAILABLE = True
except ImportError:
    try:
        import smbus
        I2C_AVAILABLE = True
    except ImportError:
        I2C_AVAILABLE = False
        print("[警告] smbus/smbus2未インストール - LCD機能は無効です")
        print("        インストール: pip install smbus2")


# ============================================================================
# LCDコマンド定数
# ============================================================================

# LCDモード
LCD_MODE_COMMAND = 0x00
LCD_MODE_DATA = 0x01

# LCDコントロールビット
LCD_BACKLIGHT_ON = 0x08
LCD_BACKLIGHT_OFF = 0x00
LCD_ENABLE = 0x04

# LCD初期化コマンド
LCD_INIT_4BIT = 0x28    # 4ビットモード、2行表示、5x8ドット
LCD_DISPLAY_ON = 0x0C   # ディスプレイON、カーソルOFF、ブリンクOFF
LCD_ENTRY_MODE = 0x06   # カーソル自動移動、シフトなし
LCD_CLEAR = 0x01        # 画面クリア

# カーソル位置
LCD_LINE1 = 0x80
LCD_LINE2 = 0xC0

# CGRAMアドレス（カスタム文字用）
LCD_CGRAM_ADDR = 0x40


# ============================================================================
# 文字コード変換関数
# ============================================================================

def _char_to_lcd_code(char):
    """
    文字をHD44780互換LCDの文字コードに変換
    
    HD44780は以下の文字セットをサポート:
    - ASCII文字（0x20-0x7F）
    - カタカナ（0xA0-0xDF）
    
    Args:
        char (str): 変換する文字（1文字）
    
    Returns:
        int: LCD文字コード（0x20-0x7F または 0xA0-0xDF）
    """
    code = ord(char)
    
    # ASCII文字（0x20-0x7F）はそのまま使用
    if 0x20 <= code <= 0x7F:
        return code
    
    # 制御文字（0x00-0x1F）はスペースに変換
    if code < 0x20:
        return 0x20
    
    # ASCII文字以外はスペースに変換
    return 0x20


def _text_to_lcd_codes(text):
    """
    テキストをLCD文字コードのリストに変換
    
    Args:
        text (str): 変換するテキスト
    
    Returns:
        list: LCD文字コードのリスト（Noneはスキップ）
    """
    codes = []
    for char in text:
        code = _char_to_lcd_code(char)
        if code is not None:
            codes.append(code)
    return codes


# ============================================================================
# LCD制御クラス
# ============================================================================

class LCD_I2C:
    """
    I2C 1602 LCDディスプレイ制御クラス
    HD44780互換のI2C LCDモジュールを制御
    """
    
    def __init__(self, addr=0x27, bus=1, backlight=True):
        """
        LCDを初期化
        
        Args:
            addr (int): I2Cアドレス（通常は0x27または0x3F）
            bus (int): I2Cバス番号（Raspberry Pi 3/4は1、初期モデルは0）
            backlight (bool): バックライトON/OFF（デフォルト: True）
        """
        self.available = I2C_AVAILABLE
        self.addr = addr
        self.backlight_enabled = backlight
        
        if not self.available:
            return
        
        try:
            self.bus = smbus.SMBus(bus)
            self._init_lcd()
        except Exception as e:
            print(f"[警告] LCD初期化失敗: {e}")
            print(f"        I2Cアドレス 0x{addr:02X} が見つかりません")
            self.available = False
    
    def _write_byte(self, data):
        """
        I2C経由で1バイト書き込み
        
        Args:
            data (int): 書き込むデータ
        """
        if not self.available:
            return
        
        try:
            self.bus.write_byte(self.addr, data)
        except Exception:
            pass
    
    def _send(self, data, mode):
        """
        4ビットモードでデータを送信
        
        Args:
            data (int): 送信するデータ（8ビット）
            mode (int): モード（LCD_MODE_COMMAND または LCD_MODE_DATA）
        """
        if not self.available:
            return
        
        try:
            # バックライト制御ビットを設定
            backlight_bit = LCD_BACKLIGHT_ON if self.backlight_enabled else LCD_BACKLIGHT_OFF
            
            # 上位4ビット送信
            high = mode | (data & 0xF0) | backlight_bit
            self._write_byte(high)
            self._write_byte(high | LCD_ENABLE)
            time.sleep(0.001)
            self._write_byte(high & ~LCD_ENABLE)
            
            # 下位4ビット送信
            low = mode | ((data << 4) & 0xF0) | backlight_bit
            self._write_byte(low)
            self._write_byte(low | LCD_ENABLE)
            time.sleep(0.001)
            self._write_byte(low & ~LCD_ENABLE)
        except Exception:
            pass
    
    def _init_lcd(self):
        """
        LCDを初期化（4ビットモード）
        """
        if not self.available:
            return
        
        try:
            # 初期化シーケンス
            self._send(0x33, LCD_MODE_COMMAND)  # 8ビットモードで初期化
            self._send(0x32, LCD_MODE_COMMAND)  # 4ビットモードに切り替え
            self._send(LCD_INIT_4BIT, LCD_MODE_COMMAND)  # 4ビット、2行、5x8
            self._send(LCD_DISPLAY_ON, LCD_MODE_COMMAND)  # ディスプレイON
            self._send(LCD_ENTRY_MODE, LCD_MODE_COMMAND)  # エントリーモード設定
            self._send(LCD_CLEAR, LCD_MODE_COMMAND)  # 画面クリア
            time.sleep(0.2)
        except Exception:
            self.available = False
    
    def clear(self):
        """
        画面をクリア
        """
        if not self.available:
            return
        
        try:
            self._send(LCD_CLEAR, LCD_MODE_COMMAND)
            time.sleep(0.002)
        except Exception:
            pass
    
    def set_cursor(self, row, col):
        """
        カーソル位置を設定
        
        Args:
            row (int): 行（0または1）
            col (int): 列（0-15）
        """
        if not self.available:
            return
        
        try:
            addr = LCD_LINE1 if row == 0 else LCD_LINE2
            self._send(addr + col, LCD_MODE_COMMAND)
        except Exception:
            pass
    
    def write(self, text):
        """
        テキストを書き込み（現在のカーソル位置から）
        日本語文字は自動的にASCII文字に変換される
        
        Args:
            text (str): 表示するテキスト
        """
        if not self.available:
            return
        
        try:
            codes = _text_to_lcd_codes(text)
            for code in codes:
                self._send(code, LCD_MODE_DATA)
        except Exception:
            pass
    
    def show(self, line1, line2):
        """
        2行のテキストを表示
        
        Args:
            line1 (str): 1行目のテキスト（最大16文字）
            line2 (str): 2行目のテキスト（最大16文字）
        """
        if not self.available:
            return
        
        try:
            self.clear()
            self.set_cursor(0, 0)
            self.write(line1[:16])  # 16文字まで
            self.set_cursor(1, 0)
            self.write(line2[:16])  # 16文字まで
        except Exception:
            pass
    
    def show_with_time(self, line2):
        """
        1行目に現在時刻、2行目にメッセージを表示
        
        Args:
            line2 (str): 2行目のテキスト（最大16文字）
        """
        if not self.available:
            return
        
        try:
            # 1行目: 日時（例: "2025/10/20 15:30"）
            line1 = datetime.now().strftime("%Y/%m/%d %H:%M")
            self.show(line1, line2)
        except Exception:
            pass
    
    def backlight_on(self):
        """バックライトをON"""
        if not self.available:
            return
        
        self.backlight_enabled = True
        try:
            self._write_byte(LCD_BACKLIGHT_ON)
        except Exception:
            pass
    
    def backlight_off(self):
        """バックライトをOFF"""
        if not self.available:
            return
        
        self.backlight_enabled = False
        try:
            self._write_byte(LCD_BACKLIGHT_OFF)
        except Exception:
            pass


# ============================================================================
# テスト
# ============================================================================

if __name__ == "__main__":
    """
    LCD動作テスト
    使用方法: python lcd_i2c.py
    """
    if not I2C_AVAILABLE:
        print("[エラー] smbus/smbus2がインストールされていません")
        print("  pip install smbus2")
        sys.exit(1)
    
    print("[情報] LCDを初期化しています...")
    lcd = LCD_I2C(addr=0x27, bus=1)
    
    if not lcd.available:
        print("[エラー] LCD初期化に失敗しました")
        print("  - I2Cアドレスを確認してください（0x27 または 0x3F）")
        sys.exit(1)
    
    print("[OK] LCD初期化成功")
    
    try:
        # 基本テスト
        lcd.show("Hello", "World!")
        time.sleep(2)
        lcd.show_with_time("Test")
        time.sleep(2)
        lcd.clear()
        print("[OK] テスト完了")
        
    except KeyboardInterrupt:
        print("\n[終了] テストを中断しました")
        lcd.clear()
    except Exception as e:
        print(f"\n[エラー] {e}")

