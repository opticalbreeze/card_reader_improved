#!/bin/bash
# GitHubから最新のコードをプルするスクリプト（ラズパイ用）

echo "========================================"
echo "GitHubから最新のコードをプル"
echo "========================================"
echo ""

# 現在のディレクトリを確認
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"
echo "作業ディレクトリ: $(pwd)"
echo ""

# Gitリポジトリの確認
if [ ! -d ".git" ]; then
    echo "エラー: このディレクトリはGitリポジトリではありません"
    echo ""
    echo "初回セットアップの場合、以下のコマンドを実行してください:"
    echo "  git clone https://github.com/opticalbreeze/card_reader_improved.git ."
    echo ""
    exit 1
fi

# リモートリポジトリの確認
echo "[1/3] リモートリポジトリを確認しています..."
REMOTE_URL=$(git remote get-url origin 2>/dev/null)
if [ $? -ne 0 ]; then
    echo "リモートリポジトリが設定されていません。設定します..."
    git remote add origin https://github.com/opticalbreeze/card_reader_improved.git
    if [ $? -ne 0 ]; then
        echo "エラー: リモートリポジトリの設定に失敗しました"
        exit 1
    fi
    echo "リモートリポジトリを設定しました"
else
    echo "リモートリポジトリ: $REMOTE_URL"
fi
echo ""

# 現在のブランチを確認
echo "[2/3] 現在のブランチを確認しています..."
CURRENT_BRANCH=$(git branch --show-current)
if [ -z "$CURRENT_BRANCH" ]; then
    echo "ブランチが存在しません。mainブランチに切り替えます..."
    git checkout -b main
    CURRENT_BRANCH="main"
fi
echo "現在のブランチ: $CURRENT_BRANCH"
echo ""

# ローカルの変更を確認
echo "[3/3] ローカルの変更を確認しています..."
if [ -n "$(git status --porcelain)" ]; then
    echo "警告: ローカルに未コミットの変更があります"
    echo ""
    echo "以下のオプションを選択してください:"
    echo "1. 変更を保存してからプル（stash）"
    echo "2. 変更を破棄してからプル"
    echo "3. キャンセル"
    echo ""
    read -p "選択 (1/2/3): " choice
    
    case $choice in
        1)
            echo "変更を保存しています..."
            git stash
            echo "変更を保存しました"
            ;;
        2)
            echo "変更を破棄しています..."
            git reset --hard HEAD
            echo "変更を破棄しました"
            ;;
        3)
            echo "キャンセルしました"
            exit 0
            ;;
        *)
            echo "無効な選択です。キャンセルしました"
            exit 1
            ;;
    esac
    echo ""
fi

# 最新のコードをプル
echo "GitHubから最新のコードを取得しています..."
git pull origin $CURRENT_BRANCH

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "プルが完了しました！"
    echo "========================================"
    echo ""
    
    # 保存した変更を復元（stashした場合）
    if [ "$choice" = "1" ]; then
        echo "保存した変更を復元しますか？ (y/n)"
        read -p "選択: " restore_choice
        if [ "$restore_choice" = "y" ] || [ "$restore_choice" = "Y" ]; then
            git stash pop
            if [ $? -ne 0 ]; then
                echo "警告: 変更の復元で競合が発生しました。手動で解決してください"
            else
                echo "変更を復元しました"
            fi
        fi
    fi
    
    echo ""
    echo "最新のファイル一覧:"
    git log -1 --oneline
    echo ""
else
    echo ""
    echo "エラー: プルに失敗しました"
    echo ""
    echo "考えられる原因:"
    echo "1. ネットワーク接続の問題"
    echo "2. リモートリポジトリへのアクセス権限がない"
    echo "3. 競合が発生している"
    echo ""
    echo "対処法:"
    echo "- ネットワーク接続を確認してください"
    echo "- リモートリポジトリのURLを確認してください"
    echo "- 競合を解決してください: git status"
    exit 1
fi

