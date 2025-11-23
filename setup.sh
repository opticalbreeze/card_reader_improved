#!/bin/bash
# ============================================================================
# カードリーダーシステム 自動セットアップスクリプト
# 初心者でも簡単にセットアップできるように全自動化
# ============================================================================

set -e  # エラーが発生したら停止

echo "========================================================================"
echo "  カードリーダーシステム 自動セットアップ"
echo "========================================================================"
echo ""
echo "このスクリプトは以下を自動的にインストール・設定します："
echo "  1. 必要なシステムパッケージ"
echo "  2. Pythonライブラリ"
echo "  3. カードリーダーのアクセス権限"
echo "  4. PC/SCサービス"
echo "  5. I2C設定"
echo ""
echo "所要時間: 約5-10分"
echo "========================================================================"
echo ""

# rootユーザーでの実行を確認
if [ "$EUID" -eq 0 ]; then 
    echo "[エラー] このスクリプトはroot権限で実行しないでください"
    echo "[ヒント] sudo なしで実行してください: ./setup.sh"
    exit 1
fi

echo "[1/7] システムパッケージリストを更新中..."
sudo apt-get update -qq

echo "[2/7] 必要なシステムパッケージをインストール中..."
sudo apt-get install -y -qq \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    python3-smbus \
    i2c-tools \
    libusb-1.0-0-dev \
    pcscd \
    libccid \
    pcsc-tools

echo "[3/7] I2Cを有効化中..."
if ! grep -q "^dtparam=i2c_arm=on" /boot/config.txt; then
    echo "dtparam=i2c_arm=on" | sudo tee -a /boot/config.txt > /dev/null
    echo "    I2Cを有効化しました（再起動後に有効）"
else
    echo "    I2Cは既に有効です"
fi

# i2cグループに追加
if ! groups $USER | grep -q i2c; then
    sudo usermod -a -G i2c $USER
    echo "    ユーザーをi2cグループに追加しました（再起動後に有効）"
else
    echo "    ユーザーは既にi2cグループに所属しています"
fi

echo "[4/7] 仮想環境を作成中..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "    仮想環境を作成しました"
else
    echo "    仮想環境は既に存在します"
fi

echo "[5/7] Pythonライブラリをインストール中..."
source venv/bin/activate
pip install --upgrade pip -qq

# requirements_pi.txtが存在する場合はそれを使用、なければ個別インストール
if [ -f "requirements_pi.txt" ]; then
    pip install -q -r requirements_pi.txt
else
    pip install -q \
        smbus2 \
        nfcpy \
        pyscard \
        requests \
        RPi.GPIO
fi

echo "[6/7] カードリーダーのアクセス権限を設定中..."
# Sony RC-S380のudevルール
UDEV_RULE='/etc/udev/rules.d/nfcdev.rules'
if [ ! -f "$UDEV_RULE" ]; then
    echo 'SUBSYSTEM=="usb", ACTION=="add", ATTRS{idVendor}=="054c", ATTRS{idProduct}=="06c1", GROUP="plugdev"' | sudo tee $UDEV_RULE > /dev/null
    sudo udevadm control --reload-rules
    echo "    udevルールを設定しました"
else
    echo "    udevルールは既に設定されています"
fi

# plugdevグループに追加
if ! groups $USER | grep -q plugdev; then
    sudo usermod -a -G plugdev $USER
    echo "    ユーザーをplugdevグループに追加しました（再起動後に有効）"
else
    echo "    ユーザーは既にplugdevグループに所属しています"
fi

echo "[7/7] PC/SCサービスを設定中..."
sudo systemctl enable pcscd
sudo systemctl start pcscd
echo "    PC/SCサービスを有効化・起動しました"

echo ""
echo "========================================================================"
echo "  セットアップ完了！"
echo "========================================================================"
echo ""
echo "次のステップ:"
echo ""
echo "  1. Raspberry Piを再起動してください:"
echo "     sudo reboot"
echo ""
echo "  2. 再起動後、設定ファイルを編集してください:"
echo "     nano client_config.json"
echo "     (サーバーのIPアドレスを正しく設定)"
echo ""
echo "  3. プログラムを起動してください:"
echo "     cd $(pwd)"
echo "     source venv/bin/activate  # 仮想環境を有効化（必須）"
echo "     python3 pi_client.py"
echo ""
echo "  または、起動スクリプトを使用（仮想環境を自動有効化）:"
echo "     ./start_pi_simple.sh"
echo "     または"
echo "     ./start_pi.sh"
echo ""
echo "========================================================================"
echo ""

# 再起動が必要か確認
NEED_REBOOT=false
if ! groups $USER | grep -q i2c || ! groups $USER | grep -q plugdev; then
    NEED_REBOOT=true
fi

if [ "$NEED_REBOOT" = true ]; then
    echo "[重要] グループ設定を有効にするため、再起動が必要です"
    echo ""
    read -p "今すぐ再起動しますか？ (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo reboot
    else
        echo "後で手動で再起動してください: sudo reboot"
    fi
fi

