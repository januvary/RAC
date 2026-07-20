#!/bin/bash
# ============================================
# RAC - Build & Release Script
# Builds for Windows (Wine), zips, tags, and
# creates a GitHub Release with the artifact.
#
# Run directly or: ./release.sh <version> [notes]
# ============================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

cleanup() {
    exit_code=$?
    if [ "$exit_code" -ne 0 ] && [ -z "$1" ]; then
        echo ""
        echo -e "${RED}Script exited with error (code $exit_code).${NC}"
    fi
    if [ -z "$1" ]; then
        read -rp "Press Enter to close..."
    fi
    exit "$exit_code"
}
trap 'cleanup' EXIT

if [ -z "$1" ]; then
    echo -e "${YELLOW}RAC - Release${NC}"
    echo ""
    read -rp "Version (e.g. 1.0.0): " VERSION
    if [ -z "$VERSION" ]; then
        echo -e "${RED}[ERROR]${NC} Version is required."
        exit 1
    fi
    read -rp "Notes [optional]: " NOTES
    NOTES="${NOTES:-Release v${VERSION}}"
    INTERACTIVE=1
else
    VERSION="$1"
    NOTES="${2:-Release v${VERSION}}"
fi
TAG="v${VERSION}"
REPO="januvary/RAC"

if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo -e "${RED}[ERROR]${NC} Version must be semver (e.g. 1.0.0)"
    exit 1
fi

cd "$(dirname "$0")/.."
PROJECT_ROOT="$(pwd)"
BUILD_CONFIG="$PROJECT_ROOT/build_config"
DIST_WINDOWS="$BUILD_CONFIG/dist_windows"
ZIP_NAME="RAC-${TAG}-windows.zip"
ZIP_PATH="/tmp/${ZIP_NAME}"

echo -e "${YELLOW}============================================${NC}"
echo -e "${YELLOW}RAC - Release ${TAG}${NC}"
echo -e "${YELLOW}============================================${NC}"
echo ""

echo "[1/6] Checking for uncommitted changes..."
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo -e "${YELLOW}[WARN]${NC} Uncommitted changes detected:"
    git status --short
    echo ""
    read -rp "Commit all changes before releasing? [y/N]: " COMMIT_CHOICE
    if [[ "$COMMIT_CHOICE" =~ ^[Yy]$ ]]; then
        read -rp "Commit message: " COMMIT_MSG
        COMMIT_MSG="${COMMIT_MSG:-pre-release commit}"
        git add -A
        git commit -m "$COMMIT_MSG"
        echo -e "  ${GREEN}Committed.${NC}"
    else
        echo -e "${RED}[ERROR]${NC} Cannot release with uncommitted changes."
        exit 1
    fi
fi

if git tag -l "$TAG" | grep -q "$TAG"; then
    echo -e "${RED}[ERROR]${NC} Tag ${TAG} already exists."
    exit 1
fi

if gh release view "$TAG" -R "$REPO" &>/dev/null; then
    echo -e "${RED}[ERROR]${NC} Release ${TAG} already exists on GitHub."
    exit 1
fi

echo -e "  ${GREEN}Clean working tree.${NC}"
echo ""

echo "[2/6] Bumping version to ${VERSION}..."
VERSION_FILE="$PROJECT_ROOT/src/__init__.py"
sed -i "s/^__version__ = .*/__version__ = \"${VERSION}\"/" "$VERSION_FILE"
git add "$VERSION_FILE"
git commit -m "Bump version to ${TAG}"
echo -e "  ${GREEN}src/__init__.py${NC} -> __version__ = \"${VERSION}\""
echo ""

echo "[3/6] Building Windows version..."
bash "$BUILD_CONFIG/build_windows.sh"
echo ""

if [ ! -f "$DIST_WINDOWS/RAC/RAC.exe" ]; then
    echo -e "${RED}[ERROR]${NC} Build failed - RAC.exe not found."
    exit 1
fi

echo "[4/6] Packaging..."
rm -f "$ZIP_PATH"
cd "$DIST_WINDOWS"
zip -r "$ZIP_PATH" RAC/ -q
ZIP_SIZE=$(du -sh "$ZIP_PATH" | cut -f1)
echo -e "  ${GREEN}${ZIP_NAME}${NC}: $ZIP_SIZE"
echo ""

echo "[5/6] Creating tag ${TAG}..."
git tag "$TAG"
git push origin "$TAG"
echo ""

echo "[6/6] Creating GitHub release..."
gh release create "$TAG" "$ZIP_PATH" \
    --repo "$REPO" \
    --title "$TAG" \
    --notes "$NOTES"
echo ""

echo -e "${GREEN}Done!${NC} $ZIP_SIZE uploaded to:"
echo "  https://github.com/$REPO/releases/tag/$TAG"
