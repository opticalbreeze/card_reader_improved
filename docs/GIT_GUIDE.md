# Git操作ガイド

このガイドでは、GitHubへのpush/pull方法を説明します。

---

## 📤 GitHubへのpush

### 基本的なpush手順

```bash
# 1. 変更をステージング
git add .

# 2. コミット
git commit -m "変更内容の説明"

# 3. GitHubにpush
git push origin main
```

### PowerShellでの実行例

```powershell
cd \\nas\nas_1\card_reader_improved

# ファイルを追加
git add pi_client.py win_client.py

# コミット
git commit -m "Refactor: Use common modules for shared functions"

# プッシュ
git push origin main
```

### エラーが出る場合

```bash
# 強制プッシュ（注意：通常は使用しない）
git push origin main --force
```

---

## 📥 GitHubからpull

### ラズパイでのpull

```bash
cd ~/Desktop/attendance/card_reader_improved

# ローカルの変更を一時保存（ある場合）
git stash

# GitHubから最新版を取得
git pull origin main

# 必要に応じて変更を戻す
git stash pop
```

### Windowsでのpull

```cmd
cd C:\Users\optic\Desktop\card_reader_improved
git pull origin main
```

---

## 🔄 更新の適用

### ラズパイでの更新適用

```bash
cd ~/Desktop/attendance/card_reader_improved

# 1. GitHubから最新版を取得
git pull origin main

# 2. サービスファイルを更新（必要な場合）
sudo cp attendance-client-fixed.service /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/attendance-client-fixed.service

# 3. systemdをリロード
sudo systemctl daemon-reload

# 4. サービスを再起動
sudo systemctl restart attendance-client-fixed.service

# 5. 状態を確認
sudo systemctl status attendance-client-fixed.service
```

---

## ⚠️ 注意事項

- **コミット前に動作確認**: pushする前に必ず動作確認を行ってください
- **コミットメッセージ**: 変更内容が分かるように明確なメッセージを記述してください
- **強制プッシュ**: `--force`オプションは通常使用しないでください（他の人の作業を上書きする可能性があります）

