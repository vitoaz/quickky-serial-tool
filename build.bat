@echo off
chcp 65001 > nul
setlocal
echo ===================================
echo   QSerial - Build (PySide6 / Qt)
echo ===================================

python3 scripts/generate_version.py
if errorlevel 1 goto :error

python3 -c "import PyInstaller" 2>nul
if errorlevel 1 pip3 install PyInstaller
python3 -c "import PySide6" 2>nul
if errorlevel 1 pip3 install "PySide6>=6.8,<7"
python3 -c "import serial" 2>nul
if errorlevel 1 pip3 install "pyserial>=3.5"

if exist build rmdir /s /q build
if exist dist\QSerial.exe del dist\QSerial.exe

python3 -m PyInstaller --noconfirm --clean --onefile --windowed ^
  --name QSerial --icon icon.ico ^
  --add-data "version.py;." --add-data "icon.png;." --add-data "themes;themes" ^
  --paths src ^
  --additional-hooks-dir scripts\pyinstaller_hooks ^
  --exclude-module PySide6.Qt3DAnimation ^
  --exclude-module PySide6.Qt3DCore ^
  --exclude-module PySide6.Qt3DExtras ^
  --exclude-module PySide6.Qt3DInput ^
  --exclude-module PySide6.Qt3DLogic ^
  --exclude-module PySide6.Qt3DRender ^
  --exclude-module PySide6.QtAxContainer ^
  --exclude-module PySide6.QtBluetooth ^
  --exclude-module PySide6.QtCharts ^
  --exclude-module PySide6.QtDataVisualization ^
  --exclude-module PySide6.QtDesigner ^
  --exclude-module PySide6.QtGraphs ^
  --exclude-module PySide6.QtHelp ^
  --exclude-module PySide6.QtHttpServer ^
  --exclude-module PySide6.QtLocation ^
  --exclude-module PySide6.QtMultimedia ^
  --exclude-module PySide6.QtMultimediaWidgets ^
  --exclude-module PySide6.QtNetwork ^
  --exclude-module PySide6.QtNetworkAuth ^
  --exclude-module PySide6.QtNfc ^
  --exclude-module PySide6.QtOpenGL ^
  --exclude-module PySide6.QtOpenGLWidgets ^
  --exclude-module PySide6.QtPdf ^
  --exclude-module PySide6.QtPdfWidgets ^
  --exclude-module PySide6.QtPositioning ^
  --exclude-module PySide6.QtQuick ^
  --exclude-module PySide6.QtQuick3D ^
  --exclude-module PySide6.QtQuickControls2 ^
  --exclude-module PySide6.QtQuickWidgets ^
  --exclude-module PySide6.QtQml ^
  --exclude-module PySide6.QtRemoteObjects ^
  --exclude-module PySide6.QtScxml ^
  --exclude-module PySide6.QtSensors ^
  --exclude-module PySide6.QtSerialBus ^
  --exclude-module PySide6.QtSerialPort ^
  --exclude-module PySide6.QtSpatialAudio ^
  --exclude-module PySide6.QtSql ^
  --exclude-module PySide6.QtStateMachine ^
  --exclude-module PySide6.QtSvg ^
  --exclude-module PySide6.QtSvgWidgets ^
  --exclude-module PySide6.QtTextToSpeech ^
  --exclude-module PySide6.QtUiTools ^
  --exclude-module PySide6.QtVirtualKeyboard ^
  --exclude-module PySide6.QtWebChannel ^
  --exclude-module PySide6.QtWebEngineCore ^
  --exclude-module PySide6.QtWebEngineQuick ^
  --exclude-module PySide6.QtWebEngineWidgets ^
  --exclude-module PySide6.QtWebSockets ^
  --exclude-module PySide6.QtWebView ^
  --exclude-module PySide6.QtXml ^
  --exclude-module PySide6.QtXmlPatterns ^
  src\main\app_qt.py
if errorlevel 1 goto :error

if exist build rmdir /s /q build
if exist QSerial.spec del QSerial.spec
if not exist dist\licenses mkdir dist\licenses
copy LICENSE dist\LICENSE >nul
copy licenses\THIRD_PARTY_NOTICES.md dist\licenses\THIRD_PARTY_NOTICES.md >nul
python3 scripts\collect_qt_licenses.py dist\licenses
if errorlevel 1 goto :error
echo 构建完成：dist\QSerial.exe
exit /b 0

:error
echo [ERROR] Qt 构建失败
exit /b 1
