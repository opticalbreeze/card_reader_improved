#!/bin/bash
# ============================================================================
# 手動起動と自動起動のプロセス環境を検証するスクリプト
# ============================================================================

# UTF-8環境設定
export PYTHONIOENCODING=utf-8
if locale -a | grep -q "ja_JP.utf8\|ja_JP.UTF-8"; then
    export LANG=ja_JP.UTF-8
    export LC_ALL=ja_JP.UTF-8
fi

echo "========================================================================"
echo "  プロセス環境の検証"
echo "========================================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "[1] 現在のプロセス情報"
echo "----------------------------------------"
echo "PID: $$"
echo "PPID: $PPID"
echo "ユーザー: $(whoami)"
echo "現在のディレクトリ: $(pwd)"
echo ""

echo "[2] 環境変数（重要なもの）"
echo "----------------------------------------"
echo "PATH: $PATH"
echo "PYTHONIOENCODING: $PYTHONIOENCODING"
echo "LANG: $LANG"
echo "LC_ALL: $LC_ALL"
echo "VIRTUAL_ENV: $VIRTUAL_ENV"
echo ""

echo "[3] Pythonのパス"
echo "----------------------------------------"
echo "which python3: $(which python3)"
echo "python3 --version: $(python3 --version 2>&1)"
echo ""

echo "[4] 仮想環境の状態"
echo "----------------------------------------"
if [ -n "$VIRTUAL_ENV" ]; then
    echo "✅ 仮想環境が有効化されています"
    echo "VIRTUAL_ENV: $VIRTUAL_ENV"
    echo "仮想環境のPython: $VIRTUAL_ENV/bin/python3"
    if [ -f "$VIRTUAL_ENV/bin/python3" ]; then
        echo "仮想環境のPythonバージョン: $($VIRTUAL_ENV/bin/python3 --version 2>&1)"
    fi
else
    echo "❌ 仮想環境が有効化されていません"
    if [ -d "venv" ]; then
        echo "venvディレクトリは存在します: $(pwd)/venv"
        echo "仮想環境を有効化しますか？ (y/N)"
        read -p "> " CONFIRM
        if [ "$CONFIRM" = "y" ] || [ "$CONFIRM" = "Y" ]; then
            source venv/bin/activate
            echo "✅ 仮想環境を有効化しました"
            echo "VIRTUAL_ENV: $VIRTUAL_ENV"
        fi
    fi
fi
echo ""

echo "[5] USBデバイスの状態"
echo "----------------------------------------"
echo "lsusb出力:"
lsusb | grep -E "054c:06c1|Sony|PaSoRi|NFC|Card Reader" || echo "  カードリーダーが見つかりません"
echo ""

echo "[6] PC/SCサービスの状態"
echo "----------------------------------------"
if systemctl is-active --quiet pcscd 2>/dev/null; then
    echo "✅ PC/SCサービスは起動中"
else
    echo "❌ PC/SCサービスは停止中"
fi
echo ""

echo "[7] プロセスツリー"
echo "----------------------------------------"
echo "現在のプロセスの親プロセス:"
ps -p $PPID -o pid,ppid,cmd --no-headers 2>/dev/null || echo "  親プロセス情報を取得できません"
echo ""

echo "[8] 実行中のpi_client.pyプロセス"
echo "----------------------------------------"
ps aux | grep "[p]i_client.py" || echo "  pi_client.pyは実行されていません"
echo ""

echo "========================================================================"
echo "検証完了"
echo "========================================================================"
echo ""
echo "自動起動時の環境を確認するには:"
echo "  sudo journalctl -u attendance-client-fixed.service -n 100"
echo ""

