#!/bin/bash
# ============================================================================
# PC/SCサービスへのアクセス権限を修正するスクリプト
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
echo -e "${BLUE}  PC/SCサービスへのアクセス権限を修正${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo ""

# 現在のユーザーを確認
CURRENT_USER=$(whoami)
echo -e "${BLUE}[INFO]${NC} 現在のユーザー: ${CURRENT_USER}"
echo ""

# pcscdグループが存在するか確認
echo -e "${BLUE}[1/4]${NC} pcscdグループを確認中..."
if getent group pcscd > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC} pcscdグループが存在します"
    PCSCD_GROUP_EXISTS=true
else
    echo -e "${YELLOW}⚠️${NC}  pcscdグループが見つかりません"
    PCSCD_GROUP_EXISTS=false
fi
echo ""

# ユーザーがpcscdグループに属しているか確認
echo -e "${BLUE}[2/4]${NC} ユーザーのグループを確認中..."
USER_GROUPS=$(groups)
if echo "$USER_GROUPS" | grep -q "pcscd"; then
    echo -e "${GREEN}✅${NC} ユーザーはpcscdグループに属しています"
    IN_PCSCD_GROUP=true
else
    echo -e "${YELLOW}⚠️${NC}  ユーザーはpcscdグループに属していません"
    IN_PCSCD_GROUP=false
fi
echo "  現在のグループ: $USER_GROUPS"
echo ""

# ユーザーをpcscdグループに追加
if [ "$IN_PCSCD_GROUP" = "false" ] && [ "$PCSCD_GROUP_EXISTS" = "true" ]; then
    echo -e "${BLUE}[3/4]${NC} ユーザーをpcscdグループに追加中..."
    sudo usermod -a -G pcscd "$CURRENT_USER"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅${NC} ユーザーをpcscdグループに追加しました"
        echo -e "${YELLOW}⚠️${NC}  変更を反映するには、ログアウト/ログインが必要です"
        GROUP_ADDED=true
    else
        echo -e "${RED}[ERROR]${NC} グループへの追加に失敗しました"
        GROUP_ADDED=false
    fi
else
    echo -e "${BLUE}[3/4]${NC} グループへの追加は不要です"
    GROUP_ADDED=false
fi
echo ""

# PC/SCサービスの状態を確認
echo -e "${BLUE}[4/4]${NC} PC/SCサービスの状態を確認中..."
if systemctl is-active --quiet pcscd 2>/dev/null; then
    echo -e "${GREEN}✅${NC} PC/SCサービスは起動中です"
else
    echo -e "${YELLOW}⚠️${NC}  PC/SCサービスは停止中です"
    echo "  起動しますか？ (y/N)"
    read -p "> " START_PCSCD
    if [ "$START_PCSCD" = "y" ] || [ "$START_PCSCD" = "Y" ]; then
        sudo systemctl start pcscd
        sleep 2
        if systemctl is-active --quiet pcscd 2>/dev/null; then
            echo -e "${GREEN}✅${NC} PC/SCサービスを起動しました"
        else
            echo -e "${RED}[ERROR]${NC} PC/SCサービスの起動に失敗しました"
        fi
    fi
fi
echo ""

echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN}✅ 完了${NC}"
echo -e "${GREEN}======================================================================${NC}"
echo ""

if [ "$GROUP_ADDED" = "true" ]; then
    echo -e "${YELLOW}重要:${NC}"
    echo "  ユーザーをpcscdグループに追加しました"
    echo "  変更を反映するには、以下を実行してください:"
    echo "    1. ログアウト/ログイン"
    echo "    2. または、新しいターミナルセッションを開始"
    echo ""
fi

echo -e "${BLUE}確認方法:${NC}"
echo "  groups  # pcscdグループが含まれているか確認"
echo "  systemctl status pcscd  # PC/SCサービスの状態を確認"
echo ""

