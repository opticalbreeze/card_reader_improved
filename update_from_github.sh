#!/bin/bash
# GitHubから最新版を取得するスクリプト（ローカル変更を一時保存）

# UTF-8環境設定（ロケールが利用可能な場合のみ）
export PYTHONIOENCODING=utf-8
if locale -a | grep -q "ja_JP.utf8\|ja_JP.UTF-8"; then
    export LANG=ja_JP.UTF-8
    export LC_ALL=ja_JP.UTF-8
fi

echo "========================================================================"
echo "  GitHubから最新版を取得"
echo "========================================================================"
echo ""

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"

# ローカルの変更があるか確認
if [ -n "$(git status --porcelain)" ]; then
    echo "[1/3] ローカルの変更を一時保存中..."
    git stash save "Local changes before pull $(date +%Y%m%d_%H%M%S)"
    echo "✅ 変更を保存しました"
else
    echo "[1/3] ローカルの変更はありません"
fi

echo ""
echo "[2/3] GitHubから最新版を取得中..."
git pull origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "[3/3] ✅ 更新完了！"
    echo ""
    echo "一時保存した変更を確認するには:"
    echo "  git stash list"
    echo ""
    echo "一時保存した変更を適用するには:"
    echo "  git stash pop"
else
    echo ""
    echo "❌ エラーが発生しました"
    exit 1
fi

echo "========================================================================"

