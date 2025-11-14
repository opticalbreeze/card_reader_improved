#!/bin/bash
# ============================================================================
# 手動起動と自動起動の実際の違いを確認するスクリプト
# ============================================================================

# UTF-8環境設定
export PYTHONIOENCODING=utf-8
if locale -a | grep -q "ja_JP.utf8\|ja_JP.UTF-8"; then
    export LANG=ja_JP.UTF-8
    export LC_ALL=ja_JP.UTF-8
fi

echo "========================================================================"
echo "  手動起動と自動起動の実際の違いを確認"
echo "========================================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "[1] 手動起動時の環境（現在のターミナルセッション）"
echo "----------------------------------------"
echo "PID: $$"
echo "PPID: $PPID"
echo "ユーザー: $(whoami)"
echo "現在のディレクトリ: $(pwd)"
echo ""
echo "環境変数:"
echo "  PATH: $PATH"
echo "  PYTHONIOENCODING: $PYTHONIOENCODING"
echo "  LANG: $LANG"
echo "  LC_ALL: $LC_ALL"
echo "  VIRTUAL_ENV: $VIRTUAL_ENV"
echo "  USER: $USER"
echo "  HOME: $HOME"
echo "  SHELL: $SHELL"
echo ""

echo "[2] 仮想環境を有効化した場合"
echo "----------------------------------------"
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "仮想環境を有効化しました"
    echo "  PATH: $PATH"
    echo "  VIRTUAL_ENV: $VIRTUAL_ENV"
    echo "  which python3: $(which python3)"
    echo "  python3 --version: $(python3 --version 2>&1)"
    echo ""
    echo "仮想環境のPythonパス:"
    if [ -f "$VIRTUAL_ENV/bin/python3" ]; then
        echo "  $VIRTUAL_ENV/bin/python3"
        echo "  存在: ✅"
    else
        echo "  $VIRTUAL_ENV/bin/python3"
        echo "  存在: ❌"
    fi
else
    echo "venvディレクトリが見つかりません"
fi
echo ""

echo "[3] 自動起動時の環境（systemdサービスから実行される場合）"
echo "----------------------------------------"
echo "サービスファイルの設定:"
if [ -f "attendance-client-fixed.service" ]; then
    echo "User: $(grep '^User=' attendance-client-fixed.service | cut -d= -f2)"
    echo "WorkingDirectory: $(grep '^WorkingDirectory=' attendance-client-fixed.service | cut -d= -f2)"
    echo ""
    echo "環境変数設定:"
    grep "^Environment=" attendance-client-fixed.service | sed 's/^Environment="//;s/"$//' | sed 's/^/  /'
else
    echo "attendance-client-fixed.serviceが見つかりません"
fi
echo ""

echo "[4] 実行中のサービスプロセスの実際の環境"
echo "----------------------------------------"
SERVICE_PID=$(systemctl show attendance-client-fixed.service -p MainPID --value 2>/dev/null)
if [ -n "$SERVICE_PID" ] && [ "$SERVICE_PID" != "0" ]; then
    echo "サービスプロセスPID: $SERVICE_PID"
    echo ""
    echo "プロセス情報:"
    ps -f -p $SERVICE_PID 2>/dev/null | tail -1
    echo ""
    echo "プロセスの環境変数（重要なもの）:"
    sudo cat /proc/$SERVICE_PID/environ 2>/dev/null | tr '\0' '\n' | grep -E "PATH|PYTHON|LANG|LC_|VIRTUAL|USER|HOME|SHELL" | sort | sed 's/^/  /'
    echo ""
    echo "プロセスの作業ディレクトリ:"
    sudo readlink /proc/$SERVICE_PID/cwd 2>/dev/null || echo "  取得できません"
    echo ""
    echo "プロセスの実行ファイル:"
    sudo readlink /proc/$SERVICE_PID/exe 2>/dev/null || echo "  取得できません"
    echo ""
    echo "プロセスのコマンドライン:"
    sudo cat /proc/$SERVICE_PID/cmdline 2>/dev/null | tr '\0' ' ' | sed 's/^/  /'
    echo ""
else
    echo "サービスは実行されていません"
    echo ""
    echo "サービスを起動して確認する場合:"
    echo "  sudo systemctl start attendance-client-fixed.service"
    echo "  sleep 5"
    echo "  ./check_actual_difference.sh"
fi
echo ""

echo "[5] 比較"
echo "----------------------------------------"
echo "手動起動と自動起動で異なる可能性がある項目:"
echo ""
echo "1. PATH:"
echo "   手動: ユーザーの.bashrc/.profileで設定されたPATH + 仮想環境のパス"
echo "   自動: サービスファイルで設定されたPATH（最小限）"
echo ""
echo "2. 環境変数:"
echo "   手動: .bashrc/.profileで設定された環境変数"
echo "   自動: サービスファイルで明示的に設定された環境変数のみ"
echo ""
echo "3. プロセスの親:"
echo "   手動: ターミナル（bash/zshなど）"
echo "   自動: systemd"
echo ""
echo "4. 作業ディレクトリ:"
echo "   手動: ターミナルでcdしたディレクトリ"
echo "   自動: WorkingDirectoryで指定されたディレクトリ"
echo ""

echo "========================================================================"
echo "検証完了"
echo "========================================================================"
echo ""
echo "サービスログを確認:"
echo "  sudo journalctl -u attendance-client-fixed.service -n 100 --no-pager"
echo ""

