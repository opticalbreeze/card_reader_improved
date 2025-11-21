#!/bin/bash
# メモリモニタリングテストスクリプト

echo "========================================================================"
echo "  メモリモニタリング機能テスト"
echo "========================================================================"
echo ""

# 設定ファイルのバックアップ
if [ -f "client_config.json" ]; then
    cp client_config.json client_config.json.backup
    echo "[1/4] 設定ファイルをバックアップしました"
else
    echo "[1/4] 設定ファイルが見つかりません - client_config_sample.jsonをコピーします"
    cp client_config_sample.json client_config.json
fi

# メモリモニタリングを有効化
echo ""
echo "[2/4] メモリモニタリングを有効化しています..."
python3 -c "
import json
with open('client_config.json', 'r') as f:
    config = json.load(f)
config['memory_monitor'] = {
    'enabled': True,
    'interval': 60,
    'tracemalloc': False
}
with open('client_config.json', 'w') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)
print('✅ メモリモニタリング設定を有効化しました（1分間隔）')
"

# 仮想環境でpsutilをインストール
echo ""
echo "[3/4] 依存パッケージ（psutil）をインストール中..."
if [ -d "venv" ]; then
    source venv/bin/activate
    pip install psutil>=5.9.0 -q
    echo "✅ psutilをインストールしました"
else
    echo "❌ 仮想環境が見つかりません"
    echo "   先に ./auto_setup.sh を実行してください"
    exit 1
fi

# メモリモニター単体テスト
echo ""
echo "[4/4] メモリモニター単体テストを実行しますか？ (y/N)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo ""
    echo "5分間のメモリモニタリングテストを開始します..."
    echo "Ctrl+Cで中断できます"
    echo ""
    python memory_monitor.py test
else
    echo "テストをスキップしました"
fi

echo ""
echo "========================================================================"
echo "  セットアップ完了"
echo "========================================================================"
echo ""
echo "次のステップ:"
echo "  1. クライアントを起動: bash start_pi.sh"
echo "  2. ログを確認: tail -f memory_usage.log"
echo "  3. 設定を変更: nano client_config.json"
echo ""
echo "設定を元に戻すには:"
echo "  mv client_config.json.backup client_config.json"
echo ""
