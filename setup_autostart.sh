#!/bin/bash
################################################################################
# ラズパイ版自動起動設定スクリプト
################################################################################
#
# このスクリプトは、ラズパイ起動時に打刻システムを自動起動するように設定します
#
# 使い方：
#   sudo bash setup_autostart.sh
#
################################################################################

set -e

echo "========================================"
echo "打刻システム - 自動起動設定"
echo "========================================"
echo ""

# rootユーザーで実行されているか確認
if [ "$EUID" -ne 0 ]; then
    echo "[エラー] このスクリプトはroot権限で実行する必要があります"
    echo "[実行] sudo bash setup_autostart.sh"
    exit 1
fi

# カレントディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "[情報] プロジェクトディレクトリ: $SCRIPT_DIR"
echo ""

# ユーザー名を取得（sudoで実行された場合は元のユーザー）
if [ -n "$SUDO_USER" ]; then
    REAL_USER="$SUDO_USER"
else
    REAL_USER="pi"
fi
echo "[情報] 実行ユーザー: $REAL_USER"
echo ""

# pi_client.py の存在確認
if [ ! -f "$SCRIPT_DIR/pi_client.py" ]; then
    echo "[エラー] pi_client.py が見つかりません"
    echo "[ヒント] このスクリプトをプロジェクトのルートディレクトリで実行してください"
    exit 1
fi

# systemdサービスファイルを作成
SERVICE_FILE="/etc/systemd/system/attendance-client.service"
echo "[作成] systemdサービスファイルを作成します..."
echo "[場所] $SERVICE_FILE"

cat > "$SERVICE_FILE" << EOF
[Unit]
Description=ICカード勤怠管理システム - ラズパイクライアント
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$REAL_USER
WorkingDirectory=$SCRIPT_DIR
ExecStart=/usr/bin/python3 $SCRIPT_DIR/pi_client.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# 環境変数
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
EOF

echo "[OK] サービスファイルを作成しました"
echo ""

# systemdをリロード
echo "[実行] systemdをリロード中..."
systemctl daemon-reload
echo "[OK] リロード完了"
echo ""

# サービスを有効化
echo "[実行] サービスを有効化中..."
systemctl enable attendance-client.service
echo "[OK] サービスを有効化しました（再起動時に自動起動されます）"
echo ""

# サービスの状態を確認
echo "========================================"
echo "設定完了"
echo "========================================"
echo ""
echo "サービス名: attendance-client.service"
echo "状態確認: sudo systemctl status attendance-client"
echo "起動: sudo systemctl start attendance-client"
echo "停止: sudo systemctl stop attendance-client"
echo "再起動: sudo systemctl restart attendance-client"
echo "ログ確認: sudo journalctl -u attendance-client -f"
echo "自動起動無効化: sudo systemctl disable attendance-client"
echo ""
echo "[情報] 次回のラズパイ起動時から自動起動されます"
echo "[情報] 今すぐ起動する場合は: sudo systemctl start attendance-client"
echo ""

# 今すぐ起動するか確認
read -p "今すぐサービスを起動しますか？ (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "[実行] サービスを起動中..."
    systemctl start attendance-client.service
    sleep 2
    echo ""
    echo "[状態確認]"
    systemctl status attendance-client.service --no-pager
    echo ""
    echo "[OK] サービスを起動しました"
else
    echo "[スキップ] サービスの起動をスキップしました"
fi

echo ""
echo "========================================"
echo "完了"
echo "========================================"

