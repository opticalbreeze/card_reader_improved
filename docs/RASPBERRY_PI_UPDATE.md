# ラズパイ側を最新状態にする方法

## 概要

GitHubにプッシュされた最新のコードをラズパイ側に反映する手順です。

## ローカルの変更がある場合の対処法

### ステップ1: ローカルの変更を確認

```bash
git status
git diff
```

### ステップ2: ローカルの変更を破棄して最新状態にする（推奨）

ラズパイ側のローカル変更は通常不要なので、破棄して最新状態にすることを推奨します：

```bash
# ローカルの変更を全て破棄
git reset --hard origin/main

# 最新のコードを取得（念のため）
git pull origin main
```

### ステップ3: ローカルの変更を保持したい場合

もしローカルの変更を保持したい場合は：

```bash
# ローカルの変更を一時保存
git stash

# 最新のコードを取得
git pull origin main

# 保存した変更を復元（必要に応じて）
git stash pop
```

---

## トラブルシューティング

### git pullで競合エラーが出る場合

以下のコマンドで解決できます：

```bash
# 方法1: ローカルの変更を破棄（推奨）
git reset --hard origin/main
git pull origin main

# 方法2: ローカルの変更を保持
git stash
git pull origin main
git stash pop
```

### 動作確認

更新後、以下のコマンドで動作確認：

```bash
cd ~/Desktop/card_reader_improved
source venv/bin/activate
python3 config.py
```

---

## 完全な手順（コピー＆ペースト用）

```bash
# 1. プロジェクトディレクトリに移動
cd ~/Desktop/card_reader_improved

# 2. ローカルの変更を破棄して最新状態にする
git reset --hard origin/main

# 3. 最新のコードを取得
git pull origin main

# 4. 仮想環境を有効化
source venv/bin/activate

# 5. 動作確認
python3 config.py
```
