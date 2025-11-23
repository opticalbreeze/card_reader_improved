# カード読み取り問題の調査結果

## 問題の概要
「しばらく時間を置くと1枚目のカードは読み込まず、2枚目のカードから読み込む」

## 調査結果

### 1. 重複チェックの二重構造

#### `history` (短期的な重複チェック)
- **目的**: 2秒以内の連続読み取りを防止 (`CARD_DUPLICATE_THRESHOLD = 2.0`)
- **場所**: `nfcpy_worker`/`pcsc_worker`内でチェック (523行目)
- **管理**: `self.history[card_id] = now` でタイムスタンプを保存

#### `attendance_history` (分単位の重複チェック)
- **目的**: 同じ分（YYYY-MM-DD HH:MM）内の重複打刻を防止
- **場所**: `process_card`内でチェック (465行目)
- **管理**: `is_duplicate_attendance`関数内で履歴を更新 (430行目)

### 2. 問題の根本原因

#### 問題点1: `attendance_history`がクリーンアップされない
- `attendance_history`はメモリ内の辞書で、プログラム起動時に空で初期化される
- **しかし、古いエントリを自動的にクリーンアップする仕組みがない**
- 過去に打刻したカードIDが`attendance_history`に残り続ける可能性がある

#### 問題点2: `is_duplicate_attendance`関数の動作
```python
# 同じ分（YYYY-MM-DD HH:MM）であれば重複チェック
if current_minute_key == last_minute_key:
    time_diff = (current_dt - last_dt).total_seconds()
    if time_diff < SAME_MINUTE_THRESHOLD:  # 60秒以内
        return True, f"同一時刻打刻済み ({last_minute_key})"

# 履歴を更新（重複でなくても、重複でも）
history[card_id] = {
    'timestamp': timestamp,
    'datetime': current_dt
}
```

#### 問題点3: 時間経過後の動作
- **シナリオ**: 数時間前に同じカードIDで打刻した場合
  - 例: 昨日 11:30 に打刻
  - 今日 11:30 に再度打刻しようとする
  
- **問題**: 
  - `is_duplicate_attendance`は同じ分（11:30）として判定
  - しかし、タイムスタンプは1日前なので、`time_diff`は非常に大きい（86400秒以上）
  - 60秒以上経過しているため、重複ではないと判定される
  - **履歴は更新される**（430行目）

### 3. 実際の問題シナリオ

#### シナリオA: 同じ分内での2回目の打刻
1. 11:30:00 - 1枚目のカードをかざす → `attendance_history[card_id] = {datetime: 11:30:00}`
2. 11:30:30 - 同じカードを再度かざす
   - `current_minute_key = "2025-11-23 11:30"`
   - `last_minute_key = "2025-11-23 11:30"` → 同じ分
   - `time_diff = 30秒` → 60秒未満
   - **→ 重複と判定、スキップされる** ✅ これは正しい動作

#### シナリオB: 異なる分での打刻（しかし古い履歴が残っている場合）
1. 昨日 11:30 - カードを打刻 → `attendance_history[card_id] = {datetime: 昨日11:30}`
2. **プログラムが長時間動作している** → `attendance_history`がクリーンアップされない
3. 今日 11:30 - 同じカードを再度かざす
   - `current_minute_key = "2025-11-23 11:30"`
   - `last_minute_key = "2025-11-22 11:30"` → **異なる分**
   - `last_minute_key != current_minute_key` → 重複チェックをスキップ
   - **履歴を更新** → これは正しい動作 ✅

#### シナリオC: **問題の原因 - 同じ分で、かつ長時間経過している場合**
1. 11:30:00 - カードを打刻 → `attendance_history[card_id] = {datetime: 11:30:00}`
2. **プログラムが長時間動作している**
3. 翌日 11:30:30 - 同じカードを再度かざす（同じ分、しかし1日後）
   - `current_minute_key = "2025-11-24 11:30"`
   - `last_minute_key = "2025-11-23 11:30"` → **異なる分**
   - `last_minute_key != current_minute_key` → 重複チェックをスキップ
   - **履歴を更新** → これは正しい動作 ✅

### 4. 実際の問題の可能性

#### 可能性1: `history`と`attendance_history`の不整合
- `history`は`CARD_DUPLICATE_THRESHOLD`（2秒）で管理されている
- `attendance_history`は分単位で管理されている
- **もし、`history`に古いエントリが残っている場合、2秒以上経過していれば`process_card`は呼ばれる**
- **しかし、`attendance_history`に同じ分のエントリが残っている場合、重複と判定される可能性がある**

#### 可能性2: タイムゾーンや日付の変更
- もし、タイムゾーンや日付が変更された場合、`current_minute_key`と`last_minute_key`の比較が正しく行われない可能性がある

#### 可能性3: `last_id`の状態
- `nfcpy_worker`/`pcsc_worker`内で`last_id`が設定されているが、これはスレッド内のローカル変数
- もし、カードが長時間リーダーに触れていた場合、`last_id`が設定され、次のカードが検出されない可能性がある

### 5. 推奨される修正

#### 修正1: `attendance_history`のクリーンアップ
- 古いエントリ（例えば1時間以上前）を定期的にクリーンアップする

#### 修正2: `is_duplicate_attendance`関数の改善
- 同じ分であっても、日付が異なる場合は重複と判定しない
- または、古いエントリ（例えば1時間以上前）は無視する

#### 修正3: ログ出力の追加
- カード読み取り時に、`history`と`attendance_history`の状態をログ出力してデバッグする

