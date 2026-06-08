#!/bin/bash
# ============================================
# RAC - Build & Release Script
# Builds for Windows (Wine), zips, tags, and
# creates a GitHub Release with the artifact.
#
# Usage: ./release.sh <version> [notes]
#   version: semver tag (e.g. 1.1.0)
#   notes:   release notes (default: "Release v<version>")
#
# Examples:
#   ./release.sh 1.1.0
#   ./release.sh 1.2.0 "Bug fixes and new stats page"
# ============================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

VERSION="${1:?Usage: $0 <version> [notes]}"
NOTES="${2:-Release v${VERSION}}"
TAG="v${VERSION}"
REPO="januvary/RAC"

if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo -e "${RED}[ERROR]${NC} Version must be semver (e.g. 1.1.0)"
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
    echo -e "${RED}[ERROR]${NC} Uncommitted changes detected. Commit or stash first."
    git status --short
    exit 1
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
