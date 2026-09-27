#!/usr/bin/env bash
#
# install.sh - derpi-cli installer.
#
# Usage:
#   curl -fsSL https://derpy.me/install.sh | bash
#   curl -fsSL https://derpy.me/install.sh | bash -s -- --key API_KEY
#   bash install.sh --uninstall
#
set -euo pipefail

# ---------- Constants ----------
REPO_URL="${DERPI_REPO_URL:-https://github.com/arkain123/derpi-cli.git}"
INSTALL_DIR="${DERPI_INSTALL_DIR:-$HOME/.local/share/derpi-cli}"
BIN_DIR="$HOME/.local/bin"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/derpi-cli"
CONFIG_FILE="$CONFIG_DIR/config.json"

# Colors (if available)
if [ -t 1 ]; then
    RED=$'\033[0;31m'; GREEN=$'\033[0;32m'; YELLOW=$'\033[1;33m'
    BLUE=$'\033[0;34m'; BOLD=$'\033[1m'; NC=$'\033[0m'
else
    RED=''; GREEN=''; YELLOW=''; BLUE=''; BOLD=''; NC=''
fi

log()  { printf '%s\n' "${BLUE}==>${NC} ${BOLD}$*${NC}"; }
ok()   { printf '%s\n' "${GREEN}✓${NC} $*"; }
warn() { printf '%s\n' "${YELLOW}⚠${NC} $*" >&2; }
die()  { printf '%s\n' "${RED}✗${NC} $*" >&2; exit 1; }

# ---------- Args ----------
API_KEY=""
UNINSTALL=0
while [ $# -gt 0 ]; do
    case "$1" in
        --key)        API_KEY="$2"; shift 2 ;;
        --key=*)      API_KEY="${1#*=}"; shift ;;
        --uninstall)  UNINSTALL=1; shift ;;
        --dir)        INSTALL_DIR="$2"; shift 2 ;;
        -h|--help)
            cat <<EOF
derpi-cli installer

Usage:
  install.sh [OPTIONS]

Options:
  --key KEY       Save API key to config
  --dir DIR       Install directory (default: ~/.local/share/derpi-cli)
  --uninstall     Remove derpi-cli
  -h, --help      Show this help

Examples:
  curl -fsSL https://example.com/install.sh | bash
  curl -fsSL https://example.com/install.sh | bash -s -- --key abc123
EOF
            exit 0
            ;;
        *) die "Unknown option: $1" ;;
    esac
done

# ---------- Deleting ----------
if [ "$UNINSTALL" -eq 1 ]; then
    log "Removing derpi-cli..."
    if command -v pipx >/dev/null 2>&1; then
        pipx uninstall derpi-cli 2>/dev/null || true
    fi
    rm -rf "$INSTALL_DIR"
    ok "Package removed."
    warn "Config remains: $CONFIG_FILE"
    warn "Delete manually, if not needed: rm -rf $CONFIG_DIR"
    exit 0
fi

# ---------- Checking Python ----------
log "Checking Python..."
if ! command -v python3 >/dev/null 2>&1; then
    die "Python 3 not found. Install python3 and try again."
fi

PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 9 ]; }; then
    die "Python 3.9+ needed, now is $PY_VERSION"
fi
ok "Python $PY_VERSION"

# ---------- pipx ----------
log "Checking pipx..."
if ! command -v pipx >/dev/null 2>&1; then
    warn "pipx not found. Trying to install..."

    if command -v apt >/dev/null 2>&1; then
        sudo apt update -qq
        sudo apt install -y pipx
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y pipx
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -S --noconfirm python-pipx
    elif command -v brew >/dev/null 2>&1; then
        brew install pipx
    else
        die "Cannot install pipx automaticly. Install manually: https://pipx.pypa.io"
    fi
fi

pipx ensurepath >/dev/null 2>&1 || true
ok "pipx is ready"

# ---------- Downloading sources ----------
log "Downloading sources to $INSTALL_DIR..."

if [ -d "$INSTALL_DIR/.git" ]; then
    # Updating existing clone
    (cd "$INSTALL_DIR" && git pull --ff-only) || warn "git pull finished with error, using presented"
