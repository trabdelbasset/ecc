#!/bin/bash

# 设置项目根目录
PROJECT_ROOT=$(cd "$(dirname "$0")";pwd)
VENV_DIR="${PROJECT_ROOT}/.venv"
PYTHON_VERSION="3.10"

# 检查Python 3.10是否可用
if ! command -v python${PYTHON_VERSION} &> /dev/null; then
    echo "Error: Python ${PYTHON_VERSION} is not installed or not in PATH"
    exit 1
fi

# 创建虚拟环境（如果不存在）
if [ ! -d "${VENV_DIR}" ]; then
    echo "Creating Python ${PYTHON_VERSION} virtual environment at ${VENV_DIR}..."
    python${PYTHON_VERSION} -m venv "${VENV_DIR}"
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment"
        exit 1
    fi
    echo "Virtual environment created successfully!"
else
    echo "Virtual environment already exists at ${VENV_DIR}"
fi

# 激活虚拟环境
echo "Activating virtual environment..."
source "${VENV_DIR}/bin/activate"

# 升级pip
echo "Upgrading pip..."
pip install --upgrade pip

# 安装项目依赖
echo "Installing project dependencies from pyproject.toml..."
# 使用pyproject.toml安装项目依赖
pip install -e .

# 如果需要安装开发依赖，可以使用下面的命令
# pip install -e ".[dev]"

# 构建ieda_py
echo "Building ieda_py..."

# 创建build目录（如果不存在）
BUILD_DIR="${PROJECT_ROOT}/build"
if [ ! -d "${BUILD_DIR}" ]; then
    echo "Creating build directory at ${BUILD_DIR}..."
    mkdir -p "${BUILD_DIR}"
else
    # 如果构建目录已存在，清理现有的CMake缓存和文件，以便可以使用不同的生成器
    echo "Cleaning existing build files at ${BUILD_DIR}..."
    rm -rf "${BUILD_DIR}/CMakeCache.txt" "${BUILD_DIR}/CMakeFiles" "${BUILD_DIR}/build.ninja" "${BUILD_DIR}/Makefile"
fi

# 进入build目录并运行cmake和make
cd "${BUILD_DIR}" || exit 1

# 配置项目
echo "Configuring project with CMake..."
# 检查是否安装了ninja，如果安装了则使用ninja生成器
if command -v ninja &> /dev/null; then
    echo "Using Ninja generator..."
    cmake -G Ninja -DBUILD_AIEDA=ON ..
else
    echo "Using default generator..."
    cmake -DBUILD_AIEDA=ON ..
fi
if [ $? -ne 0 ]; then
    echo "Error: CMake configuration failed"
    exit 1
fi

# 构建项目
echo "Building project..."
# 检查是否安装了ninja
if command -v ninja &> /dev/null; then
    echo "Using ninja build system..."
    ninja ieda_py
else
    echo "Using make build system..."
    make -j$(nproc) ieda_py  # 使用所有可用的CPU核心构建ieda_py目标
fi
if [ $? -ne 0 ]; then
    echo "Error: Build failed"
    exit 1
fi

echo "ieda_py build completed successfully!"
echo "Environment setup completed successfully!"
echo "To activate the virtual environment in future sessions, run:"
echo "source ${VENV_DIR}/bin/activate"
