@echo off
chcp 65001 > nul
echo ===================================
echo   Quickky Serial Tool - Build
echo ===================================
echo.

echo [1/5] 生成版本文件...
python3 scripts/generate_version.py
if errorlevel 1 (
    echo 错误: 版本文件生成失败
    pause
    exit /b 1
)
echo.

echo [2/5] 检查依赖...
python3 -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo 正在安装PyInstaller...
    pip3 install PyInstaller
)
echo.

echo [3/5] 清理旧的构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo.

echo [4/5] 打包应用程序...
python3 -m PyInstaller --onefile --windowed ^
  --name QuickkySerialTool ^
  --add-data "version.py;." ^
  src/main/app.py

if errorlevel 1 (
    echo 错误: 打包失败
    pause
    exit /b 1
)
echo.

echo [5/5] 清理临时文件...
if exist build rmdir /s /q build
if exist QuickkySerialTool.spec del QuickkySerialTool.spec
echo.

echo ===================================
echo   构建完成！
echo   可执行文件位置: dist\QuickkySerialTool.exe
echo ===================================
echo.
pause

