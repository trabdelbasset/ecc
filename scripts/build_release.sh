#!/bin/bash
#
# Complete release build script for ChipCompiler ECC
# This script builds both the Python API server and the Tauri application
#

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
GUI_DIR="$PROJECT_ROOT/chipcompiler/gui"
TAURI_DIR="$GUI_DIR/src-tauri"
BINARIES_DIR="$TAURI_DIR/binaries"
VENV_DIR="$PROJECT_ROOT/.venv"
PYTHON_VERSION="3.10"
ENABLE_OSS_CAD_SUITE=${ENABLE_OSS_CAD_SUITE:-true}
ECC_TOOLS_ROOT="$PROJECT_ROOT/chipcompiler/thirdparty/ecc-tools"
ECC_PY_GLOB="$ECC_TOOLS_ROOT/bin/ecc_py*.so"
OSS_CAD_DIR="$PROJECT_ROOT/chipcompiler/thirdparty/oss-cad-suite"
TAURI_RESOURCES_DIR="$TAURI_DIR/resources"
OSS_CAD_BUNDLE_DIR="$TAURI_RESOURCES_DIR/oss-cad-suite"

echo "=========================================="
echo "ChipCompiler ECC Release Build"
echo "=========================================="
echo "Project root: $PROJECT_ROOT"
echo ""

# Get target platform
TARGET=$(rustc -vV | grep host | cut -d' ' -f2)
echo "Target platform: $TARGET"
echo ""

# Step 1: Setup Python environment with uv (aligned with build.sh)
echo "=== Step 1: Setting up Python environment ==="
if ! command -v uv &> /dev/null; then
    echo "ERROR: uv is not installed or not in PATH"
    echo "Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi
echo "Syncing Python ${PYTHON_VERSION} environment with uv..."
uv sync --frozen --all-groups --python ${PYTHON_VERSION}
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"
echo "Python environment ready."
echo ""

# Step 2: Ensure yosys is available (required by runtime)
echo "=== Step 2: Ensuring yosys is available ==="
if command -v yosys &> /dev/null; then
    echo "yosys found: $(command -v yosys)"
else
    if [ "$ENABLE_OSS_CAD_SUITE" == "true" ]; then
        echo "yosys not found, installing OSS CAD Suite..."
        if [ -d "${OSS_CAD_DIR}" ] && [ -f "${OSS_CAD_DIR}/bin/yosys" ]; then
            echo "OSS CAD Suite already exists at ${OSS_CAD_DIR}, skipping download..."
        else
            LATEST_TAG=$(curl -s "https://api.github.com/repos/YosysHQ/oss-cad-suite-build/releases/latest" | grep -o '"tag_name": *"[^"]*"' | cut -d'"' -f4)
            OSS_CAD_URL="https://github.com/YosysHQ/oss-cad-suite-build/releases/download/${LATEST_TAG}/oss-cad-suite-linux-x64-${LATEST_TAG//-/}.tgz"
            mkdir -p "${OSS_CAD_DIR}"
            TMP_DIR=$(mktemp -d)
            echo "Downloading OSS CAD Suite from ${OSS_CAD_URL}..."
            curl -fL "${OSS_CAD_URL}" -o "${TMP_DIR}/oss-cad-suite.tgz"
            tar -xzf "${TMP_DIR}/oss-cad-suite.tgz" -C "${OSS_CAD_DIR}" --strip-components=1
            rm -rf "${TMP_DIR}/oss-cad-suite.tgz"
        fi
        export PATH="${OSS_CAD_DIR}/bin:$PATH"
        if command -v yosys &> /dev/null; then
            echo "yosys installed: $(command -v yosys)"
        else
            echo "ERROR: yosys still not found after OSS CAD Suite setup."
            exit 1
        fi
    else
        echo "ERROR: yosys not found and ENABLE_OSS_CAD_SUITE=false"
        exit 1
    fi
fi
echo ""

# Step 3: Stage Yosys runtime for bundling
echo "=== Step 3: Staging Yosys runtime ==="
rm -rf "$OSS_CAD_BUNDLE_DIR"
mkdir -p "$OSS_CAD_BUNDLE_DIR/bin" "$OSS_CAD_BUNDLE_DIR/share"

YOSYS_BIN_SRC="$OSS_CAD_DIR/bin/yosys"
if [[ "$TARGET" == *"windows"* ]]; then
    YOSYS_BIN_SRC="$OSS_CAD_DIR/bin/yosys.exe"
fi

if [ ! -f "$YOSYS_BIN_SRC" ]; then
    echo "ERROR: yosys binary not found at $YOSYS_BIN_SRC"
    exit 1
fi

SLANG_SRC=$(ls "$OSS_CAD_DIR/share/yosys/plugins"/slang.* 2>/dev/null | head -1)
if [ -z "$SLANG_SRC" ]; then
    echo "ERROR: slang plugin not found under $OSS_CAD_DIR/share/yosys/plugins"
    exit 1
fi

cp "$YOSYS_BIN_SRC" "$OSS_CAD_BUNDLE_DIR/bin/"
if [ -f "$OSS_CAD_DIR/bin/abc" ]; then
    cp "$OSS_CAD_DIR/bin/abc" "$OSS_CAD_BUNDLE_DIR/bin/"
    chmod +x "$OSS_CAD_BUNDLE_DIR/bin/abc"
