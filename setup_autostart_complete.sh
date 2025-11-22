#!/bin/bash
# ============================================================================
# Raspberry Pi版 完全自動起動設定スクリプト
# 仮想環境の作成から自動起動設定まで、すべてを自動で実施します
# ============================================================================

set -e

# UTF-8環境設定
export PYTHONIOENCODING=utf-8
if locale -a | grep -q "ja_JP.utf8\|ja_JP.UTF-8"; then
    export LANG=ja_JP.UTF-8
    export LC_ALL=ja_JP.UTF-8
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}  Raspberry Pi版 完全自動起動設定${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo ""

# rootユーザーで実行されているか確認
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[エラー] このスクリプトはroot権限で実行する必要があります${NC}"
    echo -e "${YELLOW}[実行] sudo bash setup_autostart_complete.sh${NC}"
    exit 1
fi

# カレントディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo -e "${GREEN}[情報]${NC} プロジェクトディレクトリ: ${SCRIPT_DIR}"
echo ""

# ユーザー名を取得（sudoで実行された場合は元のユーザー）
if [ -n "$SUDO_USER" ]; then
    REAL_USER="$SUDO_USER"
else
    # デフォルトユーザーを確認
    if id "raspberry" &>/dev/null; then
        REAL_USER="raspberry"
    elif id "pi" &>/dev/null; then
        REAL_USER="pi"
    else
        # ホームディレクトリから推測
        REAL_USER=$(basename "$(eval echo ~$SUDO_USER)")
    fi
fi
echo -e "${GREEN}[情報]${NC} 実行ユーザー: ${REAL_USER}"
echo ""

# ============================================================================
# ステップ1: 必要なファイルの存在確認
# ============================================================================
echo -e "${BLUE}[1/8]${NC} 必要なファイルの確認中..."

REQUIRED_FILES=(
    "pi_client.py"
    "start_pi.sh"
    "requirements_unified.txt"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$SCRIPT_DIR/$file" ]; then
        echo -e "${RED}[エラー]${NC} $file が見つかりません"
        echo -e "${YELLOW}[ヒント]${NC} このスクリプトをプロジェクトのルートディレクトリで実行してください"
        exit 1
    fi
done
echo -e "${GREEN}[OK]${NC} 必要なファイルがすべて存在します"
echo ""

# ============================================================================
# ステップ2: Python3の確認
# ============================================================================
echo -e "${BLUE}[2/8]${NC} Python3の確認中..."
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}[インストール]${NC} Python3をインストール中..."
    apt-get update
    apt-get install -y python3 python3-pip python3-venv
fi
PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}[OK]${NC} Python3がインストールされています: ${PYTHON_VERSION}"
echo ""

# ============================================================================
# ステップ3: 仮想環境の作成（存在しない場合）
# ============================================================================
echo -e "${BLUE}[3/8]${NC} 仮想環境の確認中..."
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo -e "${YELLOW}[作成]${NC} 仮想環境を作成中..."
    sudo -u "$REAL_USER" python3 -m venv "$SCRIPT_DIR/venv"
    echo -e "${GREEN}[OK]${NC} 仮想環境を作成しました"
else
    echo -e "${GREEN}[OK]${NC} 仮想環境は既に存在します"
fi
echo ""

# ============================================================================
# ステップ4: 依存パッケージのインストール
# ============================================================================
echo -e "${BLUE}[4/8]${NC} 依存パッケージのインストール中..."
VENV_PYTHON="$SCRIPT_DIR/venv/bin/python3"
VENV_PIP="$SCRIPT_DIR/venv/bin/pip"

# pipのアップグレード
sudo -u "$REAL_USER" "$VENV_PIP" install --upgrade pip --quiet

# 依存パッケージのインストール
if [ -f "$SCRIPT_DIR/requirements_unified.txt" ]; then
    echo -e "${BLUE}[インストール]${NC} requirements_unified.txtからパッケージをインストール中..."
    sudo -u "$REAL_USER" "$VENV_PIP" install -r "$SCRIPT_DIR/requirements_unified.txt" --quiet
    echo -e "${GREEN}[OK]${NC} 依存パッケージをインストールしました"
else
    echo -e "${YELLOW}[警告]${NC} requirements_unified.txtが見つかりません"
fi
echo ""

# ============================================================================
# ステップ5: PC/SC関連の設定
# ============================================================================
echo -e "${BLUE}[5/8]${NC} PC/SC関連の設定中..."

# pcscdサービスの確認と起動
if systemctl list-unit-files | grep -q "pcscd.service"; then
    echo -e "${GREEN}[OK]${NC} pcscdサービスが存在します"
    systemctl enable pcscd.service 2>/dev/null || true
    systemctl start pcscd.service 2>/dev/null || true
else
    echo -e "${YELLOW}[インストール]${NC} pcscdをインストール中..."
    apt-get update
    apt-get install -y pcscd pcsc-tools
    systemctl enable pcscd.service
    systemctl start pcscd.service
fi

# pcscdグループの確認と作成
if getent group pcscd > /dev/null 2>&1; then
    echo -e "${GREEN}[OK]${NC} pcscdグループが存在します"
else
    echo -e "${YELLOW}[作成]${NC} pcscdグループを作成中..."
    groupadd pcscd
    echo -e "${GREEN}[OK]${NC} pcscdグループを作成しました"
fi

# ユーザーをpcscdグループに追加
if groups "$REAL_USER" | grep -q '\bpcscd\b'; then
    echo -e "${GREEN}[OK]${NC} ユーザー $REAL_USER は既にpcscdグループに所属しています"
