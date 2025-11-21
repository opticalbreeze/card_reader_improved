#!/bin/bash
# SSHでラズパイにシンプル版を送信するスクリプト（Linux/Mac用）

# デフォルト値
RASPBERRY_IP="${1:-}"
USERNAME="${2:-pi}"
REMOTE_PATH="${3:-~/card_reader_improved}"

# IPアドレスの確認
if [ -z "$RASPBERRY_IP" ]; then
    echo "使用方法: $0 <ラズパイのIPアドレス> [ユーザー名] [リモートパス]"
    echo "例: $0 192.168.1.100 pi ~/card_reader_improved"
    read -p "ラズパイのIPアドレスを入力してください: " RASPBERRY_IP
fi

if [ -z "$RASPBERRY_IP" ]; then
    echo "[エラー] IPアドレスが指定されていません"
    exit 1
fi

echo "========================================"
echo "ラズパイへのファイル転送"
echo "========================================"
echo "IPアドレス: $RASPBERRY_IP"
echo "ユーザー名: $USERNAME"
echo "リモートパス: $REMOTE_PATH"
echo ""

# 転送するファイル
FILES=(
    "pi_client_simple.py"
    "start_pi_simple.sh"
    "common_utils.py"
    "constants.py"
    "lcd_i2c.py"
    "gpio_config.py"
)

# ファイル転送
echo "[転送開始] ファイルを転送しています..."
echo ""

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "転送中: $file"
        scp "$file" "${USERNAME}@${RASPBERRY_IP}:${REMOTE_PATH}/"
        if [ $? -eq 0 ]; then
            echo "[成功] $file"
        else
            echo "[エラー] $file の転送に失敗しました"
            exit 1
        fi
    else
        echo "[警告] $file が見つかりません（スキップ）"
    fi
done

echo ""
echo "========================================"
echo "転送完了！"
echo "========================================"
echo ""
echo "ラズパイで以下のコマンドを実行してください:"
echo ""
echo "  cd $REMOTE_PATH"
echo "  chmod +x start_pi_simple.sh"
echo "  ./start_pi_simple.sh"
echo ""

