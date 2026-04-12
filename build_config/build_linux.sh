#!/bin/bash
# ============================================
# RAC - Linux Build Script
# Builds optimized Linux binary with PyInstaller
# ============================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

cd "$(dirname "$0")/.."
PROJECT_ROOT="$(pwd)"
BUILD_CONFIG="$PROJECT_ROOT/build_config"
DIST="$BUILD_CONFIG/dist_linux"

echo "============================================"
echo "RAC - Linux Build"
echo "============================================"
echo ""

echo "[1/5] Cleaning previous builds..."
rm -rf "$DIST"
rm -rf "$BUILD_CONFIG/build"
find "$PROJECT_ROOT/src" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$PROJECT_ROOT/src" -type f -name "*.pyc" -delete 2>/dev/null || true

echo "[2/5] Building with PyInstaller..."
cd "$BUILD_CONFIG"
python3 -m PyInstaller --clean -y rac.spec 2>&1 | tail -5

echo "[3/5] Organizing output..."
mkdir -p "$DIST"
cp -r "$BUILD_CONFIG/dist/RAC" "$DIST/"

echo "[4/5] Optimizing build size..."

DIST_INTERNAL="$DIST/RAC/_internal"

# --- Remove unused Qt plugins ---
QT_PLUGINS="$DIST_INTERNAL/PySide6/Qt/plugins"
if [ -d "$QT_PLUGINS" ]; then
    for d in wayland-decoration-client wayland-graphics-integration-client \
             wayland-shell-integration egldeviceintegrations generic \
             platforminputcontexts iconengines xcbglintegrations; do
        rm -rf "$QT_PLUGINS/$d"
    done

    # Keep only jpeg + gif in imageformats
    if [ -d "$QT_PLUGINS/imageformats" ]; then
        find "$QT_PLUGINS/imageformats" -type f ! -name "libqjpeg.so" ! -name "libqgif.so" -delete
    fi

    # Keep only xcb + wayland + offscreen in platforms
    if [ -d "$QT_PLUGINS/platforms" ]; then
        find "$QT_PLUGINS/platforms" -type f ! -name "libqxcb.so" ! -name "libqwayland.so" ! -name "libqoffscreen.so" -delete
    fi

    # Remove gtk platform theme
    if [ -d "$QT_PLUGINS/platformthemes" ]; then
        find "$QT_PLUGINS/platformthemes" -type f -name "*gtk*" -delete
    fi
fi

# --- Keep only PT translations ---
QT_TRANS="$DIST_INTERNAL/PySide6/Qt/translations"
if [ -d "$QT_TRANS" ]; then
    find "$QT_TRANS" -type f ! -name "qtbase_pt*" ! -name "qt_pt*" -delete
fi

# --- Remove unused Qt shared libs ---
QT_LIB="$DIST_INTERNAL/PySide6/Qt/lib"
if [ -d "$QT_LIB" ]; then
    for pattern in libQt6Quick* libQt6Qml* libQt6Pdf* libQt6Svg* \
                   libQt6VirtualKeyboard* libQt6WaylandClient* \
                   libQt6EglFS* libQt6WlShellIntegration* \
                   libQt6OpenGL* libQt6Network*; do
        rm -f "$QT_LIB"/$pattern
    done
fi

# --- Remove unused system libs ---
for pattern in libglycin-2.so* libgtk-3.so* libgdk-3.so* libatspi.so* \
               libatk-bridge-2.0.so* libatk-1.0.so* libepoxy.so* \
               libcairo-gobject.so* libcloudproviders.so* libXinerama.so* \
               libXcomposite.so* libXdamage.so*; do
    rm -f "$DIST_INTERNAL"/$pattern
done

# --- Remove CJK codecs and readline ---
DYNLOAD="$DIST_INTERNAL/python3.14/lib-dynload"
if [ -d "$DYNLOAD" ]; then
    for pattern in _codecs_jp* _codecs_kr* _codecs_cn* _codecs_tw* \
                   _codecs_hk* _codecs_iso2022* readline*; do
        rm -f "$DYNLOAD"/$pattern
    done
fi

# --- Trim ICU data (31M -> 2.9M, keeping root + pt locales) ---
TRIMMED_ICU="$BUILD_CONFIG/build_icu/libicudata.so.73"
ICU_TARGET="$DIST_INTERNAL/PySide6/Qt/lib/libicudata.so.73"
if [ -f "$TRIMMED_ICU" ] && [ -f "$ICU_TARGET" ]; then
    cp "$TRIMMED_ICU" "$ICU_TARGET"
    echo -e "  ${GREEN}ICU trimmed (31M -> 2.9M)${NC}"
fi

# --- Clean up temp src ---
rm -rf "$BUILD_CONFIG/_build_src"

echo "[5/5] Final build size:"
echo ""
FINAL_SIZE=$(du -sh "$DIST/RAC" | cut -f1)
echo -e "  ${GREEN}dist_linux/RAC/${NC}: $FINAL_SIZE"
echo ""
echo -e "${GREEN}Build complete!${NC}"
echo "  $DIST/RAC/RAC"
echo ""
echo "Test with:"
echo "  $DIST/RAC/RAC"
