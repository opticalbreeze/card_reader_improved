#!/bin/bash
# ============================================================================
# サービス管理スクリプト
# systemdサービスの起動・停止・再起動・ログ確認を簡単に行う
# ============================================================================

# 色付き出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SERVICE_NAME="card-reader.service"

show_usage() {
    echo -e "${BLUE}======================================================================${NC}"
    echo -e "${BLUE}  カードリーダーサービス管理${NC}"
    echo -e "${BLUE}======================================================================${NC}"
    echo ""
    echo "使用方法: $0 [コマンド]"
    echo ""
    echo "コマンド:"
    echo -e "  ${GREEN}start${NC}     サービスを起動"
    echo -e "  ${GREEN}stop${NC}      サービスを停止"
    echo -e "  ${GREEN}restart${NC}   サービスを再起動"
    echo -e "  ${GREEN}status${NC}    サービスの状態を表示"
    echo -e "  ${GREEN}enable${NC}    自動起動を有効化"
    echo -e "  ${GREEN}disable${NC}   自動起動を無効化"
    echo -e "  ${GREEN}log${NC}       ログをリアルタイム表示"
    echo -e "  ${GREEN}log-all${NC}   全てのログを表示"
    echo ""
    echo "例:"
    echo "  $0 start     # サービスを起動"
    echo "  $0 log       # ログをリアルタイム表示"
    echo ""
}

check_service_exists() {
    if ! systemctl list-unit-files | grep -q "$SERVICE_NAME"; then
        echo -e "${RED}[ERROR] サービスが登録されていません${NC}"
        echo -e "${YELLOW}[INFO] ./auto_setup.sh を実行してください${NC}"
        exit 1
    fi
}

case "$1" in
    start)
        echo -e "${BLUE}[INFO] サービスを起動しています...${NC}"
        sudo systemctl start $SERVICE_NAME
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}[OK] サービスを起動しました${NC}"
            echo ""
            sudo systemctl status $SERVICE_NAME --no-pager -l | head -n 15
        else
            echo -e "${RED}[ERROR] サービスの起動に失敗しました${NC}"
            exit 1
        fi
        ;;
    
    stop)
        echo -e "${BLUE}[INFO] サービスを停止しています...${NC}"
        sudo systemctl stop $SERVICE_NAME
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}[OK] サービスを停止しました${NC}"
        else
            echo -e "${RED}[ERROR] サービスの停止に失敗しました${NC}"
            exit 1
        fi
        ;;
    
    restart)
        echo -e "${BLUE}[INFO] サービスを再起動しています...${NC}"
        sudo systemctl restart $SERVICE_NAME
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}[OK] サービスを再起動しました${NC}"
            echo ""
            sudo systemctl status $SERVICE_NAME --no-pager -l | head -n 15
        else
            echo -e "${RED}[ERROR] サービスの再起動に失敗しました${NC}"
            exit 1
        fi
        ;;
    
    status)
        echo -e "${BLUE}[INFO] サービスの状態:${NC}"
        echo ""
        sudo systemctl status $SERVICE_NAME --no-pager -l
        ;;
    
    enable)
        echo -e "${BLUE}[INFO] 自動起動を有効化しています...${NC}"
        sudo systemctl enable $SERVICE_NAME
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}[OK] 自動起動を有効化しました${NC}"
            echo -e "${YELLOW}[INFO] 次回起動時から自動的に起動します${NC}"
        else
            echo -e "${RED}[ERROR] 自動起動の有効化に失敗しました${NC}"
            exit 1
        fi
        ;;
    
    disable)
        echo -e "${BLUE}[INFO] 自動起動を無効化しています...${NC}"
        sudo systemctl disable $SERVICE_NAME
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}[OK] 自動起動を無効化しました${NC}"
            echo -e "${YELLOW}[INFO] 次回起動時は自動的に起動しません${NC}"
        else
            echo -e "${RED}[ERROR] 自動起動の無効化に失敗しました${NC}"
            exit 1
        fi
        ;;
    
    log)
        echo -e "${BLUE}[INFO] ログをリアルタイム表示します (Ctrl+C で終了)${NC}"
        echo ""
        sudo journalctl -u $SERVICE_NAME -f
        ;;
    
    log-all)
        echo -e "${BLUE}[INFO] 全てのログを表示します${NC}"
        echo ""
        sudo journalctl -u $SERVICE_NAME --no-pager
        ;;
    
    *)
        show_usage
        exit 1
        ;;
esac

