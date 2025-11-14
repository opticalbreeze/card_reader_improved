#!/bin/bash
# サービス状態確認スクリプト

# UTF-8環境設定（ロケールが利用可能な場合のみ）
export PYTHONIOENCODING=utf-8
if locale -a | grep -q "ja_JP.utf8\|ja_JP.UTF-8"; then
    export LANG=ja_JP.UTF-8
    export LC_ALL=ja_JP.UTF-8
fi

echo "========================================================================"
echo "  サービス状態確認"
echo "========================================================================"
echo ""

# サービス状態
echo "[1] サービス状態:"
sudo systemctl status attendance-client.service --no-pager -l

echo ""
echo "========================================================================"
echo "[2] 最新のログ（最後の50行）:"
echo "========================================================================"
sudo journalctl -u attendance-client.service -n 50 --no-pager

echo ""
echo "========================================================================"
echo "[3] エラーログ（最後の20行）:"
echo "========================================================================"
sudo journalctl -u attendance-client.service -p err -n 20 --no-pager

echo ""
echo "========================================================================"
echo "[4] 設定ファイル確認:"
echo "========================================================================"
if [ -f "/home/raspberry/Desktop/attendance/card_reader_improved/client_config.json" ]; then
    echo "設定ファイルが見つかりました:"
    cat /home/raspberry/Desktop/attendance/card_reader_improved/client_config.json
else
    echo "⚠️  設定ファイルが見つかりません"
fi

echo ""
echo "========================================================================"
echo "[5] ネットワーク接続確認:"
echo "========================================================================"
if [ -f "/home/raspberry/Desktop/attendance/card_reader_improved/client_config.json" ]; then
    SERVER_URL=$(grep -o '"server_url": "[^"]*' /home/raspberry/Desktop/attendance/card_reader_improved/client_config.json | cut -d'"' -f4)
    if [ -n "$SERVER_URL" ]; then
        echo "サーバーURL: $SERVER_URL"
        # サーバーに接続テスト
        SERVER_HOST=$(echo $SERVER_URL | sed -e 's|http://||' -e 's|https://||' | cut -d':' -f1)
        SERVER_PORT=$(echo $SERVER_URL | sed -e 's|http://||' -e 's|https://||' | cut -d':' -f2)
        echo "接続テスト中..."
        timeout 3 bash -c "echo > /dev/tcp/$SERVER_HOST/$SERVER_PORT" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "✅ サーバーに接続できました"
        else
            echo "❌ サーバーに接続できません"
        fi
    else
        echo "⚠️  サーバーURLが設定されていません"
    fi
else
    echo "設定ファイルが見つかりません"
fi

echo ""
echo "========================================================================"