else
    echo -e "${YELLOW}[追加]${NC} ユーザー $REAL_USER をpcscdグループに追加中..."
    usermod -a -G pcscd "$REAL_USER"
    echo -e "${GREEN}[OK]${NC} ユーザーをpcscdグループに追加しました"
    echo -e "${YELLOW}[注意]${NC} グループの変更を反映するには、ログアウト/ログインが必要です"
fi
echo ""

# ============================================================================
# ステップ6: GPIOグループの設定（オプション）
# ============================================================================
echo -e "${BLUE}[6/8]${NC} GPIOグループの確認中..."
if getent group gpio > /dev/null 2>&1; then
    if groups "$REAL_USER" | grep -q '\bgpio\b'; then
        echo -e "${GREEN}[OK]${NC} ユーザー $REAL_USER は既にgpioグループに所属しています"
    else
        echo -e "${YELLOW}[追加]${NC} ユーザー $REAL_USER をgpioグループに追加中..."
        usermod -a -G gpio "$REAL_USER"
        echo -e "${GREEN}[OK]${NC} ユーザーをgpioグループに追加しました"
    fi
else
    echo -e "${YELLOW}[スキップ]${NC} gpioグループが存在しません（GPIO機能を使用しない場合は問題ありません）"
fi
echo ""

# ============================================================================
# ステップ7: systemdサービスファイルの作成
# ============================================================================
echo -e "${BLUE}[7/8]${NC} systemdサービスファイルを作成中..."

SERVICE_FILE="/etc/systemd/system/attendance-client-fixed.service"

# サービスファイルを作成
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=ICカード勤怠管理システム - ラズパイクライアント
After=network.target pcscd.service
Wants=network.target pcscd.service

[Service]
Type=simple
User=$REAL_USER
Group=pcscd
WorkingDirectory=$SCRIPT_DIR
ExecStartPre=/bin/sleep 5
ExecStartPre=/bin/bash -c 'until systemctl is-active --quiet pcscd; do sleep 1; done'
ExecStartPre=/bin/bash -c 'until [ -S /var/run/pcscd/pcscd.comm ]; do sleep 1; done'
ExecStart=/bin/bash $SCRIPT_DIR/start_pi.sh
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

Environment="PYTHONUNBUFFERED=1"
Environment="PYTHONIOENCODING=utf-8"
Environment="LANG=ja_JP.UTF-8"
Environment="LC_ALL=ja_JP.UTF-8"
Environment="PATH=$SCRIPT_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="VIRTUAL_ENV=$SCRIPT_DIR/venv"
Environment="PCSCLITE_CSOCK_NAME=/var/run/pcscd/pcscd.comm"

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}[OK]${NC} サービスファイルを作成しました: $SERVICE_FILE"
echo ""

# 古いサービスを無効化（存在する場合）
if systemctl list-unit-files | grep -q "attendance-client.service"; then
    echo -e "${YELLOW}[無効化]${NC} 古いサービスを無効化中..."
    systemctl stop attendance-client.service 2>/dev/null || true
    systemctl disable attendance-client.service 2>/dev/null || true
    echo -e "${GREEN}[OK]${NC} 古いサービスを無効化しました"
    echo ""
fi

# systemdをリロード
echo -e "${BLUE}[リロード]${NC} systemdをリロード中..."
systemctl daemon-reload
echo -e "${GREEN}[OK]${NC} リロード完了"
echo ""

# ============================================================================
# ステップ8: サービスの有効化
# ============================================================================
echo -e "${BLUE}[8/8]${NC} サービスを有効化中..."
systemctl enable attendance-client-fixed.service
echo -e "${GREEN}[OK]${NC} サービスを有効化しました（再起動時に自動起動されます）"
echo ""

# ============================================================================
# 完了メッセージ
# ============================================================================
echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN}  設定完了！${NC}"
echo -e "${GREEN}======================================================================${NC}"
echo ""
echo -e "${BLUE}サービス名:${NC} attendance-client-fixed.service"
echo ""
echo -e "${BLUE}【便利なコマンド】${NC}"
echo ""
echo -e "  状態確認:"
echo -e "    ${GREEN}sudo systemctl status attendance-client-fixed.service${NC}"
echo ""
echo -e "  起動:"
echo -e "    ${GREEN}sudo systemctl start attendance-client-fixed.service${NC}"
echo ""
echo -e "  停止:"
echo -e "    ${GREEN}sudo systemctl stop attendance-client-fixed.service${NC}"
echo ""
echo -e "  再起動:"
echo -e "    ${GREEN}sudo systemctl restart attendance-client-fixed.service${NC}"
echo ""
echo -e "  ログ確認:"
echo -e "    ${GREEN}sudo journalctl -u attendance-client-fixed.service -f${NC}"
echo ""
echo -e "  自動起動無効化:"
echo -e "    ${GREEN}sudo systemctl disable attendance-client-fixed.service${NC}"
echo ""
echo -e "${YELLOW}[重要]${NC} グループの変更を反映するには、再ログインまたは再起動が必要です"
echo -e "${YELLOW}[情報]${NC} 次回のラズパイ起動時から自動起動されます"
echo -e "${YELLOW}[情報]${NC} 今すぐ起動する場合は: sudo systemctl start attendance-client-fixed.service"
echo ""

# 今すぐ起動するか確認
read -p "今すぐサービスを起動しますか？ (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}[実行]${NC} サービスを起動中..."
    systemctl start attendance-client-fixed.service
    sleep 2
    echo ""
    echo -e "${BLUE}[状態確認]${NC}"
    systemctl status attendance-client-fixed.service --no-pager
    echo ""
    echo -e "${GREEN}[OK]${NC} サービスを起動しました"
else
    echo -e "${YELLOW}[スキップ]${NC} サービスの起動をスキップしました"
fi

echo ""
echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN}  完了${NC}"
echo -e "${GREEN}======================================================================${NC}"
echo ""

