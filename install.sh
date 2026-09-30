#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
#  V4Z MEGA BOT — Installer by V4Z RASHD
#  Repo: https://github.com/v4zrashd/RASHDMegaBotTermuxx
# ============================================================
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; MAGENTA='\033[0;35m'; BLUE='\033[0;34m'; NC='\033[0m'; BOLD='\033[1m'

REPO="v4zrashd/RASHDMegaBotTermuxx"
APP_DIR="$HOME/.v4zmegabot/app"

clear
echo -e "${MAGENTA}${BOLD}"
echo '  ╔══════════════════════════════════════╗'
echo '  ║                                      ║'
echo '  ║       🤖  V4Z MEGA BOT  🤖            ║'
echo '  ║                                      ║'
echo '  ║        Installer by V4Z RASHD        ║'
echo '  ║                                      ║'
echo '  ╚══════════════════════════════════════╝'
echo -e "${NC}"
echo -e "  ${BLUE}${BOLD}📢 Telegram: ${CYAN}https://t.me/rashdteem${NC}\n"

echo -e "${CYAN}[1/5]${NC} Updating packages..."
pkg update -y >/dev/null 2>&1

echo -e "${CYAN}[2/5]${NC} Installing dependencies (python, ffmpeg, curl)..."
pkg install -y python ffmpeg curl >/dev/null 2>&1

echo -e "${CYAN}[3/5]${NC} Installing Python libraries..."
pip install -U python-telegram-bot yt-dlp qrcode pillow -q >/dev/null 2>&1

echo -e "${CYAN}[4/5]${NC} Installing bot files..."
mkdir -p "$APP_DIR"
curl -fsSL "https://raw.githubusercontent.com/${REPO}/main/megabot.py" -o "$APP_DIR/megabot.py"
curl -fsSL "https://raw.githubusercontent.com/${REPO}/main/v4zmegabot" -o "$PREFIX/bin/v4zmegabot"
chmod +x "$PREFIX/bin/v4zmegabot"

echo -e "${CYAN}[5/5]${NC} Bot token setup..."
echo ""
echo -e "${YELLOW}  Get a token first:${NC}"
echo -e "   1. Open Telegram → @BotFather"
echo -e "   2. Send /newbot → choose a name & username"
echo -e "   3. Copy the token it gives you"
echo ""
if [ ! -s "$HOME/.v4zmegabot/token" ]; then
    echo -ne "${YELLOW}  Paste your bot token (Enter to skip): ${NC}"
    read -r tok
    if [ -n "$tok" ]; then
        mkdir -p "$HOME/.v4zmegabot"
        echo "$tok" > "$HOME/.v4zmegabot/token"
        chmod 600 "$HOME/.v4zmegabot/token"
        echo -e "${GREEN}  ✓ Token saved.${NC}"
    else
        echo -e "${YELLOW}  Skipped — run 'v4zmegabot --set-token' later.${NC}"
    fi
else
    echo -e "${GREEN}  ✓ Token already saved.${NC}"
fi

echo ""
echo -e "${GREEN}${BOLD}  ✓ V4Z MEGA BOT installed!${NC}"
echo ""
echo -e "  Start it with:  ${CYAN}${BOLD}v4zmegabot${NC}"
echo -e "  Set token:      ${CYAN}v4zmegabot --set-token${NC}"
echo ""
echo -e "${MAGENTA}  — by V4Z RASHD ⚡${NC}"
