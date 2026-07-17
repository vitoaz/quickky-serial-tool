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
