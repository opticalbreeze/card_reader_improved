#!/bin/bash
# ラズパイ統合版クライアント起動スクリプト

echo "=========================================="
echo "[ラズパイ統合版クライアント起動]"
echo "=========================================="

cd ~/simple_card_reader || cd "$(dirname "$0")"

# I2C確認
if ! command -v i2cdetect &> /dev/null; then
    echo "[警告] i2c-tools未インストール"
    echo "sudo apt install -y i2c-tools"
fi

# 仮想環境
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# LCD確認（エラーでも続行）
echo "[確認] LCD I2Cアドレス確認中..."
i2cdetect -y 1 2>/dev/null || echo "[警告] LCD未検出 - LCD機能無効で続行"

# 起動
echo "[起動] 統合版クライアント..."
python3 client_card_reader_unified.py

