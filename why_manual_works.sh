#!/bin/bash
# ============================================================================
# なぜ手動起動では動くのかを検証するスクリプト
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
echo -e "${BLUE}  なぜ手動起動では動くのかを検証${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}[1] 手動起動時の環境（現在のターミナルセッション）${NC}"
echo "----------------------------------------"
echo "ユーザー: $(whoami)"
echo "UID: $(id -u)"
echo "GID: $(id -g)"
echo ""
echo "グループ:"
groups | tr ' ' '\n' | sed 's/^/  /'
echo ""
echo "pcscdグループに属しているか:"
if groups | grep -q "pcscd"; then
    echo -e "  ${GREEN}✅ はい${NC}"
else
    echo -e "  ${RED}❌ いいえ${NC}"
fi
echo ""

echo -e "${BLUE}[2] PC/SCサービスへのアクセステスト${NC}"
echo "----------------------------------------"
echo "PC/SCサービスが起動しているか:"
if systemctl is-active --quiet pcscd 2>/dev/null; then
    echo -e "  ${GREEN}✅ 起動中${NC}"
else
    echo -e "  ${RED}❌ 停止中${NC}"
fi
echo ""

echo "PC/SCサービスへのアクセステスト（Pythonから）:"
if [ -d "venv" ]; then
    source venv/bin/activate
    python3 << 'EOF'
try:
    from smartcard.System import readers
    readers_list = readers()
    print(f"  ✅ アクセス成功: {len(readers_list)}台のリーダーを検出")
    for reader in readers_list:
        print(f"     - {reader}")
except Exception as e:
    print(f"  ❌ アクセス失敗: {e}")
EOF
else
    echo "  venvが見つかりません"
fi
echo ""

echo -e "${BLUE}[3] 自動起動時の環境（systemdサービス）${NC}"
echo "----------------------------------------"
SERVICE_PID=$(systemctl show attendance-client-fixed.service -p MainPID --value 2>/dev/null)
if [ -n "$SERVICE_PID" ] && [ "$SERVICE_PID" != "0" ]; then
    echo "サービスプロセスPID: $SERVICE_PID"
    echo ""
    echo "プロセスのユーザー情報:"
    ps -p $SERVICE_PID -o user,uid,gid,group --no-headers 2>/dev/null | awk '{print "  ユーザー: "$1" (UID: "$2", GID: "$3", グループ: "$4")"}'
    echo ""
    echo "プロセスのグループ:"
    sudo cat /proc/$SERVICE_PID/status 2>/dev/null | grep "^Groups:" | sed 's/^Groups:/  /'
    echo ""
    echo "pcscdグループにアクセスできるか:"
    PCSCD_GID=$(getent group pcscd | cut -d: -f3)
    if sudo cat /proc/$SERVICE_PID/status 2>/dev/null | grep "^Groups:" | grep -q "\b${PCSCD_GID}\b"; then
        echo -e "  ${GREEN}✅ はい（GID: ${PCSCD_GID}）${NC}"
    else
        echo -e "  ${RED}❌ いいえ（GID: ${PCSCD_GID}が見つかりません）${NC}"
    fi
else
    echo "サービスは実行されていません"
fi
echo ""

echo -e "${BLUE}[4] 違いの分析${NC}"
echo "----------------------------------------"
echo "手動起動で動く理由:"
echo "  1. ユーザーがログインしているセッションから実行される"
echo "  2. ユーザーのグループメンバーシップが有効"
echo "  3. 環境変数が正しく設定されている"
echo ""
echo "自動起動で動かない理由（推測）:"
echo "  1. systemdサービスとして実行される"
echo "  2. ユーザーのグループメンバーシップが正しく適用されていない可能性"
echo "  3. サービスファイルにGroup=pcscdが設定されていない"
echo ""

echo -e "${BLUE}[5] 解決策${NC}"
echo "----------------------------------------"
echo "1. ユーザーをpcscdグループに追加:"
echo "   sudo usermod -a -G pcscd raspberry"
echo ""
echo "2. サービスファイルにGroup=pcscdを追加（既に修正済み）"
echo ""
echo "3. サービスを再起動:"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl restart attendance-client-fixed.service"
echo ""

echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN}検証完了${NC}"
echo -e "${GREEN}======================================================================${NC}"
echo ""

