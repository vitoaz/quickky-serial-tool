@echo off
chcp 65001 > nul
echo ===================================
echo   QSerial - Build
echo ===================================
echo.

echo [1/7] 生成版本文件...
python3 scripts/generate_version.py
if errorlevel 1 (
    echo [ERROR] 版本文件生成失败
    pause
    exit /b 1
)
echo.

echo [2/7] 生成图标文件...
python3 -c "from PIL import Image; img = Image.open('icon.png').convert('RGBA'); img.save('icon.ico', format='ICO', sizes=[(256, 256)])" 2>nul
if errorlevel 1 (
    echo [INFO] Pillow not installed, installing...
    pip3 install Pillow
    python3 -c "from PIL import Image; img = Image.open('icon.png').convert('RGBA'); img.save('icon.ico', format='ICO', sizes=[(256, 256)])"
)
echo.

echo [3/7] 检查依赖...
python3 -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [INFO] 正在安装PyInstaller...
    pip3 install PyInstaller
)
echo.

echo [4/7] 清理旧的构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo.

echo [5/7] 打包应用程序...
python3 -m PyInstaller --onefile --windowed ^
  --name QSerial ^
  --icon icon.ico ^
  --add-data "version.py;." ^
  --add-data "icon.png;." ^
  --paths src ^
  --hidden-import pages.work_tab ^
  --hidden-import components.serial_settings_panel ^
  --hidden-import components.receive_settings_panel ^
  --hidden-import components.send_settings_panel ^
  --hidden-import components.quick_commands_panel ^
  --hidden-import components.send_history_panel ^
  --hidden-import utils.config_manager ^
  --hidden-import utils.serial_manager ^
  --hidden-import utils.theme_manager ^
  src/main/app.py

if errorlevel 1 (
    echo [ERROR] 打包失败
    pause
    exit /b 1
)
echo.

echo [6/7] 清理临时文件和复制资源...
if exist build rmdir /s /q build
if exist QSerial.spec del QSerial.spec

REM 确保themes目录在dist下有独立拷贝
if exist themes (
    if exist dist (
        echo [INFO] 拷贝themes目录到dist...
        xcopy themes dist\themes\ /E /I /Y >nul 2>&1
        echo [INFO] themes目录已拷贝到dist
    )
) else (
    echo [WARNING] themes目录不存在
)
echo.

echo [7/7] 生成发布包...
REM 读取版本号
for /f "tokens=3 delims= " %%a in ('findstr /C:"VERSION = " version.py') do set VERSION=%%a
set VERSION=%VERSION:"=%
echo [INFO] Version: %VERSION%

REM 创建压缩包（包含exe和themes目录）
cd dist
if exist QSerial_v%VERSION%.zip del QSerial_v%VERSION%.zip
if exist themes (
    powershell -Command "Compress-Archive -Path QSerial.exe,themes -DestinationPath QSerial_v%VERSION%.zip -Force"
    echo [INFO] 压缩包包含: QSerial.exe + themes目录
) else (
    powershell -Command "Compress-Archive -Path QSerial.exe -DestinationPath QSerial_v%VERSION%.zip -Force"
    echo [INFO] 压缩包包含: QSerial.exe（themes已内嵌）
)
cd ..
echo.

echo ===================================
echo   Build completed!
echo   EXE: dist\QSerial.exe
echo   ZIP: dist\QSerial_v%VERSION%.zip
echo ===================================
echo.
