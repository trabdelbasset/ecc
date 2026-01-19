#!/bin/bash

# ECC GUI 安装构建脚本
# 支持平台: Linux (Ubuntu/Debian)

set -e  # 遇到错误时退出

echo "====================================="
echo "ECC GUI 安装构建脚本"
echo "====================================="

# 1. 检查并安装 Node.js
echo "\n1. 检查 Node.js 环境..."
if ! command -v node &> /dev/null; then
    echo "Node.js 未安装，正在安装..."
    curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
    sudo apt-get install -y nodejs
else
    echo "Node.js 已安装: $(node --version)"
fi

# 2. 检查并安装 pnpm
echo "\n2. 检查 pnpm 环境..."
if ! command -v pnpm &> /dev/null; then
    echo "pnpm 未安装，正在安装..."
    npm install -g pnpm
else
    echo "pnpm 已安装: $(pnpm --version)"
fi

# 3. 检查并安装 Rust
echo "\n3. 检查 Rust 环境..."
if ! command -v rustc &> /dev/null; then
    echo "Rust 未安装，正在安装..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    # 添加 Rust 环境变量
    source "$HOME/.cargo/env"
else
    echo "Rust 已安装: $(rustc --version)"
fi

# 4. 安装系统依赖（Linux）
echo "\n4. 安装系统依赖..."
sudo apt update
sudo apt install -y build-essential libwebkit2gtk-4.1-dev libssl-dev libgtk-3-dev libayatana-appindicator3-dev librsvg2-dev patchelf libsoup-3.0-dev libjavascriptcoregtk-4.1-dev curl wget file

echo "\n5. 进入 GUI 目录并安装项目依赖..."
cd "$(dirname "$0")/chipcompiler/gui"

# 6. 安装项目依赖
echo "正在安装项目依赖..."
pnpm install

echo "\n6. 构建 GUI 项目..."
# 确保加载 Rust 环境变量
source "$HOME/.cargo/env"
# 执行构建命令
pnpm run tauri:build

echo "\n====================================="
echo "ECC GUI 构建完成！"
echo "====================================="
echo "构建产物目录: $PWD/src-tauri/target/release/"
echo "可执行文件: $PWD/src-tauri/target/release/ecc-client"
echo "打包文件位于: $PWD/src-tauri/target/release/bundle/"

# 显示生成的包文件列表
echo -e "\n生成的安装包:"
find "$PWD/src-tauri/target/release/bundle" -type f -name "*.deb" -o -name "*.rpm" -o -name "*.AppImage" | sort

# change listener ip
# /usr/bin/vncserver -kill :2 && sleep 2 && /usr/bin/vncserver -depth 24 -geometry 1920x1080 -localhost no :2