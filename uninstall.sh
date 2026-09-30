#!/data/data/com.termux/files/usr/bin/bash
# V4Z MEGA BOT — Uninstaller by V4Z RASHD

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

echo -e "${YELLOW}Removing V4Z Mega Bot...${NC}"
rm -f "$PREFIX/bin/v4zmegabot"
rm -rf "$HOME/.v4zmegabot"

echo -e "${GREEN}✓ V4Z Mega Bot removed (including saved token).${NC}"
