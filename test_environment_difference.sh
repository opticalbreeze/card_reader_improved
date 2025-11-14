#!/bin/bash
# ============================================================================
# 手動起動と自動起動の環境の違いをテストするスクリプト
# ============================================================================

echo "========================================================================"
echo "  環境の違いをテスト"
echo "========================================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "[テスト1] 手動起動時の環境（ターミナルから実行）"
echo "----------------------------------------"
echo "現在の環境変数:"
echo "  PATH: $PATH"
echo "  PYTHONIOENCODING: $PYTHONIOENCODING"
echo "  LANG: $LANG"
echo "  LC_ALL: $LC_ALL"
echo "  VIRTUAL_ENV: $VIRTUAL_ENV"
echo "  USER: $(whoami)"
echo "  HOME: $HOME"
echo ""

echo "[テスト2] 仮想環境を有効化した場合"
echo "----------------------------------------"
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "仮想環境を有効化しました"
    echo "  PATH: $PATH"
    echo "  VIRTUAL_ENV: $VIRTUAL_ENV"
    echo "  which python3: $(which python3)"
    echo "  python3 --version: $(python3 --version 2>&1)"
else
    echo "venvディレクトリが見つかりません"
fi
echo ""

echo "[テスト3] systemdサービスから実行される場合の環境"
echo "----------------------------------------"
echo "サービスファイルの環境変数設定を確認:"
if [ -f "attendance-client-fixed.service" ]; then
    echo "Environment設定:"
    grep "^Environment=" attendance-client-fixed.service | sed 's/^/  /'
else
    echo "  attendance-client-fixed.serviceが見つかりません"
fi
echo ""

echo "[テスト4] 実行中のサービスプロセスの環境"
echo "----------------------------------------"
SERVICE_PID=$(systemctl show attendance-client-fixed.service -p MainPID --value 2>/dev/null)
if [ -n "$SERVICE_PID" ] && [ "$SERVICE_PID" != "0" ]; then
    echo "サービスプロセスPID: $SERVICE_PID"
    echo ""
    echo "環境変数（重要なもの）:"
    sudo cat /proc/$SERVICE_PID/environ 2>/dev/null | tr '\0' '\n' | grep -E "PATH|PYTHON|LANG|LC_|VIRTUAL|USER|HOME" | sort | sed 's/^/  /'
    echo ""
    echo "プロセスツリー:"
    ps -f -p $SERVICE_PID 2>/dev/null | sed 's/^/  /'
else
    echo "サービスは実行されていません"
fi
echo ""

echo "[テスト5] USBデバイスの認識状態"
echo "----------------------------------------"
echo "lsusb出力:"
lsusb | grep -E "054c:06c1|Sony|PaSoRi|NFC|Card Reader" || echo "  カードリーダーが見つかりません"
echo ""

echo "========================================================================"
echo "比較結果"
echo "========================================================================"
echo ""
echo "手動起動と自動起動で環境が違う場合、以下を確認:"
echo "  1. PATHが違う → 仮想環境のパスが含まれているか"
echo "  2. 環境変数が違う → LANG, LC_ALLなど"
echo "  3. ユーザー環境が違う → .bashrc/.profileが読み込まれているか"
echo ""

