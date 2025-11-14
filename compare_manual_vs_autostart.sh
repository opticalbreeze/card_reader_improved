#!/bin/bash
# ============================================================================
# 手動起動と自動起動の環境を比較するスクリプト
# ============================================================================

echo "========================================================================"
echo "  手動起動 vs 自動起動 環境比較"
echo "========================================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "[手動起動時の環境]"
echo "----------------------------------------"
echo "1. ターミナルから実行した場合の環境変数を保存..."
# 手動起動時の環境をシミュレート
MANUAL_ENV=$(cat <<EOF
PATH=$PATH
PYTHONIOENCODING=$PYTHONIOENCODING
LANG=$LANG
LC_ALL=$LC_ALL
VIRTUAL_ENV=$VIRTUAL_ENV
USER=$(whoami)
HOME=$HOME
SHELL=$SHELL
EOF
)
echo "$MANUAL_ENV" > /tmp/manual_env.txt
echo "✅ 保存完了: /tmp/manual_env.txt"
echo ""

echo "[自動起動時の環境]"
echo "----------------------------------------"
echo "2. systemdサービスから実行される場合の環境を確認..."
echo ""
echo "サービスファイルの環境変数設定:"
if [ -f "attendance-client-fixed.service" ]; then
    grep -E "^Environment=" attendance-client-fixed.service || echo "  環境変数設定なし"
else
    echo "  attendance-client-fixed.serviceが見つかりません"
fi
echo ""

echo "3. 実行中のサービスプロセスの環境を確認..."
SERVICE_PID=$(systemctl show attendance-client-fixed.service -p MainPID --value 2>/dev/null)
if [ -n "$SERVICE_PID" ] && [ "$SERVICE_PID" != "0" ]; then
    echo "サービスプロセスPID: $SERVICE_PID"
    echo ""
    echo "環境変数:"
    sudo cat /proc/$SERVICE_PID/environ 2>/dev/null | tr '\0' '\n' | grep -E "PATH|PYTHON|LANG|LC_|VIRTUAL|USER|HOME" | sort
    echo ""
    echo "プロセス情報:"
    ps -p $SERVICE_PID -o pid,ppid,user,cmd --no-headers 2>/dev/null || echo "  プロセスが見つかりません"
else
    echo "サービスは実行されていません"
    echo ""
    echo "サービスログを確認:"
    echo "  sudo journalctl -u attendance-client-fixed.service -n 50"
fi
echo ""

echo "[比較]"
echo "----------------------------------------"
echo "主な違いを確認:"
echo ""
echo "手動起動:"
echo "  - ターミナルセッションから実行"
echo "  - ユーザーの.bashrc/.profileが読み込まれる"
echo "  - 仮想環境を手動で有効化"
echo ""
echo "自動起動:"
echo "  - systemdサービスから実行"
echo "  - ユーザーの.bashrc/.profileが読み込まれない可能性"
echo "  - 環境変数はサービスファイルで明示的に設定する必要がある"
echo ""

echo "========================================================================"
echo "推奨される修正"
echo "========================================================================"
echo ""
echo "1. サービスファイルに必要な環境変数を追加"
echo "2. 仮想環境のパスを明示的に設定"
echo "3. ユーザーの環境設定を読み込む"
echo ""

