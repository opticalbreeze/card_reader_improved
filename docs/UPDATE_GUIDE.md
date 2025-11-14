# 更新ガイド

このガイドでは、最新版への更新方法を説明します。

---

## 📋 目次

1. [Windows版の更新](#windows版の更新)
2. [Raspberry Pi版の更新](#raspberry-pi版の更新)
3. [トラブルシューティング](#トラブルシューティング)

---

## 🪟 Windows版の更新

### 基本的な更新手順

```cmd
cd C:\Users\YourName\Desktop\card_reader_improved
git pull origin main
```

### 設定ファイルのバックアップ

更新前に設定ファイルをバックアップ：

```cmd
copy client_config.json client_config.json.backup
```

### 更新後の確認

1. クライアントが起動するか確認
2. カードリーダーが検出されるか確認
3. カード読み取りが正常に動作するか確認

---

## 🍓 Raspberry Pi版の更新

### 方法1: 既存リポジトリを更新（推奨）

#### ステップ1: バックアップ

```bash
cd ~/Desktop/attendance/card_reader_improved

# バックアップディレクトリを作成
mkdir -p ~/backup_$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=~/backup_$(date +%Y%m%d_%H%M%S)

# 設定ファイルとデータベースをバックアップ
cp client_config.json $BACKUP_DIR/ 2>/dev/null
cp attendance.db $BACKUP_DIR/ 2>/dev/null
```

#### ステップ2: サービスを停止

```bash
sudo systemctl stop attendance-client-fixed.service
```

#### ステップ3: 最新版を取得

```bash
# ローカルの変更を破棄して最新版を取得
git reset --hard
git pull origin main
```

#### ステップ4: 設定ファイルを復元

```bash
cp $BACKUP_DIR/client_config.json ./
cp $BACKUP_DIR/attendance.db ./ 2>/dev/null
```

#### ステップ5: サービスファイルを更新

```bash
sudo cp attendance-client-fixed.service /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/attendance-client-fixed.service
sudo systemctl daemon-reload
```

#### ステップ6: サービスを再起動

```bash
sudo systemctl start attendance-client-fixed.service
sudo systemctl status attendance-client-fixed.service
```

### 方法2: 新しい場所にクローン（安全）

```bash
# 既存ディレクトリをリネーム
cd ~
mv card_reader_improved card_reader_improved_old_$(date +%Y%m%d)

# 最新版をクローン
git clone https://github.com/opticalbreeze/card_reader_improved.git
cd card_reader_improved

# 設定ファイルを移行
cp ../card_reader_improved_old_*/client_config.json ./
cp ../card_reader_improved_old_*/attendance.db ./ 2>/dev/null

# 自動起動を再設定
chmod +x setup_autostart_fixed.sh
sudo bash setup_autostart_fixed.sh
```

---

## 🔧 トラブルシューティング

### git pullでエラーが出る

**ローカルの変更を破棄:**
```bash
git reset --hard
git pull origin main
```

### マージコンフリクトが発生

**リモートの内容を優先:**
```bash
git checkout --theirs [ファイル名]
git add [ファイル名]
git commit -m "Resolve conflict"
```

### サービスが起動しない

**ログを確認:**
```bash
sudo journalctl -u attendance-client-fixed.service -n 100
```

**サービスファイルを確認:**
```bash
sudo nano /etc/systemd/system/attendance-client-fixed.service
# パスが正しいか確認
sudo systemctl daemon-reload
sudo systemctl restart attendance-client-fixed.service
```

---

## 📚 関連ドキュメント

- [Git操作ガイド](GIT_GUIDE.md)
- [トラブルシューティング](TROUBLESHOOTING.md)

