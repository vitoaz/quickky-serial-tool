@echo off
chcp 65001 >nul
title QSerial - PySide6 Qt版本
echo ===================================
echo   QSerial 串口调试工具
echo   PySide6 / Qt版本 - 开发运行
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
python3 -c "import serial, PySide6" 2>nul
if errorlevel 1 (
    echo 警告: 缺少必要的依赖库
    echo 正在安装依赖...
    pip3 install -r requirements.txt
    if errorlevel 1 (
        echo 错误: 依赖安装失败
        pause
        exit /b 1
    )
)
echo.

echo [3/3] 启动应用程序...
python3 src/main/app_qt.py

echo.
echo 程序已退出
