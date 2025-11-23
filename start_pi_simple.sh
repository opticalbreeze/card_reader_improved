#!/bin/bash
# ラズパイ版シンプルクライアント起動スクリプト

cd "$(dirname "$0")"

# 仮想環境の確認とアクティベート
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Python実行
python3 pi_client.py

