# ラズパイで最新のコードをプルする方法

## 📋 概要

ラズパイでGitHubから最新のコードを取得（プル）する方法を説明します。

## 🚀 方法1: スクリプトを使用（簡単・推奨）

### 初回セットアップ

1. **リポジトリをクローン**

```bash
cd ~
git clone https://github.com/opticalbreeze/card_reader_improved.git
cd card_reader_improved
```

### スクリプトの実行

1. **スクリプトに実行権限を付与**

```bash
chmod +x pull_on_raspberry_pi.sh
```

2. **スクリプトを実行**

```bash
./pull_on_raspberry_pi.sh
```

スクリプトが自動的に以下を実行します：
- リモートリポジトリの確認
- 現在のブランチの確認
- ローカルの変更の確認
- 最新のコードをプル

## 🔧 方法2: 手動でコマンドを実行

### 初回セットアップ

```bash
# 1. 作業ディレクトリに移動
cd ~/card_reader_improved

# 2. リモートリポジトリを確認
git remote -v

# 3. リモートが設定されていない場合
git remote add origin https://github.com/opticalbreeze/card_reader_improved.git
```

### 最新のコードをプル

```bash
# 1. 作業ディレクトリに移動
cd ~/card_reader_improved

# 2. 現在のブランチを確認
git branch

# 3. 最新のコードをプル
git pull origin main
```

**注意**: ブランチ名が `master` の場合は、以下のコマンドを使用してください：

```bash
git pull origin master
```

## ⚠️ ローカルに変更がある場合

### 変更を保存してからプル（推奨）

```bash
# 1. 変更を一時的に保存
git stash

# 2. 最新のコードをプル
git pull origin main

# 3. 保存した変更を復元
git stash pop
```

### 変更を破棄してからプル

**警告**: この方法は、ローカルの変更を完全に削除します。

```bash
# 1. すべての変更を破棄
git reset --hard HEAD

# 2. 最新のコードをプル
git pull origin main
```

## 🔍 現在の状態を確認

### リモートリポジトリの確認

```bash
git remote -v
```

### 現在のブランチの確認

```bash
git branch
```

### ローカルの変更の確認

```bash
git status
```

### 最新のコミット履歴を確認

```bash
git log --oneline -5
```

## 📝 よくあるシナリオ

### シナリオ1: 初めてコードを取得する

```bash
# ホームディレクトリに移動
cd ~

# リポジトリをクローン
git clone https://github.com/opticalbreeze/card_reader_improved.git

# ディレクトリに移動
cd card_reader_improved

# 依存関係をインストール
pip3 install -r requirements_unified.txt
```

### シナリオ2: 既存のリポジトリを更新する

```bash
# 作業ディレクトリに移動
cd ~/card_reader_improved

# 最新のコードをプル
git pull origin main

# 依存関係を更新（必要に応じて）
pip3 install -r requirements_unified.txt --upgrade
```

### シナリオ3: ローカルの変更を保持しながら更新

```bash
# 作業ディレクトリに移動
cd ~/card_reader_improved

# 変更を保存
git stash

# 最新のコードをプル
git pull origin main

# 保存した変更を復元
git stash pop

# 競合が発生した場合、手動で解決
# 競合ファイルを編集してから:
git add <競合ファイル>
git commit -m "競合を解決"
```

## 🛠️ トラブルシューティング

### エラー: "fatal: not a git repository"

**原因**: 現在のディレクトリがGitリポジトリではありません。

**対処法**:
```bash
# リポジトリをクローン
git clone https://github.com/opticalbreeze/card_reader_improved.git
cd card_reader_improved
```

### エラー: "fatal: remote origin already exists"

**原因**: リモートリポジトリが既に設定されています。

**対処法**: このエラーは無視して問題ありません。次のステップに進んでください。

### エラー: "Your local changes would be overwritten by merge"

**原因**: ローカルに未コミットの変更があります。

**対処法**:
```bash
# 変更を保存
git stash

# プル
git pull origin main

# 変更を復元
git stash pop
```

### エラー: "CONFLICT (content): Merge conflict"

**原因**: ローカルの変更とリモートの変更が競合しています。

**対処法**:
1. 競合ファイルを開く
2. 競合部分を確認（`<<<<<<<`, `=======`, `>>>>>>>` で囲まれた部分）
3. 必要な変更を残して、競合マーカーを削除
4. ファイルを保存
5. 以下のコマンドを実行：

```bash
git add <競合ファイル>
git commit -m "競合を解決"
```

### エラー: "Permission denied (publickey)"

**原因**: SSH認証が設定されていません。

**対処法**: HTTPSを使用するか、SSH認証を設定してください。

**HTTPSを使用する場合**:
```bash
git remote set-url origin https://github.com/opticalbreeze/card_reader_improved.git
```

## 📚 便利なコマンド

### 最新の変更内容を確認（プル前）

```bash
git fetch origin
git log HEAD..origin/main --oneline
```

### 特定のファイルだけを更新

```bash
# 特定のファイルを取得
git checkout origin/main -- <ファイル名>
```

### リモートのブランチ一覧を確認

```bash
git branch -r
```

### リモートの最新情報を取得（プルしない）

```bash
git fetch origin
```

## 🔄 自動更新スクリプト（オプション）

定期的に自動更新したい場合、cronを使用できます：

```bash
# crontabを編集
crontab -e

# 以下の行を追加（毎日午前3時に更新）
0 3 * * * cd ~/card_reader_improved && git pull origin main
```

## 📞 サポート

問題が解決しない場合は、以下の情報を含めてお問い合わせください：
- エラーメッセージ
- 実行したコマンド
- `git status` の出力

---

**更新日**: 2025年1月

