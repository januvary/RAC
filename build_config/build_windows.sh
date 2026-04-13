#!/bin/bash
# ============================================
# RAC - Windows Build Script (Linux + Wine)
# Creates Windows .exe using PyInstaller through Wine
# ============================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

cd "$(dirname "$0")/.."
PROJECT_ROOT="$(pwd)"
BUILD_CONFIG="$PROJECT_ROOT/build_config"
DIST="$BUILD_CONFIG/dist_windows"

PYTHON_VERSION="3.10"
PYTHON_SHORT="${PYTHON_VERSION//.}"
WINE_PYTHON="C:\\\\Python${PYTHON_SHORT}\\\\python.exe"

echo "============================================"
echo "RAC - Windows Build (Wine)"
echo "============================================"
echo ""

# --- Check prerequisites ---
echo "[1/6] Checking prerequisites..."

if ! command -v wine &>/dev/null; then
    echo -e "${RED}[ERROR]${NC} Wine is not installed!"
    echo "Install with: sudo dnf install wine"
    exit 1
fi

if ! wine $WINE_PYTHON --version &>/dev/null; then
    echo -e "${RED}[ERROR]${NC} Python $PYTHON_VERSION not found in Wine!"
    echo "Expected: $WINE_PYTHON"
    echo ""
    echo "Install with:"
    echo "  cd /tmp"
    echo "  wget https://www.python.org/ftp/python/${PYTHON_VERSION}.11/python-${PYTHON_VERSION}.11-amd64.exe"
    echo "  wine python-${PYTHON_VERSION}.11-amd64.exe /passive InstallAllUsers=1 PrependPath=1 TargetDir=C:\\\\Python${PYTHON_SHORT}"
    echo "  wine $WINE_PYTHON -m pip install --upgrade pip"
    echo "  wine $WINE_PYTHON -m pip install PySide6>=6.6.0 openpyxl>=3.1.0 pyinstaller>=6.0"
    exit 1
fi

WINE_PY_VER=$(wine $WINE_PYTHON --version 2>&1 | grep -v fixme | head -1)
echo -e "  ${GREEN}Python:${NC} $WINE_PY_VER"

# --- Clean ---
echo ""
echo "[2/6] Cleaning previous builds..."
rm -rf "$DIST"
rm -rf "$BUILD_CONFIG/build"
find "$PROJECT_ROOT/src" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$PROJECT_ROOT/src" -type f -name "*.pyc" -delete 2>/dev/null || true

# Clear Wine Python cache
wine $WINE_PYTHON -c "import sys; import shutil; [shutil.rmtree(p, ignore_errors=True) for p in [sys.prefix+'\\\\Lib\\\\site-packages\\\\PySide6\\\\__pycache__', sys.prefix+'\\\\Lib\\\\site-packages\\\\openpyxl\\\\__pycache__']]" 2>/dev/null || true

# --- Build ---
echo ""
echo "[3/6] Building with PyInstaller..."
cd "$BUILD_CONFIG"
yes | wine $WINE_PYTHON -m PyInstaller --clean -y rac.spec 2>&1 | grep -v "fixme" | grep -v "WARNING: Failed to run strip" | grep -v "FileNotFound\|Traceback\|subprocess\|Popen\|execute_child\|CreateProcess\|winapi\|process_collected"

if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}[ERROR]${NC} Build failed! Check error messages above."
    exit 1
fi

# --- Organize ---
echo ""
echo "[4/6] Organizing output..."
mkdir -p "$DIST"
cp -r "$BUILD_CONFIG/dist/RAC" "$DIST/"
cp "$BUILD_CONFIG/update_windows.ps1" "$DIST/RAC/update.ps1"

if [ ! -f "$DIST/RAC/RAC.exe" ]; then
    echo -e "${RED}[ERROR]${NC} RAC.exe was not created!"
    exit 1
fi

# --- Optimize ---
echo "[5/6] Optimizing build size..."

DIST_INTERNAL="$DIST/RAC/_internal"

