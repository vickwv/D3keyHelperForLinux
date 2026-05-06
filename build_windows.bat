@echo off
setlocal

set PYTHON_BIN=python
set APP_NAME=D3Macro-Windows
set ROOT_DIR=%~dp0

echo === D3Macro Windows Build ===

%PYTHON_BIN% -m pip install --upgrade pip
%PYTHON_BIN% -m pip install -r "%ROOT_DIR%requirements.txt"
%PYTHON_BIN% -m pip install pyinstaller

%PYTHON_BIN% -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --windowed ^
  --onefile ^
  --name "%APP_NAME%" ^
  --hidden-import pynput.keyboard._win32 ^
  --hidden-import pynput.mouse._win32 ^
  --collect-submodules mss ^
  --collect-submodules pynput ^
  --add-data "%ROOT_DIR%mainwindow.png;." ^
  "%ROOT_DIR%d3keyhelper_gui.py"

echo.
echo === Build complete: dist\%APP_NAME%.exe ===
endlocal
