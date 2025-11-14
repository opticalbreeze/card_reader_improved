# 手動起動 vs 自動起動 プロセス分析

## 質問
**手動起動では `/home/raspberry/Desktop/attendance/card_reader_improved` に移動して `source venv/bin/activate` を実行して `start_pi.sh` を実行してうまくいっている。自動起動は同じプロセスか？**

## 回答：**同じプロセスではない。重要な違いがある**

---

## 手動起動のプロセス

### 実行環境
1. **シェルセッション**: ユーザーがログインした対話型シェル（通常は `bash`）
2. **環境変数の継承**: 
   - `~/.bashrc` が読み込まれる（対話型シェルのため）
   - `~/.profile` が読み込まれる
   - ユーザーの環境変数が全て継承される
3. **実行コマンド**:
   ```bash
   cd /home/raspberry/Desktop/attendance/card_reader_improved
   source venv/bin/activate
   bash start_pi.sh
   ```

### 重要なポイント
- `source venv/bin/activate` が実行されると：
  - `VIRTUAL_ENV` 環境変数が設定される
  - `PATH` の先頭に `venv/bin` が追加される
  - `python3` コマンドが仮想環境のPythonを指すようになる
- ユーザーのログインセッションなので、グループメンバーシップ（`pcscd`グループなど）が有効
- シェルの設定ファイル（`.bashrc`）が読み込まれるため、追加の環境変数やエイリアスが有効

---

## 自動起動のプロセス

### 実行環境
1. **シェルセッション**: `systemd` が起動する非対話型シェル（`/bin/bash`）
2. **環境変数の設定**:
   - `systemd` の `Environment` ディレクティブで明示的に設定された変数のみ
   - **`.bashrc` は読み込まれない**（非対話型シェルのため）
   - `~/.profile` も通常は読み込まれない
3. **実行コマンド**:
   ```ini
   ExecStart=/bin/bash /home/raspberry/Desktop/attendance/card_reader_improved/start_pi.sh
   ```

### 現在の設定（`attendance-client-fixed.service`）
```ini
Environment="PATH=/home/raspberry/Desktop/attendance/card_reader_improved/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="VIRTUAL_ENV=/home/raspberry/Desktop/attendance/card_reader_improved/venv"
```

### 重要なポイント
- `PATH` は `systemd` の `Environment` で設定されている
- `VIRTUAL_ENV` も設定されているが、**`source venv/bin/activate` の効果は限定的**
- `start_pi.sh` 内で `source venv/bin/activate` を実行しているが、既に `PATH` が設定されているため、重複している
- **非対話型シェルなので、`.bashrc` が読み込まれない** → 追加の環境変数が設定されない可能性

---

## 主な違いと問題点

### 1. Python実行ファイルの特定

**手動起動**:
```bash
source venv/bin/activate  # PATHの先頭にvenv/binが追加される
python3 pi_client.py      # venv/bin/python3が実行される
```

**自動起動**:
```bash
# PATHは既に設定されているが、python3が正しく解決されるか？
python3 pi_client.py      # システムのpython3か、venvのpython3か？
```

**問題**: `start_pi.sh` の120行目で `python3` を直接呼び出しているが、仮想環境のPythonが確実に使われるか不明確

### 2. PC/SCライブラリ（pyscard）の検出

**手動起動**:
- 仮想環境のPythonが使われる
- 仮想環境に `pyscard` がインストールされていれば、正しくインポートされる

**自動起動**:
- `python3` がシステムのPythonを指している可能性がある
- システムのPythonには `pyscard` がインストールされていない可能性がある
- または、仮想環境のPythonが使われていても、PC/SCライブラリが正しく検出されない

### 3. 環境変数の違い

**手動起動**:
- ユーザーのログインセッションの環境変数が全て継承される
- `.bashrc` で設定された変数が有効

**自動起動**:
- `systemd` の `Environment` で明示的に設定された変数のみ
- `.bashrc` は読み込まれない

### 4. グループメンバーシップ

**手動起動**:
- ユーザーがログインしているため、グループメンバーシップが有効
- `pcscd` グループへのアクセス権限が有効

**自動起動**:
- `Group=pcscd` が設定されているが、ユーザーが `pcscd` グループに所属していない場合、権限エラーが発生する可能性

---

## 推奨される修正

### 1. `start_pi.sh` で明示的に仮想環境のPythonを使用

```bash
# 現在（120行目）
python3 pi_client.py

# 修正後
"$VIRTUAL_ENV/bin/python3" pi_client.py
# または
exec "$(dirname "$0")/venv/bin/python3" pi_client.py
```

### 2. PC/SC接続テストでも仮想環境のPythonを使用

```bash
# 現在（101行目）
if python3 -c "from smartcard.System import readers; readers()" 2>/dev/null; then

# 修正後
if "$VIRTUAL_ENV/bin/python3" -c "from smartcard.System import readers; readers()" 2>/dev/null; then
```

### 3. 仮想環境の有効化を確実にする

`start_pi.sh` で `source venv/bin/activate` の後に、実際に仮想環境が有効化されたか確認する：

```bash
source venv/bin/activate
if [ -z "$VIRTUAL_ENV" ]; then
    echo "[エラー] 仮想環境の有効化に失敗しました"
    exit 1
fi
echo "[確認] 仮想環境: $VIRTUAL_ENV"
echo "[確認] Python: $(which python3)"
```

---

## 確認方法

### 手動起動時の確認
```bash
cd /home/raspberry/Desktop/attendance/card_reader_improved
source venv/bin/activate
which python3
python3 -c "import sys; print(sys.executable)"
python3 -c "from smartcard.System import readers; print(readers())"
```

### 自動起動時の確認（ログから）
```bash
sudo journalctl -u attendance-client-fixed.service -n 200 --no-pager | grep -E "Python|python3|仮想環境|PC/SC"
```

---

## 結論

**自動起動は `start_pi.sh` に依存しているが、実行環境が異なるため、同じプロセスではない。**

主な違い：
1. シェルの種類（対話型 vs 非対話型）
2. 環境変数の継承方法
3. Python実行ファイルの特定方法
4. グループメンバーシップの有効性

**修正が必要な点**:
- `start_pi.sh` で明示的に仮想環境のPythonを使用する
- PC/SC接続テストでも仮想環境のPythonを使用する
- 仮想環境の有効化を確認する

