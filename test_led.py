#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LED動作テストスクリプト
GPIO接続とLED制御をテストする
"""

import sys
import time

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("[エラー] RPi.GPIOがインストールされていません")
    print("  pip install RPi.GPIO")
    sys.exit(1)

# GPIO設定
LED_RED_PIN = 13
LED_GREEN_PIN = 19
LED_BLUE_PIN = 26

LED_COLORS = {
    "off": (0, 0, 0),
    "red": (100, 0, 0),
    "green": (0, 100, 0),
    "blue": (0, 0, 100),
    "orange": (100, 50, 0),
    "white": (100, 100, 100)
}

def test_led():
    """LED動作テスト"""
    print("="*60)
    print("LED動作テスト")
    print("="*60)
    print()
    
    try:
        # GPIO初期化
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup([LED_RED_PIN, LED_GREEN_PIN, LED_BLUE_PIN], GPIO.OUT)
        
        # PWM初期化
        print("[情報] PWMを初期化しています...")
        pwms = [
            GPIO.PWM(LED_RED_PIN, 1000),
            GPIO.PWM(LED_GREEN_PIN, 1000),
            GPIO.PWM(LED_BLUE_PIN, 1000)
        ]
        
        for pwm in pwms:
            pwm.start(0)
        
        print("[OK] PWM初期化成功")
        print()
        
        # 各色をテスト
        colors = ["red", "green", "blue", "orange", "white", "off"]
        
        for color in colors:
            r, g, b = LED_COLORS.get(color, (0, 0, 0))
            print(f"[テスト] {color:8s} - R={r:3d} G={g:3d} B={b:3d}")
            
            try:
                pwms[0].ChangeDutyCycle(r)
                pwms[1].ChangeDutyCycle(g)
                pwms[2].ChangeDutyCycle(b)
                time.sleep(2)
            except Exception as e:
                print(f"  [エラー] {e}")
        
        # クリーンアップ
        print()
        print("[情報] クリーンアップ中...")
        for pwm in pwms:
            pwm.stop()
        GPIO.cleanup()
        print("[OK] テスト完了")
        
    except Exception as e:
        print(f"[エラー] GPIO初期化失敗: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_led()

