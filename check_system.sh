#!/bin/bash
# ============================================================================
# システム診断スクリプト
# 依存関係、権限、デバイスの状態をチェック
# ============================================================================

# 色付き出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}  カードリーダーシステム - システム診断${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo ""

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"

# ============================================================================
# 1. システムパッケージのチェック
# ============================================================================
echo -e "${BLUE}[1] システムパッケージのチェック${NC}"

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
)

ALL_INSTALLED=true

for package in "${REQUIRED_PACKAGES[@]}"; do
    if dpkg -l | grep -q "^ii  $package"; then
        echo -e "  ${GREEN}✓${NC} $package"
    else
        echo -e "  ${RED}✗${NC} $package ${YELLOW}(未インストール)${NC}"
        ALL_INSTALLED=false
    fi
done

if [ "$ALL_INSTALLED" = true ]; then
    echo -e "${GREEN}[OK] 全てのシステムパッケージがインストールされています${NC}"
else
    echo -e "${YELLOW}[WARNING] 不足しているパッケージがあります${NC}"
    echo -e "${YELLOW}  → sudo apt install -y ${REQUIRED_PACKAGES[@]}${NC}"
fi
echo ""

# ============================================================================
# 2. 仮想環境のチェック
# ============================================================================
echo -e "${BLUE}[2] Python仮想環境のチェック${NC}"

if [ -d "venv" ]; then
    echo -e "  ${GREEN}✓${NC} 仮想環境が存在します"
    
    if [ -f "venv/bin/activate" ]; then
        echo -e "  ${GREEN}✓${NC} activate スクリプトが存在します"
    else
        echo -e "  ${RED}✗${NC} activate スクリプトが見つかりません"
    fi
    
    if [ -f "venv/bin/python3" ]; then
        PYTHON_VERSION=$(venv/bin/python3 --version 2>&1)
        echo -e "  ${GREEN}✓${NC} Python: $PYTHON_VERSION"
    else
        echo -e "  ${RED}✗${NC} Python3が見つかりません"
    fi
else
    echo -e "  ${RED}✗${NC} 仮想環境が存在しません"
    echo -e "${YELLOW}  → ./auto_setup.sh を実行してください${NC}"
fi
echo ""

# ============================================================================
# 3. Pythonパッケージのチェック
# ============================================================================
echo -e "${BLUE}[3] Python依存パッケージのチェック${NC}"

if [ -d "venv" ]; then
    source venv/bin/activate
    
    REQUIRED_PY_PACKAGES=(
        "requests"
        "nfcpy"
        "pyscard"
        "smbus2"
        "RPi.GPIO"
    )
    
    for package in "${REQUIRED_PY_PACKAGES[@]}"; do
        if pip show "$package" > /dev/null 2>&1; then
            VERSION=$(pip show "$package" | grep Version | cut -d' ' -f2)
            echo -e "  ${GREEN}✓${NC} $package ($VERSION)"
        else
            echo -e "  ${RED}✗${NC} $package ${YELLOW}(未インストール)${NC}"
        fi
    done
    
    deactivate
else
    echo -e "  ${YELLOW}[SKIP] 仮想環境が存在しないためスキップ${NC}"
fi
echo ""

# ============================================================================
# 4. 設定ファイルのチェック
# ============================================================================
echo -e "${BLUE}[4] 設定ファイルのチェック${NC}"

if [ -f "client_config.json" ]; then
    echo -e "  ${GREEN}✓${NC} client_config.json が存在します"
    
    SERVER_URL=$(grep -oP '"server_url":\s*"\K[^"]+' client_config.json 2>/dev/null)
    if [ -n "$SERVER_URL" ]; then
        echo -e "  ${GREEN}✓${NC} サーバーURL: ${SERVER_URL}"
    else
        echo -e "  ${YELLOW}⚠${NC} サーバーURLが設定されていません"
    fi
else
    echo -e "  ${RED}✗${NC} client_config.json が見つかりません"
    echo -e "${YELLOW}  → cp client_config_sample.json client_config.json${NC}"
fi
echo ""

# ============================================================================
# 5. 必須ファイルのチェック
# ============================================================================
echo -e "${BLUE}[5] 必須ファイルのチェック${NC}"

REQUIRED_FILES=(
    "pi_client.py"
    "lcd_i2c.py"
    "gpio_config.py"
    "config.py"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}✓${NC} $file"
    else
        echo -e "  ${RED}✗${NC} $file ${YELLOW}(見つかりません)${NC}"
    fi
done
echo ""

# ============================================================================
# 6. ユーザー権限のチェック
# ============================================================================
echo -e "${BLUE}[6] ユーザー権限のチェック${NC}"

CURRENT_USER=$(whoami)

if groups $CURRENT_USER | grep -q '\bi2c\b'; then
    echo -e "  ${GREEN}✓${NC} i2cグループに所属しています"
else
    echo -e "  ${RED}✗${NC} i2cグループに所属していません"
    echo -e "${YELLOW}  → sudo usermod -a -G i2c $CURRENT_USER${NC}"
fi

