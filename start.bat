@echo off
chcp 65001 > nul
title AstralLounge

echo.
echo  ██████╗ ███████╗██╗   ██╗    ██╗     ██╗██╗  ██╗██╗   ██╗
echo  ██╔══██╗██╔════╝██║   ██║    ██║     ██║██║ ██╔╝╚██╗ ██╔╝
echo  ██║  ██║█████╗  ██║   ██║    ██║     ██║█████╔╝  ╚████╔╝
echo  ██║  ██║██╔══╝  ╚██╗ ██╔╝    ██║     ██║██╔═██╗   ╚██╔╝
echo  ██████╔╝███████╗ ╚████╔╝     ███████╗██║██║  ██╗   ██║
echo  ╚═════╝ ╚══════╝  ╚═══╝      ╚══════╝╚═╝╚═╝  ╚═╝   ╚═╝
echo.
echo  本地 AI 对话平台
echo.

REM 检查 Python
python --version > nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.9+
    pause
    exit /b 1
)

REM 创建数据目录
if not exist "data" mkdir data
if not exist "data\characters" mkdir data\characters
if not exist "data\world_info" mkdir data\world_info
if not exist "data\logs" mkdir data\logs

REM 检查依赖
echo [1/2] 检查后端依赖...
pip show fastapi > nul 2>&1
if errorlevel 1 (
    echo [安装] 正在安装后端依赖...
    pip install -r backend/requirements.txt -q
)

REM 检查前端 node_modules
echo [2/2] 检查前端依赖...
if not exist "frontend\node_modules" (
    echo [安装] 正在安装前端依赖...
    cd frontend
    call npm install
    cd ..
)

echo.
echo ========================================
echo  启动中...
echo ========================================
echo.

REM 启动后端（后台）
start /B python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 > backend.log 2>&1

REM 等待后端启动
timeout /t 3 /nobreak > nul

REM 检查后端是否启动成功
curl -s http://localhost:8000/api/health > nul 2>&1
if errorlevel 1 (
    echo [警告] 后端可能未启动成功，请检查 backend.log
)

REM 启动前端
cd frontend
start /B npm run dev
cd ..

echo.
echo ========================================
echo  已启动！
echo  - 后端: http://localhost:8000
echo  - 前端: http://localhost:3000
echo ========================================
echo.
echo 按任意键退出...
pause > nul
