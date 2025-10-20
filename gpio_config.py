#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPIO設定ファイル
"""

# GPIO設定
BUZZER_PIN = 18      # 圧電ブザー
LED_RED_PIN = 13     # 赤LED
LED_GREEN_PIN = 19   # 緑LED
LED_BLUE_PIN = 26    # 青LED

# ブザーパターン設定（duration, frequency）
BUZZER_PATTERNS = {
    "startup": [(0.2, 1000), (0.1, 1000), (0.2, 1000)],     # 起動時：長-短-長
    "connect": [(0.1, 1500), (0.1, 1500), (0.1, 1500)],     # 接続時：短-短-短
    "card_read": [(0.05, 2000)],                            # カード読み込み：短
    "success": [(0.1, 2500), (0.05, 2500), (0.1, 2500)],   # 成功：短-短-短（高音）
    "failure": [(0.3, 800), (0.1, 800), (0.3, 800)]        # 失敗：長-短-長（低音）
}

# LED色設定（R, G, B）
LED_COLORS = {
    "off": (0, 0, 0),
    "red": (100, 0, 0),
    "green": (0, 100, 0),
    "blue": (0, 0, 100),
    "orange": (100, 50, 0),
    "white": (100, 100, 100)
}

# I2C LCD設定
LCD_I2C_ADDR = 0x27  # LCD I2Cアドレス
LCD_I2C_BUS = 1      # I2Cバス番号