# --- Remove unused Qt plugins (Windows) ---
QT_PLUGINS="$DIST_INTERNAL/PySide6/Qt/plugins"
if [ -d "$QT_PLUGINS" ]; then
    for d in wayland-decoration-client wayland-graphics-integration-client \
             wayland-shell-integration egldeviceintegrations generic \
             platforminputcontexts iconengines xcbglintegrations; do
        rm -rf "$QT_PLUGINS/$d"
    done

    # Keep only jpeg + gif in imageformats
    if [ -d "$QT_PLUGINS/imageformats" ]; then
        find "$QT_PLUGINS/imageformats" -type f ! -name "qjpeg.dll" ! -name "qgif.dll" -delete
    fi

    # Keep only windows platform plugin
    if [ -d "$QT_PLUGINS/platforms" ]; then
        find "$QT_PLUGINS/platforms" -type f ! -name "qwindows.dll" -delete
    fi

    # Remove styles
    rm -rf "$QT_PLUGINS/styles"
fi

# --- Keep only PT translations ---
QT_TRANS="$DIST_INTERNAL/PySide6/translations"
if [ -d "$QT_TRANS" ]; then
    find "$QT_TRANS" -type f ! -name "qtbase_pt*" ! -name "qt_pt*" -delete
fi

# --- Remove unused Qt DLLs ---
QT_BIN="$DIST_INTERNAL/PySide6"
if [ -d "$QT_BIN" ]; then
    for pattern in Qt6Quick*.dll Qt6Qml*.dll Qt6Pdf*.dll Qt6Svg*.dll \
                   Qt6VirtualKeyboard*.dll Qt6WaylandClient*.dll \
                   Qt6EglFS*.dll Qt6WlShellIntegration*.dll \
                   Qt6OpenGL*.dll Qt6Network*.dll Qt63D*.dll \
                   Qt6Bluetooth*.dll Qt6Charts*.dll Qt6DataVisualization*.dll \
                   Qt6Graphs*.dll Qt6Help*.dll Qt6HttpServer*.dll \
                   Qt6Labs*.dll Qt6Location*.dll Qt6Multimedia*.dll \
                   Qt6Nfc*.dll Qt6Positioning*.dll Qt6PrintSupport*.dll \
                   Qt6Qml*.dll Qt6Quick*.dll Qt6RemoteObjects*.dll \
                   Qt6Scxml*.dll Qt6Sensors*.dll Qt6SerialBus*.dll \
                   Qt6SerialPort*.dll Qt6ShaderTools*.dll Qt6SpatialAudio*.dll \
                   Qt6Sql*.dll Qt6StateMachine*.dll Qt6Test*.dll \
                   Qt6TextToSpeech*.dll Qt6UiTools*.dll Qt6VirtualKeyboard*.dll \
                   Qt6WebChannel*.dll Qt6WebEngine*.dll Qt6WebSockets*.dll \
                   Qt6WebView*.dll Qt6Xml*.dll; do
        rm -f "$QT_BIN"/$pattern
    done

    # Software OpenGL renderer - not needed on systems with GPU drivers
    rm -f "$QT_BIN/opengl32sw.dll"
fi

# --- Remove CJK codecs and readline ---
PY_DYNLOAD=$(find "$DIST_INTERNAL" -path "*/lib-dynload" -type d 2>/dev/null | head -1)
if [ -n "$PY_DYNLOAD" ] && [ -d "$PY_DYNLOAD" ]; then
    for pattern in _codecs_jp* _codecs_kr* _codecs_cn* _codecs_tw* \
                   _codecs_hk* _codecs_iso2022* readline*; do
        rm -f "$PY_DYNLOAD"/$pattern
    done
fi

# --- Clean up temp src ---
rm -rf "$BUILD_CONFIG/_build_src"
rm -rf "$BUILD_CONFIG/dist"

# --- Report ---
echo ""
echo "[6/6] Final build size:"
echo ""
FINAL_SIZE=$(du -sh "$DIST/RAC" | cut -f1)
echo -e "  ${GREEN}dist_windows/RAC/${NC}: $FINAL_SIZE"
echo ""
echo -e "${GREEN}Build complete!${NC}"
echo "  $DIST/RAC/RAC.exe"
echo ""
echo "Test with Wine:"
echo "  wine $DIST/RAC/RAC.exe"
echo ""
echo "To distribute to Windows users:"
echo "  1. Zip the entire dist_windows/RAC/ folder"
echo "  2. Users extract and run RAC.exe"
