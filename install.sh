#!/usr/bin/env bash
set -u
MODS_DIR="$(dirname "$(realpath "$0")")"
TARGET="${SERPANTINUM_DIR:-$HOME/.local/share/serpantinum/src}"
CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}/serpantinum/niko.json"

B=$'\033[1m'; G=$'\033[32m'; R=$'\033[31m'; Y=$'\033[33m'; N=$'\033[0m'
ok()   { echo "  ${G}ok${N}  $*"; }
warn() { echo "  ${Y}!!${N}  $*"; }
die()  { echo "  ${R}xx${N}  $*"; exit 1; }
ask()  { local a; read -r -p "$1 [Y/n] " a; [[ -z "$a" || "$a" =~ ^[Yy] ]]; }

echo "${B}Niko installer${N}"

echo; echo "${B}1. serpantinum${N}"
[ -d "$TARGET" ] || die "serpantinum not found at $TARGET. Install it first (github.com/ilyamiro/serpantinum), or set SERPANTINUM_DIR."
ok "found at $TARGET"

echo; echo "${B}2. Packages${N}"
need=()
have_pkg() { pacman -Qq "$1" >/dev/null 2>&1; }
if command -v pacman >/dev/null; then
    for p in quickshell hyprland qt6-declarative qt6-multimedia qt6-quick3d playerctl libnotify python grim; do
        have_pkg "$p" && ok "$p" || { warn "$p is missing"; need+=("$p"); }
    done
    if [ ${#need[@]} -gt 0 ]; then
        if ask "Install ${need[*]} with pacman (needs sudo)?"; then
            sudo pacman -S --needed "${need[@]}" || die "pacman failed"
        else
            warn "Skipped. Niko may not start without them."
        fi
    fi
else
    warn "Not an Arch system: install quickshell, hyprland, Qt6 (declarative, multimedia, quick3d), playerctl, libnotify, python and grim yourself."
fi
command -v python3 >/dev/null || die "python3 is required"

echo; echo "${B}3. Claude${N}"
if ! command -v claude >/dev/null && [ ! -x "$HOME/.local/bin/claude" ]; then
    warn "Claude Code is not installed (Niko needs it to talk)."
    echo "     Install it from https://claude.com/claude-code (e.g. the official install script), then run this again."
    echo "     Niko will still run without it, just without chatting."
else
    CLAUDE="$(command -v claude || echo "$HOME/.local/bin/claude")"
    ok "found $CLAUDE"
    if "$CLAUDE" auth status 2>/dev/null | grep -q '"loggedIn": true'; then
        ok "already signed in"
    else
        warn "not signed in"
        if ask "Sign in to Claude now (opens your browser)?"; then
            "$CLAUDE" auth login || warn "sign-in did not finish; run 'claude auth login' later"
        fi
    fi
fi

echo; echo "${B}4. Applying Niko to serpantinum${N}"
"$MODS_DIR/apply.sh" || die "could not apply the mods (see above)"
case ":$PATH:" in *":$HOME/.local/bin:"*) ;; *) warn "$HOME/.local/bin is not on your PATH: add it so the 'niko' command works." ;; esac

echo; echo "${B}5. Settings${N}"
mkdir -p "$(dirname "$CONFIG")"
cur="$(python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('userName',''))" "$CONFIG" 2>/dev/null || true)"
read -r -p "  What should Niko call you? [${cur:-skip}] " name
name="${name:-$cur}"
if [ -n "$name" ]; then
    python3 - "$CONFIG" "$name" <<'PY'
import json, sys
p, n = sys.argv[1:3]
try: d = json.load(open(p))
except Exception: d = {}
d["userName"] = n
json.dump(d, open(p, "w"), indent=2)
PY
    ok "saved name: $name"
fi

echo; echo "${B}6. Start${N}"
if ask "Restart the shell and start Niko now?"; then
    command -v serpantinumd >/dev/null && { serpantinumd stop; sleep 1; serpantinumd start; sleep 4; }
    "$HOME/.local/bin/niko" run
fi

echo
echo "${G}Done.${N} Commands: niko run | kill | restart | status | skins"
