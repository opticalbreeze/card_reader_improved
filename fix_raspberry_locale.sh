#!/bin/bash
# ============================================================================
# Fix Raspberry Pi Locale Settings to UTF-8
# ============================================================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}  Fix Raspberry Pi Locale Settings to UTF-8${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo ""

# Check current locale
echo -e "${YELLOW}[1/4]${NC} Current locale settings:"
locale | grep -E "LANG|LC_ALL"
echo ""

# Check available UTF-8 locales
echo -e "${YELLOW}[2/4]${NC} Checking available UTF-8 locales..."
if locale -a | grep -q "ja_JP.utf8\|ja_JP.UTF-8"; then
    echo -e "${GREEN}✅${NC} Japanese UTF-8 locale is available"
    TARGET_LOCALE="ja_JP.UTF-8"
else
    echo -e "${YELLOW}⚠️${NC}  Japanese UTF-8 locale not found. Checking C.UTF-8..."
    if locale -a | grep -q "C.utf8\|C.UTF-8"; then
        echo -e "${GREEN}✅${NC} C.UTF-8 locale is available"
        TARGET_LOCALE="C.UTF-8"
    else
        echo -e "${RED}❌${NC} No UTF-8 locale found. Installing..."
        sudo locale-gen ja_JP.UTF-8
        sudo update-locale LANG=ja_JP.UTF-8
        TARGET_LOCALE="ja_JP.UTF-8"
    fi
fi
echo ""

# Set locale for current session
echo -e "${YELLOW}[3/4]${NC} Setting locale for current session..."
export LANG=$TARGET_LOCALE
export LC_ALL=$TARGET_LOCALE
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1
echo -e "${GREEN}✅${NC} Locale set to: $TARGET_LOCALE"
echo ""

# Set locale permanently
echo -e "${YELLOW}[4/4]${NC} Setting locale permanently..."
if [ -f ~/.bashrc ]; then
    # Remove old locale settings if any
    sed -i '/^export LANG=/d' ~/.bashrc
    sed -i '/^export LC_ALL=/d' ~/.bashrc
    sed -i '/^export PYTHONIOENCODING=/d' ~/.bashrc
    
    # Add new settings
    echo "" >> ~/.bashrc
    echo "# UTF-8 Locale Settings" >> ~/.bashrc
    echo "export LANG=$TARGET_LOCALE" >> ~/.bashrc
    echo "export LC_ALL=$TARGET_LOCALE" >> ~/.bashrc
    echo "export PYTHONIOENCODING=utf-8" >> ~/.bashrc
    echo "export PYTHONUTF8=1" >> ~/.bashrc
    
    echo -e "${GREEN}✅${NC} Added to ~/.bashrc"
else
    echo -e "${YELLOW}⚠️${NC}  ~/.bashrc not found. Creating..."
    echo "# UTF-8 Locale Settings" > ~/.bashrc
    echo "export LANG=$TARGET_LOCALE" >> ~/.bashrc
    echo "export LC_ALL=$TARGET_LOCALE" >> ~/.bashrc
    echo "export PYTHONIOENCODING=utf-8" >> ~/.bashrc
    echo "export PYTHONUTF8=1" >> ~/.bashrc
    echo -e "${GREEN}✅${NC} Created ~/.bashrc"
fi

# Also set system-wide if possible
if [ -f /etc/default/locale ]; then
    echo ""
    echo -e "${BLUE}System-wide locale file found.${NC}"
    echo -e "${YELLOW}Do you want to set system-wide locale? (requires sudo) (y/N)${NC}"
    read -p "> " CONFIRM
    if [ "$CONFIRM" = "y" ] || [ "$CONFIRM" = "Y" ]; then
        sudo sed -i "s/^LANG=.*/LANG=$TARGET_LOCALE/" /etc/default/locale 2>/dev/null || echo "LANG=$TARGET_LOCALE" | sudo tee -a /etc/default/locale > /dev/null
        sudo sed -i "s/^LC_ALL=.*/LC_ALL=$TARGET_LOCALE/" /etc/default/locale 2>/dev/null || echo "LC_ALL=$TARGET_LOCALE" | sudo tee -a /etc/default/locale > /dev/null
        echo -e "${GREEN}✅${NC} System-wide locale updated"
        echo -e "${YELLOW}⚠️${NC}  Please reboot or log out/in for system-wide changes to take effect"
    fi
fi

echo ""
echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN}✅ Fix Complete${NC}"
echo -e "${GREEN}======================================================================${NC}"
echo ""
echo -e "${BLUE}Verification:${NC}"
echo "  Current session:"
echo "    LANG=$LANG"
echo "    LC_ALL=$LC_ALL"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Reload shell settings: source ~/.bashrc"
echo "  2. Or start a new terminal session"
echo "  3. Verify: locale"
echo "  4. Test: bash start_pi.sh"
echo ""

