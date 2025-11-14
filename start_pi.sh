#!/bin/bash
# ============================================================================
# カードリーダーシステム 簡単起動スクリプト
# ダブルクリックまたは ./start_pi.sh で実行
# ============================================================================

# UTF-8環境設定（強制）
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1

# ロケール設定
if locale -a | grep -q "ja_JP.utf8\|ja_JP.UTF-8"; then
    export LANG=ja_JP.UTF-8
    export LC_ALL=ja_JP.UTF-8
else
    # 日本語ロケールが利用できない場合は、UTF-8を強制
    export LANG=C.UTF-8
    export LC_ALL=C.UTF-8
fi

# ターミナルのエンコーディング設定
if [ -t 1 ]; then
    # 標準出力がターミナルの場合のみ設定
    export LC_CTYPE=UTF-8
fi

echo "========================================================================"
echo "  カードリーダーシステム 起動中..."
echo "========================================================================"
echo ""

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"

# 仮想環境が存在するか確認
if [ ! -d "venv" ]; then
    echo "[エラー] 仮想環境が見つかりません"
    echo ""
    echo "セットアップを実行してください:"
    echo "  chmod +x setup.sh"
    echo "  ./setup.sh"
    echo ""
    exit 1
fi

# 仮想環境を有効化
echo "[1/4] 仮想環境を有効化中..."
source venv/bin/activate

# USBデバイスが認識されるまで待機（最大30秒）
echo "[2/4] USBデバイスの認識を待機中..."
USB_DETECTED=false
for i in {1..30}; do
    if lsusb | grep -qE "054c:06c1|Sony|PaSoRi|NFC|Card Reader"; then
        echo "  USBデバイスを検出しました"
        USB_DETECTED=true
        break
    fi
    if [ $i -eq 30 ]; then
        echo "  [警告] USBデバイスが見つかりませんが、起動を続行します"
    else
        sleep 1
    fi
done

# PC/SCサービスが起動しているか確認
echo "[3/4] PC/SCサービスの確認中..."
if systemctl is-active --quiet pcscd 2>/dev/null; then
    echo "  PC/SCサービスは起動中です"
else
    echo "  PC/SCサービスを起動中..."
    sudo systemctl start pcscd 2>/dev/null || true
    sleep 2
    if systemctl is-active --quiet pcscd 2>/dev/null; then
        echo "  PC/SCサービスを起動しました"
    else
        echo "  [警告] PC/SCサービスの起動に失敗しましたが、続行します"
    fi
fi

# 設定ファイルが存在するか確認
if [ ! -f "client_config.json" ]; then
    echo "[4/4] 設定ファイルが見つかりません"
    echo "       デフォルト設定で起動します（初回起動時に自動作成されます）"
else
    echo "[4/4] 設定ファイル読み込み完了"
fi

# プログラムを起動
echo ""
echo "[起動] プログラムを起動します..."
echo ""
python3 pi_client.py

# 終了時
echo ""
echo "========================================================================"
echo "プログラムを終了しました"
echo "========================================================================"
echo ""

