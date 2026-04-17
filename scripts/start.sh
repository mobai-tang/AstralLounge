#!/bin/bash
# ========================================
# AstralLounge 快速启动脚本 (Linux/macOS)
# ========================================

set -e

echo "========================================"
echo "  AstralLounge 启动脚本"
echo "========================================"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 需要安装 Python 3.10+"
    exit 1
fi

# 安装后端依赖
echo "[1/3] 安装后端依赖..."
cd backend
pip install -r requirements.txt -q
cd ..

# 检查 Node.js
if command -v npm &> /dev/null; then
    echo "[2/3] 安装前端依赖..."
    cd frontend
    npm install
    cd ..
fi

# 复制环境变量
if [ ! -f .env ]; then
    echo "[3/3] 创建环境变量文件..."
    cp .env.dev .env
    echo "已创建 .env 文件，请根据需要修改"
fi

echo ""
echo "========================================"
echo "  启动完成！"
echo ""
echo "  开发模式启动后端:"
echo "    cd backend && python main.py"
echo ""
echo "  开发模式启动前端:"
echo "    cd frontend && npm run dev"
echo ""
echo "  或者安装 concurrently 后运行:"
echo "    npm run dev:all"
echo "========================================"
