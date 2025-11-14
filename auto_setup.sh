#!/bin/bash
# ============================================================================
# カードリーダーシステム - 完全自動セットアップスクリプト
# 初回実行用：仮想環境作成、ライブラリインストール、systemd登録まで全自動
# ============================================================================

set -e  # エラーが発生したら停止

# 色付き出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}  カードリーダーシステム - 完全自動セットアップ${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo ""

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"
PROJECT_DIR=$(pwd)
echo -e "${GREEN}[INFO]${NC} プロジェクトディレクトリ: ${PROJECT_DIR}"
echo ""

# ============================================================================
# ステップ1: 管理者権限の確認
# ============================================================================
echo -e "${BLUE}[1/8] 管理者権限の確認...${NC}"
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}[警告] このスクリプトはsudoなしで実行してください${NC}"
    echo -e "${YELLOW}       システムパッケージのインストール時にパスワードを求められます${NC}"
    exit 1
fi
echo -e "${GREEN}[OK] 一般ユーザーで実行中${NC}"
echo ""

# ============================================================================
# ステップ2: システムパッケージのインストール
# ============================================================================
echo -e "${BLUE}[2/8] システムパッケージのチェックとインストール...${NC}"
echo -e "${YELLOW}[INFO] パスワードの入力を求められる場合があります${NC}"

REQUIRED_PACKAGES=(
    "python3-full"
    "python3-venv"
    "python3-pip"
    "python3-dev"
    "python3-smbus"
    "i2c-tools"
    "git"
    "libpcsclite-dev"
    "pcscd"
    "pcsc-tools"
)

MISSING_PACKAGES=()

for package in "${REQUIRED_PACKAGES[@]}"; do
    if ! dpkg -l | grep -q "^ii  $package"; then
        MISSING_PACKAGES+=("$package")
    fi
done

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo -e "${YELLOW}[INFO] 不足しているパッケージをインストールします...${NC}"
    sudo apt update
    sudo apt install -y "${MISSING_PACKAGES[@]}"
    echo -e "${GREEN}[OK] システムパッケージのインストール完了${NC}"
else
    echo -e "${GREEN}[OK] 必要なシステムパッケージは全てインストール済み${NC}"
fi
echo ""

# ============================================================================
# ステップ3: pcscdサービスの起動
# ============================================================================
echo -e "${BLUE}[3/8] pcscd（カードリーダーサービス）の起動...${NC}"
if systemctl is-active --quiet pcscd; then
    echo -e "${GREEN}[OK] pcscdは既に起動中${NC}"
else
    sudo systemctl start pcscd
    sudo systemctl enable pcscd
    echo -e "${GREEN}[OK] pcscdを起動し、自動起動を有効化しました${NC}"
fi
echo ""

# ============================================================================
# ステップ4: 仮想環境の作成
# ============================================================================
echo -e "${BLUE}[4/8] Python仮想環境のセットアップ...${NC}"

if [ -d "venv" ]; then
    echo -e "${YELLOW}[INFO] 既存の仮想環境を削除します...${NC}"
    rm -rf venv
fi

echo -e "${YELLOW}[INFO] 新しい仮想環境を作成中...${NC}"
python3 -m venv venv --system-site-packages

if [ -f "venv/bin/activate" ]; then
    echo -e "${GREEN}[OK] 仮想環境の作成完了${NC}"
else
    echo -e "${RED}[ERROR] 仮想環境の作成に失敗しました${NC}"
    exit 1
fi
echo ""

# ============================================================================
# ステップ5: Pythonパッケージのインストール
# ============================================================================
echo -e "${BLUE}[5/8] Python依存パッケージのインストール...${NC}"

# 仮想環境を有効化
source venv/bin/activate

# pipを最新版に更新
echo -e "${YELLOW}[INFO] pipを最新版に更新中...${NC}"
pip install --upgrade pip setuptools wheel > /dev/null 2>&1

# requirements_unified.txtが存在するかチェック
if [ -f "requirements_unified.txt" ]; then
    echo -e "${YELLOW}[INFO] requirements_unified.txt からインストール中...${NC}"
    pip install -r requirements_unified.txt
    echo -e "${GREEN}[OK] 依存パッケージのインストール完了${NC}"
else
    echo -e "${YELLOW}[WARNING] requirements_unified.txt が見つかりません${NC}"
    echo -e "${YELLOW}[INFO] 必須パッケージを個別にインストールします...${NC}"
    
    pip install requests
    pip install nfcpy
    pip install pyscard
    pip install smbus2
    pip install RPi.GPIO
    
    echo -e "${GREEN}[OK] 必須パッケージのインストール完了${NC}"
fi

deactivate
echo ""

# ============================================================================
# ステップ6: 設定ファイルの作成
# ============================================================================
echo -e "${BLUE}[6/8] 設定ファイルのセットアップ...${NC}"

