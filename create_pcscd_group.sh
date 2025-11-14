#!/bin/bash
# ============================================================================
# pcscdグループを作成してユーザーを追加するスクリプト
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
echo -e "${BLUE}  pcscdグループを作成してユーザーを追加${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo ""

CURRENT_USER=$(whoami)
echo -e "${BLUE}[INFO]${NC} 現在のユーザー: ${CURRENT_USER}"
echo ""

# pcscdグループが存在するか確認
echo -e "${BLUE}[1/3]${NC} pcscdグループを確認中..."
if getent group pcscd > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC} pcscdグループが存在します"
    GROUP_EXISTS=true
else
    echo -e "${YELLOW}⚠️${NC}  pcscdグループが存在しません"
    GROUP_EXISTS=false
fi
echo ""

# グループを作成
if [ "$GROUP_EXISTS" = "false" ]; then
    echo -e "${BLUE}[2/3]${NC} pcscdグループを作成中..."
    sudo groupadd pcscd
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅${NC} pcscdグループを作成しました"
        GROUP_EXISTS=true
    else
        echo -e "${RED}[ERROR]${NC} グループの作成に失敗しました"
        exit 1
    fi
else
    echo -e "${BLUE}[2/3]${NC} グループの作成は不要です"
fi
echo ""

# ユーザーをグループに追加
if [ "$GROUP_EXISTS" = "true" ]; then
    echo -e "${BLUE}[3/3]${NC} ユーザーをpcscdグループに追加中..."
    sudo usermod -a -G pcscd "$CURRENT_USER"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅${NC} ユーザーをpcscdグループに追加しました"
        echo ""
        echo -e "${YELLOW}⚠️${NC}  変更を反映するには、ログアウト/ログインが必要です"
        echo ""
        echo "現在のグループ:"
        groups | tr ' ' '\n' | sed 's/^/  /'
        echo ""
        echo "新しいグループ（ログアウト/ログイン後）:"
        echo "  groups  # pcscdが含まれているはずです"
    else
        echo -e "${RED}[ERROR]${NC} グループへの追加に失敗しました"
        exit 1
    fi
fi
echo ""

echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN}✅ 完了${NC}"
echo -e "${GREEN}======================================================================${NC}"
echo ""
echo -e "${BLUE}次のステップ:${NC}"
echo "  1. ログアウト/ログイン（または新しいターミナルセッションを開始）"
echo "  2. groups コマンドでpcscdグループが含まれているか確認"
echo "  3. サービスファイルを更新"
echo "  4. サービスを再起動"
echo ""

