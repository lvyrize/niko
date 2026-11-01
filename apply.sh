#!/usr/bin/env bash

MODS_DIR="$(dirname "$(realpath "$0")")"
PATCH="$MODS_DIR/niko.patch"
FILES="$MODS_DIR/files"
TARGET="${SERPANTINUM_DIR:-$HOME/.local/share/serpantinum/src}"

if [ ! -d "$TARGET" ]; then
    echo "serpantinum not found at $TARGET"
    exit 1
fi

copy_files() {
    [ -d "$FILES" ] && cp -r "$FILES/." "$TARGET/"
    if [ -f "$TARGET/scripts/niko/niko" ]; then
        chmod +x "$TARGET/scripts/niko/niko"
        mkdir -p "$HOME/.local/bin"
        ln -sf "$TARGET/scripts/niko/niko" "$HOME/.local/bin/niko"
    fi
    return 0
}

if patch -p1 -R --dry-run -s -f -d "$TARGET" < "$PATCH" >/dev/null 2>&1; then
    copy_files
    echo "Niko is already applied, nothing to do."
    exit 0
fi

if ! patch -p1 --dry-run -s -f -d "$TARGET" < "$PATCH"; then
    echo
    echo "The update changed these files too much for the patch to apply cleanly."
    echo "Nothing was changed. Ask for help re-porting the mods to the new version."
    exit 1
fi

patch -p1 -s -f -d "$TARGET" < "$PATCH" && copy_files && echo "Niko applied. Restart the shell: serpantinumd stop && serpantinumd start"