if [ ! -f "client_config.json" ]; then
    if [ -f "client_config_sample.json" ]; then
        cp client_config_sample.json client_config.json
        echo -e "${GREEN}[OK] client_config.json を作成しました${NC}"
    else
        # デフォルト設定を作成
        cat > client_config.json << 'EOF'
{
  "server_url": "http://192.168.1.31:5000"
}
EOF
        echo -e "${GREEN}[OK] デフォルト設定ファイルを作成しました${NC}"
    fi
    echo -e "${YELLOW}[INFO] サーバーURLを変更する場合: nano client_config.json${NC}"
else
    echo -e "${GREEN}[OK] client_config.json は既に存在します${NC}"
fi
echo ""

# ============================================================================
# ステップ7: I2CとGPIOの権限設定
# ============================================================================
echo -e "${BLUE}[7/8] I2CとGPIO権限の設定...${NC}"

CURRENT_USER=$(whoami)

# i2cグループに追加
if groups $CURRENT_USER | grep -q '\bi2c\b'; then
    echo -e "${GREEN}[OK] i2cグループに既に所属しています${NC}"
else
    sudo usermod -a -G i2c $CURRENT_USER
    echo -e "${GREEN}[OK] i2cグループに追加しました${NC}"
fi

# gpioグループに追加
if groups $CURRENT_USER | grep -q '\bgpio\b'; then
    echo -e "${GREEN}[OK] gpioグループに既に所属しています${NC}"
else
    sudo usermod -a -G gpio $CURRENT_USER
    echo -e "${GREEN}[OK] gpioグループに追加しました${NC}"
fi

# dialoutグループに追加（カードリーダー用）
if groups $CURRENT_USER | grep -q '\bdialout\b'; then
    echo -e "${GREEN}[OK] dialoutグループに既に所属しています${NC}"
else
    sudo usermod -a -G dialout $CURRENT_USER
    echo -e "${GREEN}[OK] dialoutグループに追加しました${NC}"
fi

echo ""

# ============================================================================
# ステップ8: systemdサービスの作成
# ============================================================================
echo -e "${BLUE}[8/8] systemd自動起動サービスの作成...${NC}"

SERVICE_FILE="/etc/systemd/system/card-reader.service"

if [ -f "$SERVICE_FILE" ]; then
    echo -e "${YELLOW}[INFO] 既存のサービスを停止します...${NC}"
    sudo systemctl stop card-reader.service 2>/dev/null || true
    sudo systemctl disable card-reader.service 2>/dev/null || true
fi

# systemdサービスファイルを作成
sudo tee $SERVICE_FILE > /dev/null << EOF
[Unit]
Description=Card Reader Client Service
After=network.target pcscd.service
Wants=pcscd.service

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=$PROJECT_DIR/venv/bin/python3 $PROJECT_DIR/pi_client.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}[OK] systemdサービスファイルを作成しました${NC}"

# サービスをリロードして有効化
sudo systemctl daemon-reload
sudo systemctl enable card-reader.service

echo -e "${GREEN}[OK] 自動起動サービスを有効化しました${NC}"
echo ""

# ============================================================================
# セットアップ完了
# ============================================================================
echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN}  セットアップが完了しました！${NC}"
echo -e "${GREEN}======================================================================${NC}"
echo ""

echo -e "${BLUE}【次のステップ】${NC}"
echo ""
echo -e "1. ${YELLOW}設定ファイルの編集（必須）${NC}"
echo -e "   nano client_config.json"
echo -e "   → サーバーURLを正しく設定してください"
echo ""
echo -e "2. ${YELLOW}再起動（推奨）${NC}"
echo -e "   sudo reboot"
echo -e "   → I2C/GPIO権限を反映させるため"
echo ""
echo -e "3. ${YELLOW}サービスの起動${NC}"
echo -e "   sudo systemctl start card-reader.service"
echo ""
echo -e "${BLUE}【便利なコマンド】${NC}"
echo ""
echo -e "  サービスの状態確認:"
echo -e "    ${GREEN}sudo systemctl status card-reader.service${NC}"
echo ""
echo -e "  ログの確認:"
echo -e "    ${GREEN}sudo journalctl -u card-reader.service -f${NC}"
echo ""
echo -e "  サービスの停止:"
echo -e "    ${GREEN}sudo systemctl stop card-reader.service${NC}"
echo ""
echo -e "  サービスの再起動:"
echo -e "    ${GREEN}sudo systemctl restart card-reader.service${NC}"
echo ""
echo -e "  自動起動の無効化:"
echo -e "    ${GREEN}sudo systemctl disable card-reader.service${NC}"
echo ""
echo -e "  手動起動（テスト用）:"
echo -e "    ${GREEN}cd $PROJECT_DIR${NC}"
echo -e "    ${GREEN}source venv/bin/activate${NC}"
echo -e "    ${GREEN}python3 pi_client.py${NC}"
echo ""
echo -e "${YELLOW}※ 再起動後、サービスは自動的に起動します${NC}"
echo ""

