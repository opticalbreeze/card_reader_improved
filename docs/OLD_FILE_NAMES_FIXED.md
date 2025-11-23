# 古いファイル名参照の修正まとめ

## ✅ 修正完了

以下の古いファイル名や存在しないファイルへの参照を修正しました。

### 修正したファイル

#### 1. README.md
- ❌ `./start_unified.sh` → ✅ `./start_pi_simple.sh`
- ❌ `python3 check_system.py` → ✅ 削除（存在しない）
- ❌ `QUICK_START.md` → ✅ `docs/RASPBERRY_PI_SETUP_FROM_SCRATCH.md`

#### 2. docs/RASPBERRY_PI_CRASH_ANALYSIS.md
- ❌ `client_card_reader_unified_improved.py` → ✅ `pi_client.py`

#### 3. docs/RASPBERRY_PI_SIMPLE_SETUP.md
- ❌ `pi_client_simple.py` → ✅ `pi_client.py`（すべての箇所）

#### 4. docs/NFCPY_SPEED_OPTIMIZATION.md
- ❌ `client_card_reader_unified_improved.py` → ✅ `pi_client.py`
- ❌ `client_card_reader_windows_gui_improved.py` → ✅ `win_client.py`

### 現在の正しいファイル名

#### ラズパイ版
- ✅ **`pi_client.py`** - 唯一のメインファイル（これのみ使用）

#### Windows版
- ✅ **`win_client.py`** - 唯一のメインファイル（これのみ使用）

#### 設定ファイル
- ✅ **`config.py`** - 設定GUI（Windows/ラズパイ両対応）

#### 起動スクリプト（ラズパイ）
- ✅ **`start_pi_simple.sh`** - シンプル起動（推奨）
- ✅ **`start_pi.sh`** - 詳細起動（デバッグ用）

### 使用しない古いファイル名

以下のファイル名は使用しません：

- ❌ `client_card_reader_unified_improved.py`
- ❌ `client_card_reader_unified.py`
- ❌ `client_card_reader_windows_gui_improved.py`
- ❌ `client_card_reader_windows_gui.py`
- ❌ `pi_client_simple.py`（バックアップとして存在するが使用しない）
- ❌ `start_unified.sh`
- ❌ `check_system.py`

### 正しい起動方法

#### ラズパイ版
```bash
cd /home/raspberry/Desktop/card_reader_improved
source venv/bin/activate  # 仮想環境を有効化（必須）
python3 pi_client.py
```

または起動スクリプトを使用：
```bash
./start_pi_simple.sh  # 仮想環境を自動有効化
```

#### Windows版
```bash
python win_client.py
```

### 注意事項

**重要**: 今後は以下のファイル名のみを使用してください：
- ラズパイ版: `pi_client.py`
- Windows版: `win_client.py`

新しいバージョンや別名のファイルを作成しないでください。
（詳細は `docs/NO_NEW_VERSIONS.md` を参照）

