@echo off
chcp 65001 > nul
echo ===================================
echo   QSerial - Build (wxPython版本)
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
python3 -c "import wx" 2>nul
if errorlevel 1 (
    echo [ERROR] wxPython未安装，请先安装: pip3 install wxPython
    pause
    exit /b 1
)
echo.

echo [4/7] 清理旧的构建文件...
if exist build rmdir /s /q build
if exist dist\QSerial.exe del dist\QSerial.exe
echo.

echo [5/7] 打包应用程序...
python3 -m PyInstaller --onefile --windowed ^
  --name QSerial ^
  --icon icon.ico ^
  --add-data "version.py;." ^
  --add-data "icon.png;." ^
  --add-data "themes;themes" ^
  --paths src ^
  --hidden-import wx ^
  --hidden-import wx.stc ^
  --hidden-import wx.lib.agw.aui ^
  --hidden-import wx.lib.agw.flatnotebook ^
  --hidden-import wx.lib.agw.flatmenu ^
  --hidden-import wx.lib.agw.artmanager ^
  --hidden-import wx.lib.buttons ^
  --hidden-import components ^
  --hidden-import pages ^
  --hidden-import utils ^
  src/main/app_wx.py

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

REM 复制config.json示例
if exist config.json (
    copy config.json dist\config.json >nul 2>&1
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
    if exist config.json (
        powershell -Command "Compress-Archive -Path QSerial.exe,themes,config.json -DestinationPath QSerial_v%VERSION%.zip -Force"
        echo [INFO] 压缩包包含: QSerial.exe + themes目录 + config.json
    ) else (
        powershell -Command "Compress-Archive -Path QSerial.exe,themes -DestinationPath QSerial_v%VERSION%.zip -Force"
        echo [INFO] 压缩包包含: QSerial.exe + themes目录
    )
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
echo [提示] wxPython版本性能更好，支持大文本框
echo.
pause