elif [ -f "./pyproject.toml" ] && grep -q 'name = "derpi-cli"' ./pyproject.toml 2>/dev/null; then
    # Starting from local project
    INSTALL_DIR="$(pwd)"
    ok "Using local copy: $INSTALL_DIR"
else
    # Cloning
    if ! command -v git >/dev/null 2>&1; then
        die "git not found. Install git or clone repo manually."
    fi
    mkdir -p "$(dirname "$INSTALL_DIR")"
    git clone --depth 1 "$REPO_URL" "$INSTALL_DIR"
fi

[ -f "$INSTALL_DIR/pyproject.toml" ] || die "pyproject.toml not found in $INSTALL_DIR"
ok "Sources OK"

# ---------- Installing ----------
log "Installing derpi-cli with pipx..."
if pipx list --short 2>/dev/null | grep -q '^derpi-cli '; then
    pipx uninstall derpi-cli >/dev/null 2>&1 || true
fi
pipx install -e "$INSTALL_DIR"
ok "Installed"

# ---------- PATH ----------
log "Checking PATH..."
if ! echo "$PATH" | tr ':' '\n' | grep -qx "$BIN_DIR"; then
    warn "$BIN_DIR not in PATH. Adding to ~/.bashrc..."

    SHELL_RC="$HOME/.bashrc"
    [ -n "${ZSH_VERSION:-}" ] && SHELL_RC="$HOME/.zshrc"
    [ -f "$HOME/.zshrc" ] && [ ! -f "$HOME/.bashrc" ] && SHELL_RC="$HOME/.zshrc"

    if ! grep -q "export PATH=\"$BIN_DIR:\$PATH\"" "$SHELL_RC" 2>/dev/null; then
        {
            echo ""
            echo "# Added by derpi-cli installer"
            echo "export PATH=\"$BIN_DIR:\$PATH\""
        } >> "$SHELL_RC"
        ok "PATH updated in $SHELL_RC"
        warn "Restart shell or run: source $SHELL_RC"
    fi
    export PATH="$BIN_DIR:$PATH"
else
    ok "$BIN_DIR already in PATH"
fi

# ---------- config ----------
log "Checking config..."
mkdir -p "$CONFIG_DIR"
if [ ! -f "$CONFIG_FILE" ]; then
    KEY_FIELD="\"\""
    [ -n "$API_KEY" ] && KEY_FIELD="\"$API_KEY\""

    cat > "$CONFIG_FILE" <<EOF
{
  "api_key": $KEY_FIELD,
  "rate_limit_delay": 0.5,
  "default_filter_id": null,
  "default_output_dir": "$HOME/Downloads"
}
EOF
    chmod 600 "$CONFIG_FILE"
    ok "Config created: $CONFIG_FILE"
else
    ok "Config already exists: $CONFIG_FILE"
fi

# ---------- Final check ----------
log "Checking installation..."
export PATH="$BIN_DIR:$PATH"

if command -v derpi >/dev/null 2>&1; then
    VERSION=$(derpi --version 2>/dev/null | awk '{print $NF}')
    ok "derpi $VERSION installed"
else
    die "derpi not found in PATH. Try to install shell."
fi

# ---------- Final message ----------
cat <<EOF

${GREEN}${BOLD}Done!${NC}

Fast start:
  ${BOLD}derpi search "fluttershy, safe"${NC}
  ${BOLD}derpi download "fluttershy, safe" --limit 20${NC}
  ${BOLD}derpi random "pinkie pie, safe"${NC}
  ${BOLD}derpi info 123456${NC}

Config:   $CONFIG_FILE
Source: $INSTALL_DIR
Binary:    $BIN_DIR/derpi

If API-key not configured, open config and configure it:
  nano $CONFIG_FILE

API-key can be found there: https://derpibooru.org/account
EOF

if ! echo "$PATH" | tr ':' '\n' | grep -qx "$BIN_DIR"; then
    echo
    warn "Don't forget to: source ~/.bashrc (or restart terminal)"
fi
