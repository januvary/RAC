#!/bin/bash
# RAC - Source Update Script (Linux)
# Downloads latest src/ from remote and replaces bundled source.
# No git required - downloads a zip archive.
#
# Usage: ./update.sh [branch]
#   branch: git branch to download (default: main)

set -e

BRANCH="${1:-main}"
REPO_URL="https://github.com/januvary/RAC/archive/refs/heads/${BRANCH}.zip"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"
SRC_DIR="$APP_DIR/_internal/src"
BACKUP_DIR="$APP_DIR/_internal/src_backup"
TMP_DIR=$(mktemp -d)

echo "=== RAC Update ==="
echo "Branch: $BRANCH"
echo ""

if [ ! -d "$SRC_DIR" ]; then
    echo "[ERROR] Cannot find _internal/src/ - is this the right directory?"
    exit 1
fi

echo "[1/4] Downloading latest source..."
if command -v curl &>/dev/null; then
    HTTP_CODE=$(curl -L -o "$TMP_DIR/source.zip" -w "%{http_code}" "$REPO_URL" 2>/dev/null)
elif command -v wget &>/dev/null; then
    HTTP_CODE=$(wget -q -O "$TMP_DIR/source.zip" "$REPO_URL" && echo "200")
else
    echo "[ERROR] Neither curl nor wget found. Install one and try again."
    exit 1
fi

if [ "$HTTP_CODE" != "200" ]; then
    echo "[ERROR] Download failed (HTTP $HTTP_CODE). Check REPO_URL and BRANCH."
    rm -rf "$TMP_DIR"
    exit 1
fi

echo "[2/4] Extracting..."
unzip -q "$TMP_DIR/source.zip" -d "$TMP_DIR/extracted"
EXTRACTED_SRC=$(find "$TMP_DIR/extracted" -maxdepth 2 -type d -name "src" | head -1)

if [ -z "$EXTRACTED_SRC" ]; then
    echo "[ERROR] Could not find src/ in downloaded archive."
    rm -rf "$TMP_DIR"
    exit 1
fi

echo "[3/4] Replacing source files..."
rm -rf "$BACKUP_DIR"
mv "$SRC_DIR" "$BACKUP_DIR"
cp -r "$EXTRACTED_SRC" "$SRC_DIR"
find "$SRC_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

echo "[4/4] Cleaning up..."
rm -rf "$TMP_DIR"

echo ""
echo "Update complete! Backup saved to _internal/src_backup/"
echo "Restart RAC to apply changes."
echo ""
echo "To rollback: mv _internal/src_backup/ _internal/src/"
