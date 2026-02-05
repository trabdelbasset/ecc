#!/usr/bin/env bash
# CI-oriented release build script for ChipCompiler ECC
# Assumes dependencies and submodules are already installed.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

source "$PROJECT_ROOT/scripts/common.sh"

GUI_DIR="$PROJECT_ROOT/chipcompiler/gui"
TAURI_DIR="$GUI_DIR/src-tauri"
BINARIES_DIR="$TAURI_DIR/binaries"
TAURI_RESOURCES_DIR="$TAURI_DIR/resources"
OSS_CAD_BUNDLE_DIR="$TAURI_RESOURCES_DIR/oss-cad-suite"

log() {
    echo "[$(date +%H:%M:%S)] $*"
}

require_venv() {
    if [ ! -f "${VENV_DIR}/bin/activate" ]; then
        echo "ERROR: venv not found at ${VENV_DIR}."
        echo "Run: uv sync --frozen --all-groups --python ${PYTHON_VERSION}"
        exit 1
    fi
    # shellcheck disable=SC1090
    source "${VENV_DIR}/bin/activate"
}

require_yosys() {
    if [[ -d "${OSS_CAD_DIR}/bin" ]]; then
        export PATH="${OSS_CAD_DIR}/bin:$PATH"
    fi
    if ! command -v yosys &> /dev/null; then
        echo "ERROR: yosys not found in PATH."
        exit 1
    fi
}

stage_oss_cad_suite() {
    mkdir -p "$TAURI_RESOURCES_DIR"
    if [[ "$ENABLE_OSS_CAD_SUITE" != "true" ]]; then
        mkdir -p "$OSS_CAD_BUNDLE_DIR"
        return 0
    fi

    if [[ ! -d "${OSS_CAD_DIR}" || ! -f "${OSS_CAD_DIR}/bin/yosys" ]]; then
        echo "ERROR: OSS CAD Suite not found at ${OSS_CAD_DIR}."
        exit 1
    fi

    rm -rf "$OSS_CAD_BUNDLE_DIR"
    mkdir -p "$OSS_CAD_BUNDLE_DIR"

    local yosys_bin_src="$OSS_CAD_DIR/bin/yosys"
    if [[ "$TARGET" == *"windows"* ]]; then
        yosys_bin_src="$OSS_CAD_DIR/bin/yosys.exe"
    fi

    if [ ! -f "$yosys_bin_src" ]; then
        echo "ERROR: yosys binary not found at $yosys_bin_src"
        exit 1
    fi

    local slang_src
    slang_src=$(ls "$OSS_CAD_DIR/share/yosys/plugins"/slang.* 2>/dev/null | head -1)
    if [ -z "$slang_src" ]; then
        echo "ERROR: slang plugin not found under $OSS_CAD_DIR/share/yosys/plugins"
        exit 1
    fi

    cp -a "$OSS_CAD_DIR/." "$OSS_CAD_BUNDLE_DIR/"
    if [ -d "$OSS_CAD_BUNDLE_DIR/bin" ]; then
        find "$OSS_CAD_BUNDLE_DIR/bin" -maxdepth 1 -type f ! -name 'yosys' ! -name 'yosys*' ! -name 'abc' -print0 | xargs -0 -r rm -f
    fi
    if [ -d "$OSS_CAD_BUNDLE_DIR/share" ]; then
        find "$OSS_CAD_BUNDLE_DIR/share" -mindepth 1 -maxdepth 1 -print0 | \
            xargs -0 -r -I {} bash -c 'if [ "$(basename "{}")" != "yosys" ]; then rm -rf "{}"; fi'
    fi
    if [ -d "$OSS_CAD_BUNDLE_DIR/share/yosys" ]; then
        find "$OSS_CAD_BUNDLE_DIR/share/yosys" -mindepth 1 -maxdepth 1 -print0 | \
            xargs -0 -r -I {} bash -c 'name=$(basename "{}"); case "$name" in yosys*|plugins|techlibs|scripts) ;; *) rm -rf "{}" ;; esac'
    fi
    chmod +x "$OSS_CAD_BUNDLE_DIR/bin/$(basename "$yosys_bin_src")"
}

build_api_server() {
    cd "$PROJECT_ROOT"
    rm -rf build dist __pycache__
    PYINSTALLER_ONEFILE=1 pyinstaller chipcompiler.spec --clean --noconfirm

    local source_binary="dist/chipcompiler"
    if [[ "$TARGET" == *"windows"* ]]; then
        source_binary="${source_binary}.exe"
    fi
    if [ ! -f "$source_binary" ]; then
        echo "ERROR: PyInstaller build failed"
        exit 1
    fi

    mkdir -p "$BINARIES_DIR"
    local binary_name="api-server-$TARGET"
    if [[ "$TARGET" == *"windows"* ]]; then
        binary_name="$binary_name.exe"
    fi
    cp "$source_binary" "$BINARIES_DIR/$binary_name"
    chmod +x "$BINARIES_DIR/$binary_name"

    echo "$binary_name"
}

main() {
    setup_project_vars
    ENABLE_OSS_CAD_SUITE="${ENABLE_OSS_CAD_SUITE:-true}"
    TARGET=$(get_target_platform)

    log "CI build target: $TARGET"
    log "Activating venv"
    require_venv
    log "Checking yosys"
    require_yosys
    log "Staging OSS CAD Suite"
    stage_oss_cad_suite

    if [[ ! -d "${ECC_TOOLS_ROOT}" ]]; then
        echo "ERROR: ecc-tools submodule not found."
        exit 1
    fi
    log "Building ecc_py"
    build_ecc_py

    log "Building API server"
    local binary_name
    binary_name=$(build_api_server)

    log "Building Tauri app"
    build_tauri_bundle "$GUI_DIR" "$TAURI_DIR" "$OSS_CAD_BUNDLE_DIR" "$BINARIES_DIR" "$binary_name" || exit 1
}

main "$@"
