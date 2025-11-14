# LEDランプ接続ガイド

## 📋 概要

このガイドでは、Raspberry PiにRGB LEDを接続する方法を説明します。

## 🔌 GPIOピン設定

現在の設定（`gpio_config.py`）:

- **赤LED**: GPIO 13 (BCM)
- **緑LED**: GPIO 19 (BCM)
- **青LED**: GPIO 26 (BCM)
- **ブザー**: GPIO 18 (BCM) ✅ 動作確認済み

## 🔴 RGB LEDの接続方法

### 必要な部品

- RGB LED（カソードコモンまたはアノードコモン）
- 抵抗 220Ω × 3本（各色用）
- ジャンパーワイヤー
- ブレッドボード（推奨）

### 接続図

#### Raspberry Pi GPIOピン配置（BCMモード）

```
       3.3V  [1] [2]  5V
GPIO2  SDA   [3] [4]  5V
GPIO3  SCL   [5] [6]  GND
GPIO4        [7] [8]  GPIO14
      GND    [9] [10] GPIO15
GPIO17       [11] [12] GPIO18 ← ブザー
GPIO27       [13] [14] GND
GPIO22       [15] [16] GPIO23
       3.3V  [17] [18] GPIO24
GPIO10 MOSI  [19] [20] GND     ← 緑LED
GPIO9  MISO  [21] [22] GPIO25
GPIO11 SCLK  [23] [24] GPIO8
      GND    [25] [26] GPIO7   ← 青LED
GPIO0        [27] [28] GPIO1
GPIO5        [29] [30] GND
GPIO6        [31] [32] GPIO12
GPIO13       [33] [34] GND     ← 赤LED
GPIO19       [35] [36] GPIO16
GPIO26       [37] [38] GPIO20
      GND    [39] [40] GPIO21
```

#### RGB LED接続（カソードコモン型）

```
Raspberry Pi          RGB LED
GPIO 13 (赤) ──[220Ω]── R (赤)
GPIO 19 (緑) ──[220Ω]── G (緑)
GPIO 26 (青) ──[220Ω]── B (青)
GND ──────────────── C (カソード共通)
```

#### RGB LED接続（アノードコモン型）

```
Raspberry Pi          RGB LED
GPIO 13 (赤) ──[220Ω]── R (赤)
GPIO 19 (緑) ──[220Ω]── G (緑)
GPIO 26 (青) ──[220Ω]── B (青)
3.3V ─────────────── A (アノード共通)
```

**注意**: アノードコモン型の場合、GPIOの出力を反転させる必要があります。

---

## 🎨 動作確認

### テストコード

```python
import RPi.GPIO as GPIO
import time

# GPIO設定
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# LEDピン設定
RED_PIN = 13
GREEN_PIN = 19
BLUE_PIN = 26

GPIO.setup(RED_PIN, GPIO.OUT)
GPIO.setup(GREEN_PIN, GPIO.OUT)
GPIO.setup(BLUE_PIN, GPIO.OUT)

try:
    # 赤
    GPIO.output(RED_PIN, GPIO.HIGH)
    time.sleep(1)
    GPIO.output(RED_PIN, GPIO.LOW)
    
    # 緑
    GPIO.output(GREEN_PIN, GPIO.HIGH)
    time.sleep(1)
    GPIO.output(GREEN_PIN, GPIO.LOW)
    
    # 青
    GPIO.output(BLUE_PIN, GPIO.HIGH)
    time.sleep(1)
    GPIO.output(BLUE_PIN, GPIO.LOW)
    
    # 白（全色）
    GPIO.output(RED_PIN, GPIO.HIGH)
    GPIO.output(GREEN_PIN, GPIO.HIGH)
    GPIO.output(BLUE_PIN, GPIO.HIGH)
    time.sleep(1)
    
finally:
    GPIO.output(RED_PIN, GPIO.LOW)
    GPIO.output(GREEN_PIN, GPIO.LOW)
    GPIO.output(BLUE_PIN, GPIO.LOW)
    GPIO.cleanup()
```

---

## ⚠️ 注意事項

1. **抵抗は必須**: GPIOピンに直接LEDを接続すると、LEDが壊れる可能性があります
2. **電流制限**: 各GPIOピンは最大16mAまで供給可能です
3. **電圧**: Raspberry PiのGPIOは3.3Vです（5Vではありません）

---

## 🔧 トラブルシューティング

### LEDが点灯しない

1. **配線を確認**: 正しいピンに接続されているか確認
2. **抵抗値を確認**: 220Ωが適切か確認
3. **LEDの極性を確認**: アノード/カソードが正しいか確認
4. **GPIO設定を確認**: `gpio_config.py`の設定を確認

### LEDが暗い

- 抵抗値が大きすぎる可能性があります（220Ω以下を試す）
- ただし、電流制限に注意してください

### LEDがすぐに壊れる

- 抵抗が接続されていない可能性があります
- 必ず抵抗を接続してください

---

## 📚 関連ドキュメント

- [ハードウェアブザー付きリーダー対応ガイド](HARDWARE_BUZZER_READER_GUIDE.md)
- [gpio_config.py](../gpio_config.py) - GPIO設定ファイル

