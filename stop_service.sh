#!/bin/bash
# 自動起動サービスを停止するスクリプト

# UTF-8環境設定（ロケールが利用可能な場合のみ）
export PYTHONIOENCODING=utf-8
if locale -a | grep -q "ja_JP.utf8\|ja_JP.UTF-8"; then
    export LANG=ja_JP.UTF-8
    export LC_ALL=ja_JP.UTF-8
fi

echo "========================================================================"
echo "  自動起動サービスを停止"
echo "========================================================================"
echo ""

# サービスを停止
echo "[1/2] サービスを停止中..."
sudo systemctl stop attendance-client.service

if [ $? -eq 0 ]; then
    echo "✅ サービスを停止しました"
else
    echo "⚠️  サービスが既に停止しているか、エラーが発生しました"
fi

echo ""
echo "[2/2] 自動起動を無効化中..."
sudo systemctl disable attendance-client.service

if [ $? -eq 0 ]; then
    echo "✅ 自動起動を無効化しました"
else
    echo "⚠️  自動起動が既に無効化されているか、エラーが発生しました"
fi

echo ""
echo "========================================================================"
echo "完了！"
echo "========================================================================"
echo ""
echo "サービス状態確認:"
echo "  sudo systemctl status attendance-client.service"
echo ""
echo "サービスを再起動する場合:"
echo "  sudo systemctl start attendance-client.service"
echo ""
echo "自動起動を再有効化する場合:"
echo "  sudo systemctl enable attendance-client.service"
echo ""
echo "========================================================================"

