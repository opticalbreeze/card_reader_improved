#!/bin/bash
# ============================================================================
# GitHubから最新版を取得するスクリプト（ラズパイ用）
# ============================================================================

# UTF-8環境設定
export PYTHONIOENCODING=utf-8
if locale -a | grep -q "ja_JP.utf8\|ja_JP.UTF-8"; then
    export LANG=ja_JP.UTF-8
    export LC_ALL=ja_JP.UTF-8
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}  GitHubから最新版を取得${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo ""

# スクリプトのディレクトリに移動
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${GREEN}[INFO]${NC} 作業ディレクトリ: $(pwd)"
echo ""

# Gitリポジトリか確認
if [ ! -d ".git" ]; then
    echo -e "${RED}[ERROR]${NC} Gitリポジトリではありません"
    exit 1
fi

# 現在のブランチを確認
CURRENT_BRANCH=$(git branch --show-current)
echo -e "${BLUE}[INFO]${NC} 現在のブランチ: ${CURRENT_BRANCH}"
echo ""

# ローカルの変更があるか確認
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}[1/3]${NC} ローカルの変更を一時保存中..."
    git stash save "Local changes before pull $(date +%Y%m%d_%H%M%S)"
    echo -e "${GREEN}✅${NC} 変更を保存しました"
else
    echo -e "${GREEN}[1/3]${NC} ローカルの変更はありません"
fi
echo ""

# GitHubから最新版を取得
echo -e "${BLUE}[2/3]${NC} GitHubから最新版を取得中..."
git fetch origin

# リモートに更新があるか確認
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u})

if [ "$LOCAL" = "$REMOTE" ]; then
    echo -e "${GREEN}✅${NC} 既に最新版です"
    echo ""
    echo -e "${BLUE}現在のコミット:${NC}"
    git log --oneline -1
else
    echo -e "${YELLOW}更新があります。pullを実行します...${NC}"
    echo ""
    
    # リモートの変更を確認
    echo -e "${BLUE}取得されるコミット:${NC}"
    git log --oneline @..@{u}
    echo ""
    
    # Pull実行
    git pull origin main
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅${NC} 更新完了"
        echo ""
        echo -e "${BLUE}現在のコミット:${NC}"
        git log --oneline -1
    else
        echo -e "${RED}[ERROR]${NC} pullに失敗しました"
        echo ""
        echo -e "${YELLOW}コンフリクトが発生した可能性があります${NC}"
        echo "手動で解決してください:"
        echo "  git status"
        echo "  # コンフリクトを解決後"
        echo "  git add ."
        echo "  git commit"
        exit 1
    fi
fi
echo ""

echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN}✅ 完了${NC}"
echo -e "${GREEN}======================================================================${NC}"
echo ""
echo -e "${BLUE}次のステップ:${NC}"
echo "  1. サービスファイルを更新（必要に応じて）:"
echo "     sudo cp attendance-client-fixed.service /etc/systemd/system/"
echo ""
echo "  2. systemdをリロード:"
echo "     sudo systemctl daemon-reload"
echo ""
echo "  3. サービスを再起動:"
echo "     sudo systemctl restart attendance-client-fixed.service"
echo ""