fi
cp -a "$OSS_CAD_DIR/share/yosys" "$OSS_CAD_BUNDLE_DIR/share/"
chmod +x "$OSS_CAD_BUNDLE_DIR/bin/$(basename "$YOSYS_BIN_SRC")"
echo "Bundled yosys: $OSS_CAD_BUNDLE_DIR/bin/$(basename "$YOSYS_BIN_SRC")"
echo "Bundled share/yosys: $OSS_CAD_BUNDLE_DIR/share/yosys"
if [ -f "$OSS_CAD_BUNDLE_DIR/bin/abc" ]; then
    echo "Bundled abc: $OSS_CAD_BUNDLE_DIR/bin/abc"
fi
echo ""

# Step 4: Ensure ecc_py is built (required by chipcompiler.spec)
echo "=== Step 4: Ensuring ecc_py is built ==="
if ls $ECC_PY_GLOB >/dev/null 2>&1; then
    echo "ecc_py already exists in $ECC_TOOLS_ROOT/bin."
else
    echo "ecc_py not found, building..."
    if [ ! -d "$ECC_TOOLS_ROOT" ]; then
        echo "ERROR: ecc-tools submodule not found. Run: git submodule update --init --recursive"
        exit 1
    fi
    git submodule update --init --recursive

    BUILD_DIR="$ECC_TOOLS_ROOT/build"
    mkdir -p "$BUILD_DIR"
    rm -rf "$BUILD_DIR/CMakeCache.txt" "$BUILD_DIR/CMakeFiles" "$BUILD_DIR/build.ninja" "$BUILD_DIR/Makefile"

    cd "$BUILD_DIR"
    if ! command -v cmake &> /dev/null; then
        echo "ERROR: cmake not found. Please install cmake."
        exit 1
    fi

    if command -v ninja &> /dev/null; then
        echo "Configuring with Ninja..."
        cmake -G Ninja -DBUILD_AIEDA=ON ..
        echo "Building ecc_py with Ninja..."
        ninja ecc_py
    else
        echo "Configuring with default generator..."
        cmake -DBUILD_AIEDA=ON ..
        echo "Building ecc_py with make..."
        make -j$(nproc) ecc_py
    fi

    if ! ls $ECC_PY_GLOB >/dev/null 2>&1; then
        echo "ERROR: ecc_py build failed (ecc_py*.so not found)."
        exit 1
    fi
fi
echo ""

# Step 5: Build API Server with PyInstaller
echo "=== Step 5: Building API Server ==="
cd "$PROJECT_ROOT"

# Clean previous builds
rm -rf build dist __pycache__

# Build with PyInstaller
echo "Running PyInstaller..."
PYINSTALLER_ONEFILE=1 pyinstaller chipcompiler.spec --clean --noconfirm

SOURCE_BINARY="dist/chipcompiler"
if [[ "$TARGET" == *"windows"* ]]; then
    SOURCE_BINARY="${SOURCE_BINARY}.exe"
fi

if [ ! -f "$SOURCE_BINARY" ]; then
    echo "ERROR: PyInstaller build failed"
    exit 1
fi
echo "API Server built successfully."
echo ""

# Step 6: Copy binary to Tauri binaries directory
echo "=== Step 6: Installing API Server binary ==="
mkdir -p "$BINARIES_DIR"

# Determine binary name based on platform
BINARY_NAME="api-server-$TARGET"
if [[ "$TARGET" == *"windows"* ]]; then
    BINARY_NAME="$BINARY_NAME.exe"
fi

cp "$SOURCE_BINARY" "$BINARIES_DIR/$BINARY_NAME"
chmod +x "$BINARIES_DIR/$BINARY_NAME"
echo "Installed: $BINARIES_DIR/$BINARY_NAME"
echo ""

# Step 7: Install frontend dependencies
echo "=== Step 7: Installing frontend dependencies ==="
cd "$GUI_DIR"
if command -v pnpm &> /dev/null; then
    pnpm install
else
    echo "pnpm not found, installing..."
    npm install -g pnpm
    pnpm install
fi
echo "Frontend dependencies installed."
echo ""

# Step 8: Build Tauri application
echo "=== Step 8: Building Tauri application ==="
pnpm run tauri build

# Step 9: Copy API Server binary to release directory (for direct execution)
echo "=== Step 9: Copying API Server to release directory ==="
RELEASE_DIR="$TAURI_DIR/target/release"
if [ -d "$RELEASE_DIR" ]; then
    cp "$BINARIES_DIR/$BINARY_NAME" "$RELEASE_DIR/$BINARY_NAME"
    chmod +x "$RELEASE_DIR/$BINARY_NAME"
    echo "Copied: $RELEASE_DIR/$BINARY_NAME"
else
    echo "Warning: Release directory not found, skipping copy"
fi
echo ""

echo ""
echo "=========================================="
echo "Build Complete!"
echo "=========================================="
echo ""
echo "Output locations:"
echo "  - Executable: $TAURI_DIR/target/release/ecc-client"
echo "  - Bundles:    $TAURI_DIR/target/release/bundle/"
echo ""

# List generated bundles
if [ -d "$TAURI_DIR/target/release/bundle" ]; then
    echo "Generated packages:"
    find "$TAURI_DIR/target/release/bundle" -type f \( -name "*.dmg" -o -name "*.app" -o -name "*.deb" -o -name "*.rpm" -o -name "*.AppImage" -o -name "*.msi" -o -name "*.exe" \) 2>/dev/null | while read f; do
        echo "  - $f"
    done
fi
