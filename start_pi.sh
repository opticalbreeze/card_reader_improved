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

# 仮想環境が正しく有効化されたか確認
if [ -z "$VIRTUAL_ENV" ]; then
    echo "[エラー] 仮想環境の有効化に失敗しました"
    exit 1
fi
echo "  ✅ 仮想環境: $VIRTUAL_ENV"
echo "  ✅ Python: $(which python3)"

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
# 注: サービスファイルのExecStartPreで既にpcscdの起動を待っているため、
#     ここでは確認のみ行う（sudoでの起動は不要）
echo "[3/4] PC/SCサービスの確認中..."
if systemctl is-active --quiet pcscd 2>/dev/null; then
    echo "  PC/SCサービスは起動中です"
else
    echo "  [警告] PC/SCサービスが起動していませんが、続行します"
    echo "  （サービスファイルで自動的に待機しているため、通常は問題ありません）"
fi

# PC/SCアクセス権限の確認
echo "[3.5/4] PC/SCアクセス権限の確認中..."
if groups | grep -q '\bpcscd\b'; then
    echo "  ✅ ユーザーはpcscdグループに所属しています"
else
    echo "  ⚠️ [警告] ユーザーがpcscdグループに所属していません"
    echo "  ⚠️ [対処] 以下のコマンドを実行して再ログインまたは再起動してください:"
    echo "  ⚠️        sudo usermod -a -G pcscd $USER"
fi

# PC/SCソケットファイルの確認
if [ -S /var/run/pcscd/pcscd.comm ]; then
    echo "  ✅ PC/SCソケットファイルが存在します"
    if [ -r /var/run/pcscd/pcscd.comm ] && [ -w /var/run/pcscd/pcscd.comm ]; then
        echo "  ✅ PC/SCソケットファイルへの読み書き権限があります"
    else
        echo "  ⚠️ [警告] PC/SCソケットファイルへの読み書き権限がありません"
    fi
else
    echo "  ⚠️ [警告] PC/SCソケットファイルが見つかりません"
fi

# PC/SC接続テスト（オプション、エラーが出ても続行）
# 仮想環境のPythonを明示的に使用
echo "[3.6/4] PC/SC接続テスト中..."
PYTHON_EXEC="$VIRTUAL_ENV/bin/python3"
if [ ! -f "$PYTHON_EXEC" ]; then
    PYTHON_EXEC="python3"  # フォールバック
fi
if "$PYTHON_EXEC" -c "from smartcard.System import readers; readers()" 2>/dev/null; then
    echo "  ✅ PC/SC接続テスト成功"
else
    echo "  ⚠️ [警告] PC/SC接続テスト失敗 - 権限の問題の可能性があります"
    echo "  ⚠️ [対処] sudo usermod -a -G pcscd $USER を実行して再ログインしてください"
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

# 仮想環境のPythonを明示的に使用（自動起動時の確実性のため）
PYTHON_EXEC="$VIRTUAL_ENV/bin/python3"
if [ ! -f "$PYTHON_EXEC" ]; then
    echo "[警告] 仮想環境のPythonが見つかりません。システムのpython3を使用します"
    PYTHON_EXEC="python3"
fi
echo "[確認] 使用するPython: $PYTHON_EXEC"
echo ""

exec "$PYTHON_EXEC" pi_client.py

# 終了時
echo ""
echo "========================================================================"
echo "プログラムを終了しました"
echo "========================================================================"
echo ""

