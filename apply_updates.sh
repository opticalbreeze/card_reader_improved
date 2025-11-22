#!/bin/bash
# ============================================================================
# 更新を適用するスクリプト（サービスファイルの更新と再起動）
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
echo -e "${BLUE}  更新を適用${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# サービスファイルを更新
echo -e "${BLUE}[1/4]${NC} サービスファイルを更新中..."
if [ -f "attendance-client-fixed.service" ]; then
    SERVICE_FILE_PATH="/etc/systemd/system/attendance-client-fixed.service"
    
    # サービスファイルをコピー
    sudo cp attendance-client-fixed.service "$SERVICE_FILE_PATH"
    sudo chmod 644 "$SERVICE_FILE_PATH"
    echo -e "${GREEN}✅${NC} サービスファイルを更新しました"
else
    echo -e "${RED}[ERROR]${NC} attendance-client-fixed.serviceが見つかりません"
    exit 1
fi
echo ""

# systemdをリロード
echo -e "${BLUE}[2/4]${NC} systemdをリロード中..."
sudo systemctl daemon-reload
echo -e "${GREEN}✅${NC} リロード完了"
echo ""

# サービスを再起動
echo -e "${BLUE}[3/4]${NC} サービスを再起動中..."
sudo systemctl restart attendance-client-fixed.service
sleep 2
echo -e "${GREEN}✅${NC} サービスを再起動しました"
echo ""

# サービス状態を確認
echo -e "${BLUE}[4/4]${NC} サービス状態を確認中..."
sudo systemctl status attendance-client-fixed.service --no-pager -l | head -30
echo ""

echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN}✅ 適用完了${NC}"
echo -e "${GREEN}======================================================================${NC}"
echo ""
echo -e "${BLUE}ログを確認:${NC}"
echo "  sudo journalctl -u attendance-client-fixed.service -f"
echo ""

