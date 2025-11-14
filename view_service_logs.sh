#!/bin/bash
# サービスログを確認するスクリプト

# UTF-8環境設定（ロケールが利用可能な場合のみ）
export PYTHONIOENCODING=utf-8
if locale -a | grep -q "ja_JP.utf8\|ja_JP.UTF-8"; then
    export LANG=ja_JP.UTF-8
    export LC_ALL=ja_JP.UTF-8
fi

echo "========================================================================"
echo "  サービスログ確認"
echo "========================================================================"
echo ""

# サービス状態
echo "[1] サービス状態:"
sudo systemctl status attendance-client.service --no-pager -l | head -20

echo ""
echo "========================================================================"
echo "[2] 最新のログ（最後の100行）:"
echo "========================================================================"
sudo journalctl -u attendance-client.service -n 100 --no-pager

echo ""
echo "========================================================================"
echo "[3] エラーログ（最後の50行）:"
echo "========================================================================"
sudo journalctl -u attendance-client.service -p err -n 50 --no-pager

echo ""
echo "========================================================================"
echo "[4] 起動時のエラー（最初の50行）:"
echo "========================================================================"
sudo journalctl -u attendance-client.service --no-pager | head -50

echo ""
echo "========================================================================"
echo ""
echo "リアルタイムログを確認する場合:"
echo "  sudo journalctl -u attendance-client.service -f"
echo ""
echo "========================================================================"

