#!/bin/bash
# 自動起動サービスを開始するスクリプト

# UTF-8環境設定（ロケールが利用可能な場合のみ）
export PYTHONIOENCODING=utf-8
if locale -a | grep -q "ja_JP.utf8\|ja_JP.UTF-8"; then
    export LANG=ja_JP.UTF-8
    export LC_ALL=ja_JP.UTF-8
fi

echo "========================================================================"
echo "  自動起動サービスを開始"
echo "========================================================================"
echo ""

# サービスを開始
echo "[1/2] サービスを開始中..."
sudo systemctl start attendance-client.service

if [ $? -eq 0 ]; then
    echo "✅ サービスを開始しました"
else
    echo "❌ エラーが発生しました"
    exit 1
fi

echo ""
echo "[2/2] 自動起動を有効化中..."
sudo systemctl enable attendance-client.service

if [ $? -eq 0 ]; then
    echo "✅ 自動起動を有効化しました"
else
    echo "⚠️  自動起動の有効化でエラーが発生しました"
fi

echo ""
echo "========================================================================"
echo "完了！"
echo "========================================================================"
echo ""
echo "サービス状態確認:"
echo "  sudo systemctl status attendance-client.service"
echo ""
echo "ログ確認:"
echo "  sudo journalctl -u attendance-client.service -f"
echo ""
echo "サービスを停止する場合:"
echo "  sudo systemctl stop attendance-client.service"
echo ""
echo "========================================================================"