if groups $CURRENT_USER | grep -q '\bgpio\b'; then
    echo -e "  ${GREEN}✓${NC} gpioグループに所属しています"
else
    echo -e "  ${RED}✗${NC} gpioグループに所属していません"
    echo -e "${YELLOW}  → sudo usermod -a -G gpio $CURRENT_USER${NC}"
fi

if groups $CURRENT_USER | grep -q '\bdialout\b'; then
    echo -e "  ${GREEN}✓${NC} dialoutグループに所属しています"
else
    echo -e "  ${YELLOW}⚠${NC} dialoutグループに所属していません（カードリーダー用）"
    echo -e "${YELLOW}  → sudo usermod -a -G dialout $CURRENT_USER${NC}"
fi
echo ""

# ============================================================================
# 7. pcscdサービスのチェック
# ============================================================================
echo -e "${BLUE}[7] pcscdサービスのチェック${NC}"

if systemctl is-active --quiet pcscd; then
    echo -e "  ${GREEN}✓${NC} pcscdサービスは起動中です"
else
    echo -e "  ${RED}✗${NC} pcscdサービスが起動していません"
    echo -e "${YELLOW}  → sudo systemctl start pcscd${NC}"
fi

if systemctl is-enabled --quiet pcscd; then
    echo -e "  ${GREEN}✓${NC} pcscdサービスは自動起動が有効です"
else
    echo -e "  ${YELLOW}⚠${NC} pcscdサービスの自動起動が無効です"
    echo -e "${YELLOW}  → sudo systemctl enable pcscd${NC}"
fi
echo ""

# ============================================================================
# 8. カードリーダーのチェック
# ============================================================================
echo -e "${BLUE}[8] カードリーダーのチェック${NC}"

if command -v pcsc_scan > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} pcsc_scan コマンドが利用可能です"
    
    READERS=$(timeout 2 pcsc_scan -r 2>/dev/null | grep -c "Reader" || echo "0")
    if [ "$READERS" -gt 0 ]; then
        echo -e "  ${GREEN}✓${NC} カードリーダーが検出されました (${READERS}台)"
    else
        echo -e "  ${YELLOW}⚠${NC} カードリーダーが検出されませんでした"
        echo -e "${YELLOW}  → USBケーブルを確認してください${NC}"
    fi
else
    echo -e "  ${YELLOW}⚠${NC} pcsc_scan コマンドが見つかりません"
fi

echo -e "  ${BLUE}USBデバイス一覧:${NC}"
lsusb | while read line; do
    echo -e "    $line"
done
echo ""

# ============================================================================
# 9. I2Cデバイスのチェック
# ============================================================================
echo -e "${BLUE}[9] I2Cデバイスのチェック${NC}"

if [ -e "/dev/i2c-1" ]; then
    echo -e "  ${GREEN}✓${NC} /dev/i2c-1 が存在します"
    
    if command -v i2cdetect > /dev/null 2>&1; then
        echo -e "  ${BLUE}I2Cデバイススキャン:${NC}"
        sudo i2cdetect -y 1
    fi
else
    echo -e "  ${RED}✗${NC} /dev/i2c-1 が見つかりません"
    echo -e "${YELLOW}  → sudo raspi-config で I2C を有効化してください${NC}"
fi
echo ""

# ============================================================================
# 10. systemdサービスのチェック
# ============================================================================
echo -e "${BLUE}[10] systemdサービスのチェック${NC}"

SERVICE_FILE="/etc/systemd/system/card-reader.service"

if [ -f "$SERVICE_FILE" ]; then
    echo -e "  ${GREEN}✓${NC} サービスファイルが存在します"
    
    if systemctl is-active --quiet card-reader.service; then
        echo -e "  ${GREEN}✓${NC} サービスは起動中です"
    else
        echo -e "  ${YELLOW}⚠${NC} サービスは停止中です"
        echo -e "${YELLOW}  → sudo systemctl start card-reader.service${NC}"
    fi
    
    if systemctl is-enabled --quiet card-reader.service; then
        echo -e "  ${GREEN}✓${NC} 自動起動が有効です"
    else
        echo -e "  ${YELLOW}⚠${NC} 自動起動が無効です"
        echo -e "${YELLOW}  → sudo systemctl enable card-reader.service${NC}"
    fi
    
    echo -e "  ${BLUE}サービスの状態:${NC}"
    sudo systemctl status card-reader.service --no-pager -l | head -n 15
else
    echo -e "  ${RED}✗${NC} サービスファイルが存在しません"
    echo -e "${YELLOW}  → ./auto_setup.sh を実行してください${NC}"
fi
echo ""

# ============================================================================
# サマリー
# ============================================================================
echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}  診断完了${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo ""

echo -e "${YELLOW}問題が見つかった場合は、以下を実行してください:${NC}"
echo -e "  1. 完全セットアップ: ${GREEN}./auto_setup.sh${NC}"
echo -e "  2. サービス起動: ${GREEN}sudo systemctl start card-reader.service${NC}"
echo -e "  3. ログ確認: ${GREEN}sudo journalctl -u card-reader.service -f${NC}"
echo ""

