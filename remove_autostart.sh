#!/bin/bash
################################################################################
# ラズパイ版自動起動解除スクリプト
################################################################################
#
# このスクリプトは、打刻システムの自動起動設定を解除します
#
# 使い方：
#   sudo bash remove_autostart.sh
#
################################################################################

set -e

echo "========================================"
echo "打刻システム - 自動起動解除"
echo "========================================"
echo ""

# rootユーザーで実行されているか確認
if [ "$EUID" -ne 0 ]; then
    echo "[エラー] このスクリプトはroot権限で実行する必要があります"
    echo "[実行] sudo bash remove_autostart.sh"
    exit 1
fi

SERVICE_NAME="attendance-client.service"

# サービスが存在するか確認
if ! systemctl list-unit-files | grep -q "$SERVICE_NAME"; then
    echo "[情報] サービス $SERVICE_NAME は登録されていません"
    exit 0
fi

# サービスが実行中か確認
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "[実行] サービスを停止中..."
    systemctl stop "$SERVICE_NAME"
    echo "[OK] サービスを停止しました"
    echo ""
fi

# 自動起動を無効化
if systemctl is-enabled --quiet "$SERVICE_NAME"; then
    echo "[実行] 自動起動を無効化中..."
    systemctl disable "$SERVICE_NAME"
    echo "[OK] 自動起動を無効化しました"
    echo ""
fi

# サービスファイルを削除
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME"
if [ -f "$SERVICE_FILE" ]; then
    echo "[実行] サービスファイルを削除中..."
    rm "$SERVICE_FILE"
    echo "[OK] サービスファイルを削除しました"
    echo ""
fi

# systemdをリロード
echo "[実行] systemdをリロード中..."
systemctl daemon-reload
echo "[OK] リロード完了"
echo ""

echo "========================================"
echo "完了"
echo "========================================"
echo ""
echo "[OK] 自動起動設定を解除しました"
echo "[情報] 次回のラズパイ起動時から自動起動されません"
echo ""

