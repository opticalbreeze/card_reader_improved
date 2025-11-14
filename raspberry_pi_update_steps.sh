#!/bin/bash
# ============================================================================
# ラズパイ側での更新手順スクリプト
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
echo -e "${BLUE}  ラズパイ側での更新手順${NC}"
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
    echo -e "${YELLOW}[1/6]${NC} ローカルの変更を一時保存中..."
    git stash save "Local changes before update $(date +%Y%m%d_%H%M%S)"
    echo -e "${GREEN}✅${NC} 変更を保存しました"
else
    echo -e "${GREEN}[1/6]${NC} ローカルの変更はありません"
fi
echo ""

# GitHubから最新版を取得
echo -e "${BLUE}[2/6]${NC} GitHubから最新版を取得中..."
git fetch origin
if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR]${NC} fetchに失敗しました"
    exit 1
fi

# リモートに更新があるか確認
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u})

if [ "$LOCAL" = "$REMOTE" ]; then
    echo -e "${GREEN}✅${NC} 既に最新版です"
    UPDATE_NEEDED=false
else
    echo -e "${YELLOW}更新があります。pullを実行します...${NC}"
    git pull origin main
    if [ $? -ne 0 ]; then
        echo -e "${RED}[ERROR]${NC} pullに失敗しました"
        echo -e "${YELLOW}コンフリクトが発生した可能性があります${NC}"
        exit 1
    fi
    UPDATE_NEEDED=true
    echo -e "${GREEN}✅${NC} 更新完了"
fi
echo ""

# サービスファイルを確認
echo -e "${BLUE}[3/6]${NC} サービスファイルの確認..."
if [ -f "attendance-client-fixed.service" ]; then
    echo -e "${GREEN}✅${NC} attendance-client-fixed.serviceが見つかりました"
    SERVICE_FILE_PATH="/etc/systemd/system/attendance-client-fixed.service"
    
    # サービスファイルをコピーするか確認
    if [ ! -f "$SERVICE_FILE_PATH" ] || ! diff -q "attendance-client-fixed.service" "$SERVICE_FILE_PATH" > /dev/null 2>&1; then
        echo -e "${YELLOW}[4/6]${NC} サービスファイルを更新しますか？ (y/N)"
        read -p "> " UPDATE_SERVICE
        if [ "$UPDATE_SERVICE" = "y" ] || [ "$UPDATE_SERVICE" = "Y" ]; then
            echo "  サービスファイルをコピー中..."
            sudo cp attendance-client-fixed.service "$SERVICE_FILE_PATH"
            sudo chmod 644 "$SERVICE_FILE_PATH"
            echo -e "${GREEN}✅${NC} サービスファイルを更新しました"
            SERVICE_UPDATED=true
        else
            echo -e "${YELLOW}スキップしました${NC}"
            SERVICE_UPDATED=false
        fi
    else
        echo -e "${GREEN}✅${NC} サービスファイルは既に最新です"
        SERVICE_UPDATED=false
    fi
else
    echo -e "${YELLOW}[WARNING]${NC} attendance-client-fixed.serviceが見つかりません"
    SERVICE_UPDATED=false
fi
echo ""

# systemdをリロード
if [ "$SERVICE_UPDATED" = "true" ]; then
    echo -e "${BLUE}[5/6]${NC} systemdをリロード中..."
    sudo systemctl daemon-reload
    echo -e "${GREEN}✅${NC} リロード完了"
else
    echo -e "${BLUE}[5/6]${NC} systemdのリロードは不要です"
fi
echo ""

# サービスを再起動するか確認
echo -e "${BLUE}[6/6]${NC} サービスを再起動しますか？ (y/N)"
read -p "> " RESTART_SERVICE
if [ "$RESTART_SERVICE" = "y" ] || [ "$RESTART_SERVICE" = "Y" ]; then
    echo "  サービスを再起動中..."
    sudo systemctl restart attendance-client-fixed.service
    sleep 2
    echo -e "${GREEN}✅${NC} サービスを再起動しました"
    echo ""
    echo "  サービス状態:"
    sudo systemctl status attendance-client-fixed.service --no-pager -l | head -20
else
    echo -e "${YELLOW}スキップしました${NC}"
    echo ""
    echo "手動で再起動する場合:"
    echo "  sudo systemctl restart attendance-client-fixed.service"
fi
echo ""

echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN}✅ 更新完了${NC}"
echo -e "${GREEN}======================================================================${NC}"
echo ""
echo -e "${BLUE}次のステップ:${NC}"
echo "  1. サービスログを確認:"
echo "     sudo journalctl -u attendance-client-fixed.service -f"
echo ""
echo "  2. プロセス環境を検証（オプション）:"
echo "     chmod +x check_actual_difference.sh"
echo "     ./check_actual_difference.sh"
echo ""

