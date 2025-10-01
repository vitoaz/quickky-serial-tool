@echo off
chcp 65001 > nul
echo ===================================
echo   Quickky Serial Tool - Debug Run
echo ===================================
echo.

echo [1/3] 生成版本文件...
python3 scripts/generate_version.py
if errorlevel 1 (
    echo 错误: 版本文件生成失败
    pause
    exit /b 1
)
echo.

echo [2/3] 检查依赖...
python3 -c "import serial, tkinter" 2>nul
if errorlevel 1 (
    echo 警告: 缺少必要的依赖库
    echo 正在安装依赖...
    pip3 install -r requirements.txt
)
echo.

echo [3/3] 启动应用程序...
python3 src/main/app.py

echo.
