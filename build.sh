#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Source common functions
source "${SCRIPT_DIR}/scripts/common.sh"

# Initialize project variables
setup_project_vars

# Setup Python environment
setup_uv_env || exit 1

# Setup OSS CAD Suite (if enabled)
setup_oss_cad_suite
append_oss_cad_to_venv

# Initialize submodules and PDK
setup_submodules
setup_ics55_pdk

# Build and install ecc_py
build_ecc_py || exit 1
install_ecc_py

echo ""
echo "Environment setup completed successfully!"
echo "To activate the virtual environment in future sessions, run:"
echo "source ${VENV_DIR}/bin/activate"

if [ "$1" == "--release" ]; then
    echo "Starting executable build process..."
    export PYINSTALLER_ONEFILE=1
    rm -rf build/ dist/
    uv run pyinstaller chipcompiler.spec
fi