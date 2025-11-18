# LCD文字化け対策 - 追加修正

## 🔍 問題の詳細

「何度かカードをかざすと文字化けする」という問題は、以下の原因が考えられます：

1. **LCDバッファの残存**: 前の文字列が完全に消去されずに残っている
2. **文字列の長さ不一致**: 16文字未満の文字列が表示され、前の文字列の残りが残る
3. **特殊文字の混入**: カードIDやタイムスタンプに特殊文字が含まれている

## ✅ 追加した対策

### 1. 文字列のパディング強化

**修正前**:
```python
# 最大長に制限するだけ
if len(result) > max_length:
    result = result[:max_length]
```

**修正後**:
```python
# 必ずmax_length文字になるように空白でパディング
result = result.ljust(max_length, ' ')
```

これにより、短い文字列でも必ず16文字になるため、前の文字列の残りが消えます。

### 2. LCDクリア機能の追加

`clear_lcd()` 関数を追加して、LCD画面を明示的にクリアできるようにしました。

**機能**:
- LCD_I2Cモジュールに`clear()`メソッドがある場合、それを使用
- `clear()`メソッドがない場合、空白で埋めてクリア

### 3. 重要なタイミングでLCDをクリア

以下のタイミングでLCDをクリアしてから表示するようにしました：

1. **カード検出後の状態リセット時**
   - カード読み取り後、待機状態に戻る時

2. **NFCリーダー再接続時**
   - 接続が切れて再接続した時

3. **エラー発生時**
   - LCD更新でエラーが発生した時

### 4. デバッグログの強化

文字列の長さもログに出力するようにしました：

```
[DEBUG] LCD表示: 'Card Reader      ' / 'Ready            ' (長さ: 16/16)
```

## 📊 修正内容の詳細

### sanitize_lcd_text() 関数の改善

```python
def sanitize_lcd_text(self, text: str, max_length: int = 16) -> str:
    # ... 文字列のサニタイズ処理 ...
    
    # 必ずmax_length文字になるように空白でパディング
    result = result.ljust(max_length, ' ')
    
    return result
```

**効果**:
- 短い文字列でも必ず16文字になる
- 前の文字列の残りが確実に消える
- 文字化けの原因となる残存文字を防止

### clear_lcd() 関数の追加

```python
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
```

**効果**:
- LCD画面を明示的にクリア
- バッファの残存を防止
- エラーが発生しても処理を継続

### update_lcd() 関数の改善

```python
def update_lcd(self, line1: str, line2: str):
    """LCDを更新（文字化け対策版・バッファクリア対応）"""
    # 文字列をサニタイズ（必ず16文字でパディング）
    safe_line1 = self.sanitize_lcd_text(line1, 16)
    safe_line2 = self.sanitize_lcd_text(line2, 16)
    
    # LCDに表示
    self.lcd.display(safe_line1, safe_line2)
    
    # エラーが発生した場合、LCDをクリアして再試行
    # ...
```

**効果**:
- 必ず16文字でパディングされた文字列を表示
- エラー時の自動復旧
- 詳細なデバッグログ

## 🔧 使用例

### 修正前の問題

```python
# 短い文字列を表示
self.update_lcd("Card", "Ready")
# → "Card" + 前の文字列の残り（12文字）が残る可能性
```

### 修正後

```python
# 短い文字列でも必ず16文字でパディング
self.update_lcd("Card", "Ready")
# → "Card            " + "Ready           " （必ず16文字）
```

## 🐛 デバッグ方法

### ログで確認

```bash
# LCD表示のログを確認
grep "LCD表示" card_reader.log

# 出力例:
# [DEBUG] LCD表示: 'Card Reader      ' / 'Ready            ' (長さ: 16/16)
# [DEBUG] LCD表示: 'Card Detected    ' / '0123456789ABCDEF' (長さ: 16/16)
```

### 文字列の長さを確認

すべてのLCD表示文字列が16文字になっているか確認してください。16文字未満の場合は、パディングが正しく動作していない可能性があります。

## ⚠️ 注意事項

1. **パディングの重要性**: 文字列を必ず16文字でパディングすることで、前の文字列の残りを確実に消します。

2. **クリア処理のタイミング**: 重要なタイミング（状態変更時など）でLCDをクリアすることで、バッファの残存を防止します。

3. **エラーハンドリング**: LCD更新でエラーが発生した場合、自動的にクリアして再試行します。

## 🔄 今後の改善案

- [ ] LCDのバッファ状態を監視
- [ ] 定期的なLCDクリア（例：1時間ごと）
- [ ] 文字列の検証機能の追加

---

**更新日**: 2025年1月
**バージョン**: LCD文字化け対策版 v1.3

