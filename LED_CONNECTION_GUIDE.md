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

### RGB LED（カソードコモン）の接続

```
Raspberry Pi         抵抗         RGB LED
─────────────────────────────────────────
GPIO 13 (赤) ──[220Ω]─── 赤LEDアノード (+)
GPIO 19 (緑) ──[220Ω]─── 緑LEDアノード (+)
GPIO 26 (青) ──[220Ω]─── 青LEDアノード (+)
GND          ─────────── カソードコモン (-)
```

### RGB LED（アノードコモン）の接続

```
Raspberry Pi         抵抗         RGB LED
─────────────────────────────────────────
3.3V         ─────────── アノードコモン (+)
GPIO 13 (赤) ──[220Ω]─── 赤LEDカソード (-)
GPIO 19 (緑) ──[220Ω]─── 緑LEDカソード (-)
GPIO 26 (青) ──[220Ω]─── 青LEDカソード (-)
```

**注意**: アノードコモンの場合、GPIOピンはLOW（0V）でLEDが点灯します。コード側で反転が必要な場合があります。

## 🔧 接続手順

### ステップ1: 部品の準備

1. RGB LED 1個
2. 抵抗 220Ω × 3本
3. ジャンパーワイヤー × 4本（3本でも可）
4. ブレッドボード（推奨）

### ステップ2: 配線

#### カソードコモンRGB LEDの場合:

1. **赤LED**:
   - GPIO 13 → 抵抗 220Ω → RGB LEDの赤ピン
   - RGB LEDのコモン（-） → GND

2. **緑LED**:
   - GPIO 19 → 抵抗 220Ω → RGB LEDの緑ピン
   - RGB LEDのコモン（-） → GND（既に接続済み）

3. **青LED**:
   - GPIO 26 → 抵抗 220Ω → RGB LEDの青ピン
   - RGB LEDのコモン（-） → GND（既に接続済み）

### ステップ3: 動作確認

プログラムを実行してLEDが点灯するか確認：

```bash
python3 client_card_reader_unified_improved.py
```

## 🎨 LEDの色と動作

| 色 | GPIO設定 | 用途 |
|---|---------|------|
| **緑** | R:0, G:100, B:0 | 正常動作中 |
| **青** | R:0, G:0, B:100 | カード読み取り成功 |
| **赤** | R:100, G:0, B:0 | エラー・待機中 |
| **オレンジ** | R:100, G:50, B:0 | 警告・ローカル保存 |
| **消灯** | R:0, G:0, B:0 | オフ |

## ⚠️ 注意事項

### 1. 抵抗の必要性

**必ず抵抗を使用してください！** GPIOピンは最大3.3V、最大16mAまでしか供給できません。抵抗なしでLEDを接続すると、GPIOピンが破損する可能性があります。

### 2. 抵抗値の計算

一般的なLEDの順方向電圧（Vf）は約2V、順方向電流（If）は約10-20mAです。

```
抵抗値 = (電源電圧 - LED電圧) / 電流
抵抗値 = (3.3V - 2.0V) / 0.015A ≈ 87Ω
```

**推奨**: 220Ω（安全マージンを含む）

### 3. GPIOピンの確認

現在の設定を確認：

```bash
cat gpio_config.py | grep LED
```

出力例：
```
LED_RED_PIN = 13
LED_GREEN_PIN = 19
LED_BLUE_PIN = 26
```

### 4. PWM制御について

このコードはPWM（Pulse Width Modulation）を使用してLEDの明るさを制御しています。各色は0-100%のデューティ比で制御されます。

## 🔍 トラブルシューティング

### LEDが点灯しない

1. **配線の確認**
   - GPIOピン番号が正しいか
   - 抵抗が接続されているか
   - GNDが正しく接続されているか

2. **LEDの極性確認**
   - カソードコモンかアノードコモンか
   - 各色のピンが正しいか

3. **GPIOの確認**
   ```bash
   # GPIOが有効か確認（プログラム実行時のログを確認）
   python3 client_card_reader_unified_improved.py
   ```

4. **権限の確認**
   ```bash
   # sudoで実行してみる
   sudo python3 client_card_reader_unified_improved.py
   ```

### LEDが常に点灯している

- GPIOピンが他のプログラムで使用されていないか確認
- プログラムを再起動

### LEDの色がおかしい

- RGB LEDのピン配列を確認（データシート参照）
- `gpio_config.py`のピン番号を確認

## 📝 ピン番号の変更方法

`gpio_config.py`を編集：

```python
LED_RED_PIN = 13     # 変更したいピン番号
LED_GREEN_PIN = 19   # 変更したいピン番号
LED_BLUE_PIN = 26    # 変更したいピン番号
```

変更後、プログラムを再起動してください。

## 🔗 参考資料

- [Raspberry Pi GPIOピン配置](https://pinout.xyz/)
- [RPi.GPIO Documentation](https://sourceforge.net/projects/raspberry-gpio-python/)
- [RGB LEDの基礎知識](https://www.eleki-jack.com/faq/led/rgb-led/)

---

**作成日**: 2025年11月13日  
**対象**: Raspberry Pi 3/4  
**対応バージョン**: client_card_reader_unified_improved.py v1.x

