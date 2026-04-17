#!/bin/bash

# AstralLounge 启动脚本

echo ""
echo "  ██████╗ ███████╗██╗   ██╗    ██╗     ██╗██╗  ██╗██╗   ██╗"
echo "  ██╔══██╗██╔════╝██║   ██║    ██║     ██║██║ ██╔╝╚██╗ ██╔╝"
echo "  ██║  ██║█████╗  ██║   ██║    ██║     ██║█████╔╝  ╚████╔╝"
echo "  ██║  ██║██╔══╝  ╚██╗ ██╔╝    ██║     ██║██╔═██╗   ╚██╔╝"
echo "  ██████╔╝███████╗ ╚████╔╝     ███████╗██║██║  ██╗   ██║"
echo "  ╚═════╝ ╚══════╝  ╚═══╝      ╚══════╝╚═╝╚═╝  ╚═╝   ╚═╝"
echo ""
echo "  本地 AI 对话平台"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到 Python，请先安装 Python 3.9+"
    exit 1
fi

# 创建数据目录
mkdir -p data/characters data/world_info data/logs

# 检查并安装后端依赖
echo "[1/2] 检查后端依赖..."
if ! python3 -c "import fastapi" &> /dev/null; then
    echo "[安装] 正在安装后端依赖..."
    pip3 install -r backend/requirements.txt -q
fi

# 检查前端 node_modules
echo "[2/2] 检查前端依赖..."
if [ ! -d "frontend/node_modules" ]; then
    echo "[安装] 正在安装前端依赖..."
    cd frontend && npm install && cd ..
fi

echo ""
echo "========================================"
echo "  启动中..."
echo "========================================"
echo ""

# 启动后端
echo "[后端] 启动服务在 http://localhost:8000"
python3 -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 等待后端启动
sleep 3

# 启动前端
echo "[前端] 启动开发服务器在 http://localhost:3000"
cd frontend && npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "========================================"
echo "  已启动！"
echo "  - 后端: http://localhost:8000"
echo "  - 前端: http://localhost:3000"
echo "========================================"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待退出信号
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo '已停止'; exit" SIGINT SIGTERM
wait
