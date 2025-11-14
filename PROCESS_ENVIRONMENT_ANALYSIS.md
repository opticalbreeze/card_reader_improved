# 手動起動と自動起動のプロセス環境の違い

## 問題

手動起動では正常に動作するが、自動起動ではカードリーダーが認識されない。

## 原因の可能性

### 1. 環境変数の違い

**手動起動:**
- ターミナルから実行
- ユーザーの`.bashrc`や`.profile`が読み込まれる
- 環境変数が設定される

**自動起動:**
- systemdサービスから実行
- ユーザーの`.bashrc`や`.profile`が読み込まれない
- 環境変数はサービスファイルで明示的に設定する必要がある

### 2. PATHの違い

**手動起動:**
- ユーザーのPATHが設定される
- 仮想環境を有効化すると、仮想環境のパスが追加される

**自動起動:**
- 最小限のPATHしか設定されない可能性
- 仮想環境のパスが含まれていない可能性

### 3. 仮想環境の有効化

**手動起動:**
- `source venv/bin/activate`で仮想環境を有効化
- `VIRTUAL_ENV`環境変数が設定される
- PATHに仮想環境のパスが追加される

**自動起動:**
- `start_pi.sh`内で`source venv/bin/activate`を実行
- しかし、systemdサービスから実行される場合、環境が違う可能性

## 検証方法

### ラズパイ側で実行

```bash
# 1. 手動起動時の環境を確認
cd ~/Desktop/attendance/card_reader_improved
source venv/bin/activate
./verify_process_environment.sh

# 2. 自動起動時の環境を確認（サービスが実行中の場合）
./compare_manual_vs_autostart.sh

# 3. サービスログを確認
sudo journalctl -u attendance-client-fixed.service -n 100
```

## 修正内容

### `attendance-client-fixed.service`の修正

1. **PATHに仮想環境のパスを追加**
2. **LANGとLC_ALLを明示的に設定**
3. **VIRTUAL_ENV環境変数を設定**

これにより、手動起動時と同じ環境を再現します。

