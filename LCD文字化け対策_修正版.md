# LCD文字化け対策 - 修正版

## 🔍 問題の本質

LCDが元々アルファベット表示のみ対応している場合、日本語対応処理は不要です。

**実際の問題**:
- 文字列が16文字未満の場合、前の文字列の残りが残る
- 制御文字（改行、タブなど）が混入している
- LCDのバッファがクリアされていない

## ✅ 本当に必要な対策

### 1. 文字列のパディング（最重要）

**問題**: 短い文字列を表示すると、前の文字列の残りが残る

**解決策**: 必ず16文字でパディング

```python
# 修正前
"Card" → "Card" (4文字) + 前の文字列の残り（12文字）が残る

# 修正後
"Card" → "Card            " (16文字) 前の文字列の残りが消える
```

### 2. 制御文字の除去

**問題**: 改行、タブなどの制御文字が混入している

**解決策**: 制御文字を空白に変換

```python
# 改行、タブ、制御文字（0x00-0x1F）を空白に変換
if char in ['\n', '\r', '\t'] or ord(char) < 0x20:
    result += ' '
```

### 3. LCDクリア処理

**問題**: LCDのバッファがクリアされていない

**解決策**: 重要なタイミングでLCDをクリア

```python
# 状態変更時などにLCDをクリア
self.clear_lcd()
time.sleep(0.05)
self.update_lcd("Card Reader", "Ready")
```

## 📝 修正後のコード

### sanitize_lcd_text() 関数

```python
def sanitize_lcd_text(self, text: str, max_length: int = 16) -> str:
    """LCD表示用に文字列をサニタイズ（制御文字の除去とパディング）"""
    if not text:
        return " " * max_length
    
    # 制御文字や改行文字を除去・変換
    result = ""
    for char in text:
        # 改行、タブ、制御文字を空白に変換
        if char in ['\n', '\r', '\t'] or ord(char) < 0x20:
            result += ' '
        # 通常の文字（0x20-0x7E）はそのまま
        elif ord(char) <= 0x7E:
            result += char
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
    
    # 必ずmax_length文字になるように空白でパディング
    # これが文字化け防止の重要なポイント
    result = result.ljust(max_length, ' ')
    
    return result
```

## 🎯 重要なポイント

### 1. パディングが最重要

```python
# 必ず16文字でパディング
result = result.ljust(max_length, ' ')
```

これにより、短い文字列でも前の文字列の残りが確実に消えます。

### 2. 制御文字の除去

制御文字（改行、タブなど）が混入していると、LCDの表示が崩れる可能性があります。

### 3. LCDクリア処理

状態変更時などにLCDをクリアすることで、バッファの残存を防止します。

## ❌ 不要な処理

### 日本語対応処理

LCDが元々アルファベット表示のみ対応している場合、日本語をASCIIに変換する処理は不要です。ただし、日本語が混入した場合に備えて、空白に変換する処理は残しています。

## 📊 効果

### 修正前

```
"Card" → "Card" (4文字) + 前の文字列の残り（12文字）
→ 文字化けが発生
```

### 修正後

```
"Card" → "Card            " (16文字)
→ 前の文字列の残りが消える
→ 文字化けが発生しない
```

## 🔧 デバッグ方法

### ログで確認

```bash
# LCD表示のログを確認
grep "LCD表示" card_reader.log

# 出力例:
# [DEBUG] LCD表示: 'Card Reader      ' / 'Ready            ' (長さ: 16/16)
```

すべての文字列が16文字になっているか確認してください。

---

**更新日**: 2025年1月
**バージョン**: LCD文字化け対策版 v1.4（修正版）

