#!/bin/bash
# ============================================================================
# ラズパイ版自動起動設定スクリプト（改善版）
# attendance-client-fixed.service を使用
# ============================================================================

set -e

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
echo -e "${BLUE}  打刻システム - 自動起動設定（改善版）${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo ""

# rootユーザーで実行されているか確認
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[エラー] このスクリプトはroot権限で実行する必要があります${NC}"
    echo -e "${YELLOW}[実行] sudo bash setup_autostart_fixed.sh${NC}"
    exit 1
fi

# カレントディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo -e "${GREEN}[情報]${NC} プロジェクトディレクトリ: ${SCRIPT_DIR}"
echo ""

# ユーザー名を取得（sudoで実行された場合は元のユーザー）
if [ -n "$SUDO_USER" ]; then
    REAL_USER="$SUDO_USER"
else
    # デフォルトユーザーを確認
    if id "raspberry" &>/dev/null; then
        REAL_USER="raspberry"
    else
        REAL_USER="pi"
    fi
fi
echo -e "${GREEN}[情報]${NC} 実行ユーザー: ${REAL_USER}"
echo ""

# pi_client.py の存在確認
if [ ! -f "$SCRIPT_DIR/pi_client.py" ]; then
    echo -e "${RED}[エラー]${NC} pi_client.py が見つかりません"
    echo -e "${YELLOW}[ヒント]${NC} このスクリプトをプロジェクトのルートディレクトリで実行してください"
    exit 1
fi

# attendance-client-fixed.service の存在確認
if [ ! -f "$SCRIPT_DIR/attendance-client-fixed.service" ]; then
    echo -e "${RED}[エラー]${NC} attendance-client-fixed.service が見つかりません"
    echo -e "${YELLOW}[ヒント]${NC} GitHubから最新版を取得してください: git pull origin main"
    exit 1
fi

# サービスファイルのパスを更新
echo -e "${BLUE}[1/5]${NC} サービスファイルを準備中..."
SERVICE_FILE="/etc/systemd/system/attendance-client-fixed.service"

# サービスファイルをコピーしてパスを更新
sed "s|/home/raspberry/Desktop/attendance/card_reader_improved|$SCRIPT_DIR|g" \
    "$SCRIPT_DIR/attendance-client-fixed.service" > "$SERVICE_FILE"

# ユーザー名を更新（raspberry以外の場合）
if [ "$REAL_USER" != "raspberry" ]; then
    sed -i "s/User=raspberry/User=$REAL_USER/g" "$SERVICE_FILE"
fi

echo -e "${GREEN}[OK]${NC} サービスファイルを作成しました: $SERVICE_FILE"
echo ""

# pcscdグループの確認と作成
echo -e "${BLUE}[2/5]${NC} pcscdグループを確認中..."
if getent group pcscd > /dev/null 2>&1; then
    echo -e "${GREEN}[OK]${NC} pcscdグループが存在します"
else
    echo -e "${YELLOW}[作成]${NC} pcscdグループを作成中..."
    groupadd pcscd
    echo -e "${GREEN}[OK]${NC} pcscdグループを作成しました"
fi

# ユーザーをpcscdグループに追加
if groups "$REAL_USER" | grep -q '\bpcscd\b'; then
    echo -e "${GREEN}[OK]${NC} ユーザー $REAL_USER は既にpcscdグループに所属しています"
else
    echo -e "${YELLOW}[追加]${NC} ユーザー $REAL_USER をpcscdグループに追加中..."
    usermod -a -G pcscd "$REAL_USER"
    echo -e "${GREEN}[OK]${NC} ユーザーをpcscdグループに追加しました"
    echo -e "${YELLOW}[注意]${NC} グループの変更を反映するには、ログアウト/ログインが必要です"
fi
echo ""

# systemdをリロード
echo -e "${BLUE}[3/5]${NC} systemdをリロード中..."
systemctl daemon-reload
echo -e "${GREEN}[OK]${NC} リロード完了"
echo ""

# 古いサービスを無効化（存在する場合）
if systemctl list-unit-files | grep -q "attendance-client.service"; then
    echo -e "${YELLOW}[無効化]${NC} 古いサービスを無効化中..."
    systemctl stop attendance-client.service 2>/dev/null || true
    systemctl disable attendance-client.service 2>/dev/null || true
    echo -e "${GREEN}[OK]${NC} 古いサービスを無効化しました"
    echo ""
fi

# サービスを有効化
echo -e "${BLUE}[4/5]${NC} サービスを有効化中..."
systemctl enable attendance-client-fixed.service
echo -e "${GREEN}[OK]${NC} サービスを有効化しました（再起動時に自動起動されます）"
echo ""

# サービスの状態を確認
echo -e "${BLUE}[5/5]${NC} サービスの状態を確認中..."
echo ""
systemctl status attendance-client-fixed.service --no-pager || true
echo ""

# 完了メッセージ
echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN}  設定完了${NC}"
echo -e "${GREEN}======================================================================${NC}"
echo ""
echo -e "${BLUE}サービス名:${NC} attendance-client-fixed.service"
echo ""
echo -e "${BLUE}【便利なコマンド】${NC}"
echo ""
echo -e "  状態確認:"
echo -e "    ${GREEN}sudo systemctl status attendance-client-fixed.service${NC}"
echo ""
echo -e "  起動:"
echo -e "    ${GREEN}sudo systemctl start attendance-client-fixed.service${NC}"
echo ""
echo -e "  停止:"
echo -e "    ${GREEN}sudo systemctl stop attendance-client-fixed.service${NC}"
echo ""
echo -e "  再起動:"
echo -e "    ${GREEN}sudo systemctl restart attendance-client-fixed.service${NC}"
echo ""
echo -e "  ログ確認:"
echo -e "    ${GREEN}sudo journalctl -u attendance-client-fixed.service -f${NC}"
echo ""
echo -e "  自動起動無効化:"
echo -e "    ${GREEN}sudo systemctl disable attendance-client-fixed.service${NC}"
echo ""
echo -e "${YELLOW}[情報]${NC} 次回のラズパイ起動時から自動起動されます"
echo -e "${YELLOW}[情報]${NC} 今すぐ起動する場合は: sudo systemctl start attendance-client-fixed.service"
echo ""

# 今すぐ起動するか確認
read -p "今すぐサービスを起動しますか？ (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}[実行]${NC} サービスを起動中..."
    systemctl start attendance-client-fixed.service
    sleep 2
    echo ""
    echo -e "${BLUE}[状態確認]${NC}"
    systemctl status attendance-client-fixed.service --no-pager
    echo ""
    echo -e "${GREEN}[OK]${NC} サービスを起動しました"
else
    echo -e "${YELLOW}[スキップ]${NC} サービスの起動をスキップしました"
fi

echo ""
echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN}  完了${NC}"
echo -e "${GREEN}======================================================================${NC}"
echo ""

