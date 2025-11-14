# 最新版への更新ガイド

このガイドでは、PCとラズパイで最新版のリポジトリを取得・更新する方法を説明します。

---

## 📋 目次

1. [PC（Windows）での更新](#pcwindowsでの更新)
2. [ラズパイでの更新（既存リポジトリあり）](#ラズパイでの更新既存リポジトリあり)
3. [ラズパイでの新規セットアップ](#ラズパイでの新規セットアップ)
4. [トラブルシューティング](#トラブルシューティング)

---

## 🪟 PC（Windows）での更新

### 現在のワークスペースを更新する場合

```cmd
cd C:\Users\optic\Desktop\card_reader_improved
git pull origin main
```

### 新しい場所にクローンする場合

```cmd
cd C:\Users\optic\Desktop
git clone https://github.com/opticalbreeze/card_reader_improved.git card_reader_improved_new
cd card_reader_improved_new
```

### 設定ファイルを移行

古い設定ファイルがある場合は、新しいディレクトリにコピーします：

```cmd
copy "C:\Users\optic\Desktop\card_reader_improved\client_config.json" "C:\Users\optic\Desktop\card_reader_improved_new\client_config.json"
copy "C:\Users\optic\Desktop\card_reader_improved\local_cache.db" "C:\Users\optic\Desktop\card_reader_improved_new\local_cache.db"
```

---

## 🍓 ラズパイでの更新（既存リポジトリあり）

### 方法1: 既存リポジトリを更新（推奨）

#### ステップ1: 現在の状態を確認

```bash
cd ~/card_reader_improved
git status
```

#### ステップ2: ローカルの変更をバックアップ

**重要なファイルをバックアップ:**

```bash
# バックアップディレクトリを作成
mkdir -p ~/backup_$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=~/backup_$(date +%Y%m%d_%H%M%S)

# 設定ファイルとデータベースをバックアップ
cp client_config.json $BACKUP_DIR/ 2>/dev/null || echo "client_config.json not found"
cp attendance.db $BACKUP_DIR/ 2>/dev/null || echo "attendance.db not found"
cp local_cache.db $BACKUP_DIR/ 2>/dev/null || echo "local_cache.db not found"

echo "バックアップ完了: $BACKUP_DIR"
ls -la $BACKUP_DIR
```

#### ステップ3: 自動起動サービスを停止（実行中の場合）

```bash
# サービスが実行中か確認
sudo systemctl status attendance-client

# 実行中の場合は停止
sudo systemctl stop attendance-client
```

#### ステップ4: リポジトリを最新版に更新

**オプションA: ローカル変更を保持してマージ**

```bash
cd ~/card_reader_improved

# 現在のブランチを確認
git branch

# リモートから最新版を取得
git fetch origin

# ローカルの変更をstash（一時保存）
git stash

# 最新版をpull
git pull origin main

# stashした変更を戻す（必要な場合）
git stash pop
```

**オプションB: ローカル変更を破棄して最新版に上書き（推奨）**

```bash
cd ~/card_reader_improved

# ローカルの変更を破棄
git reset --hard

# 最新版を取得
git pull origin main
```

#### ステップ5: バックアップから設定ファイルを復元

```bash
# バックアップディレクトリを確認
ls -la ~/backup_*

# 最新のバックアップディレクトリを指定して復元
BACKUP_DIR=~/backup_YYYYMMDD_HHMMSS  # 実際のディレクトリ名に置き換え

cp $BACKUP_DIR/client_config.json ~/card_reader_improved/ 2>/dev/null
cp $BACKUP_DIR/attendance.db ~/card_reader_improved/ 2>/dev/null
cp $BACKUP_DIR/local_cache.db ~/card_reader_improved/ 2>/dev/null

echo "設定ファイルを復元しました"
```

#### ステップ6: 依存パッケージを更新（必要な場合）

```bash
cd ~/card_reader_improved
pip3 install --upgrade -r requirements_unified.txt
```

#### ステップ7: 自動起動サービスを再設定（systemd使用の場合）

```bash
# 自動起動スクリプトに実行権限を付与
chmod +x setup_autostart.sh

# 自動起動を再設定
sudo bash setup_autostart.sh
```

#### ステップ8: サービスを起動

```bash
# サービスを起動
sudo systemctl start attendance-client

# 状態を確認
sudo systemctl status attendance-client

# ログを確認
sudo journalctl -u attendance-client -f
```

---

### 方法2: 新しい場所に最新版をクローン（安全）

既存のリポジトリを残したまま、新しい場所に最新版を取得します。

#### ステップ1: 自動起動サービスを停止

```bash
sudo systemctl stop attendance-client 2>/dev/null || echo "サービスなし"
```

#### ステップ2: 既存ディレクトリをリネーム

```bash
cd ~
mv card_reader_improved card_reader_improved_old_$(date +%Y%m%d)
```

#### ステップ3: 最新版をクローン

```bash
cd ~
git clone https://github.com/opticalbreeze/card_reader_improved.git
cd card_reader_improved
```

#### ステップ4: 設定ファイルを移行

```bash
# 古いディレクトリから設定ファイルをコピー
OLD_DIR=~/card_reader_improved_old_$(date +%Y%m%d)

cp $OLD_DIR/client_config.json ~/card_reader_improved/ 2>/dev/null
cp $OLD_DIR/attendance.db ~/card_reader_improved/ 2>/dev/null
cp $OLD_DIR/local_cache.db ~/card_reader_improved/ 2>/dev/null

echo "設定ファイルを移行しました"
```

#### ステップ5: 自動起動を再設定

```bash
cd ~/card_reader_improved
chmod +x setup_autostart.sh
sudo bash setup_autostart.sh
```

#### ステップ6: 動作確認後、古いディレクトリを削除

```bash
# 動作確認が完了したら
rm -rf ~/card_reader_improved_old_*
```

---

## 🍓 ラズパイでの新規セットアップ

既存リポジトリがない場合の手順です。

### ステップ1: リポジトリをクローン

```bash
cd ~
git clone https://github.com/opticalbreeze/card_reader_improved.git
cd card_reader_improved
```

### ステップ2: 必要なパッケージをインストール

```bash
pip3 install -r requirements_unified.txt
```

### ステップ3: 設定ファイルを作成

```bash
# サンプル設定をコピー
cp client_config_sample.json client_config.json

# 設定を編集
nano client_config.json
```

### ステップ4: 自動起動を設定

```bash
chmod +x setup_autostart.sh
sudo bash setup_autostart.sh
```

---

## 🔧 トラブルシューティング

### 問題1: git pull でエラーが出る

**症状:**
```
error: Your local changes to the following files would be overwritten by merge:
```

**解決策:**
```bash
# ローカルの変更を破棄して最新版を取得
git reset --hard
git pull origin main
```

---

### 問題2: マージコンフリクトが発生

**症状:**
```
CONFLICT (content): Merge conflict in config.py
```

**解決策1: リモートの内容を優先（推奨）**
```bash
# リモート（GitHub）の内容を採用
git checkout --theirs config.py
git add config.py
git commit -m "Resolve conflict - use remote version"
```

**解決策2: ローカルの内容を優先**
```bash
# ローカルの内容を採用
git checkout --ours config.py
git add config.py
git commit -m "Resolve conflict - use local version"
```

**解決策3: 完全にやり直し**
```bash
# マージを中止
git merge --abort

# ローカルの変更を破棄して最新版を取得
git reset --hard origin/main
```

---

### 問題3: 古いサービスが残っている

**症状:**
```
Failed to start attendance-client.service
```

**解決策:**
```bash
# 古いサービスを完全に削除
sudo systemctl stop attendance-client
sudo systemctl disable attendance-client
sudo rm /etc/systemd/system/attendance-client.service
sudo systemctl daemon-reload

# 新しいサービスを設定
cd ~/card_reader_improved
sudo bash setup_autostart.sh
```

---

### 問題4: 依存パッケージのエラー

**症状:**
```
ModuleNotFoundError: No module named 'requests'
```

**解決策:**
```bash
# パッケージを再インストール
cd ~/card_reader_improved
pip3 install --upgrade pip
pip3 install -r requirements_unified.txt
```

---

### 問題5: 設定ファイルが消えた

**解決策:**
```bash
# バックアップから復元
ls -la ~/backup_*

# 最新のバックアップから復元
cp ~/backup_YYYYMMDD_HHMMSS/client_config.json ~/card_reader_improved/

# バックアップがない場合はサンプルから作成
cd ~/card_reader_improved
cp client_config_sample.json client_config.json
nano client_config.json
```

---

## 📝 更新後の確認チェックリスト

### Windows版
- [ ] `git pull` で最新版を取得した
- [ ] `start_venv.bat` が動作する
- [ ] カードリーダーが検出される
- [ ] カード読み取りが正常に動作する
- [ ] スリープ復帰後もカードが読み取れる

### ラズパイ版
- [ ] `git pull` で最新版を取得した
- [ ] 設定ファイルとデータベースをバックアップした
- [ ] サービスを再設定した（`sudo bash setup_autostart.sh`）
- [ ] サービスが正常に起動する（`sudo systemctl status attendance-client`）
- [ ] カードリーダーが検出される
- [ ] カード読み取りが正常に動作する
- [ ] 再起動後に自動起動する

---

## 🚀 クイックコマンド集

### Windows - 最新版に更新

```cmd
cd C:\Users\optic\Desktop\card_reader_improved
git pull origin main
```

### ラズパイ - 安全に最新版に更新（推奨）

```bash
# バックアップ
mkdir -p ~/backup_$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=~/backup_$(date +%Y%m%d_%H%M%S)
cd ~/card_reader_improved
cp client_config.json attendance.db $BACKUP_DIR/ 2>/dev/null

# サービス停止
sudo systemctl stop attendance-client 2>/dev/null

# 最新版に更新
git reset --hard
git pull origin main

# 設定復元
cp $BACKUP_DIR/* ~/card_reader_improved/ 2>/dev/null

# サービス再起動
sudo systemctl start attendance-client
sudo systemctl status attendance-client
```

---

## 📞 サポート

更新時に問題が発生した場合は、以下の情報を添えて報告してください：

### 共通
- 実行したコマンド
- エラーメッセージの全文
- `git status` の出力
- `git log --oneline -5` の出力

### ラズパイ
- `sudo systemctl status attendance-client` の出力
- `sudo journalctl -u attendance-client -n 50` の出力

---

**最終更新日: 2024年11月**
**リポジトリURL: https://github.com/opticalbreeze/card_reader_improved**

