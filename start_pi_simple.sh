#!/bin/bash
# ラズパイ版クライアント起動スクリプト
# 
# 重要: このスクリプトは pi_client.py を起動します
# 参照先を変更しないでください（バージョン管理方針参照: docs/NO_NEW_VERSIONS.md）

cd "$(dirname "$0")"

# 仮想環境の確認とアクティベート
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Python実行（参照先: pi_client.py - 変更禁止）
python3 pi_client.py

