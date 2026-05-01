#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${ROOT_DIR}/build/appimage"
DIST_DIR="${ROOT_DIR}/dist"
APP_NAME="D3keyHelper-Linux"
APPDIR="${BUILD_DIR}/AppDir"
PYTHON_BIN="${PYTHON_BIN:-python}"
USER_CONFIG_PATH="${DIST_DIR}/${APP_NAME}/d3oldsand.ini"
USER_CONFIG_BACKUP="${BUILD_DIR}/preserved-d3oldsand.ini"

mkdir -p "${BUILD_DIR}"
if [[ -f "${USER_CONFIG_PATH}" ]]; then
  cp "${USER_CONFIG_PATH}" "${USER_CONFIG_BACKUP}"
else
  rm -f "${USER_CONFIG_BACKUP}"
fi
rm -rf "${APPDIR}" "${DIST_DIR}/${APP_NAME}" "${ROOT_DIR}/build/${APP_NAME}.spec"

if ! "${PYTHON_BIN}" -m pip --version >/dev/null 2>&1; then
  "${PYTHON_BIN}" -m ensurepip --upgrade >/dev/null 2>&1 || true
fi
if ! "${PYTHON_BIN}" -m pip --version >/dev/null 2>&1; then
  echo "Error: ${PYTHON_BIN} does not provide pip. Set PYTHON_BIN to a Python interpreter with pip." >&2
  exit 1
fi

"${PYTHON_BIN}" -m pip install --upgrade pyinstaller

"${PYTHON_BIN}" -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --onedir \
  --specpath "${ROOT_DIR}/build" \
  --workpath "${ROOT_DIR}/build" \
  --distpath "${DIST_DIR}" \
  --name "${APP_NAME}" \
  --hidden-import PySide6.QtDBus \
  --collect-submodules PySide6 \
  --add-data "${ROOT_DIR}/mainwindow.png:." \
  "${ROOT_DIR}/d3keyhelper_linux_gui.py"

mkdir -p "${APPDIR}/usr/lib/d3keyhelper-linux"
mkdir -p "${APPDIR}/usr/share/applications"
mkdir -p "${APPDIR}/usr/share/metainfo"
cp -a "${DIST_DIR}/${APP_NAME}/." "${APPDIR}/usr/lib/d3keyhelper-linux/"
cp "${ROOT_DIR}/packaging/AppRun" "${APPDIR}/AppRun"
cp "${ROOT_DIR}/packaging/D3keyHelper.desktop" "${APPDIR}/io.github.WeijieH.D3keyHelper.desktop"
cp "${ROOT_DIR}/packaging/D3keyHelper.desktop" "${APPDIR}/usr/share/applications/io.github.WeijieH.D3keyHelper.desktop"
cp "${ROOT_DIR}/packaging/D3keyHelper.appdata.xml" "${APPDIR}/usr/share/metainfo/io.github.WeijieH.D3keyHelper.appdata.xml"
cp "${ROOT_DIR}/mainwindow.png" "${APPDIR}/d3keyhelper-linux.png"
chmod +x "${APPDIR}/AppRun"

APPIMAGETOOL="${BUILD_DIR}/appimagetool-x86_64.AppImage"
if [[ ! -x "${APPIMAGETOOL}" ]]; then
  curl -L \
    "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage" \
    -o "${APPIMAGETOOL}"
  chmod +x "${APPIMAGETOOL}"
fi

QT_QPA_PLATFORM=offscreen ARCH=x86_64 "${APPIMAGETOOL}" --appimage-extract-and-run "${APPDIR}" "${BUILD_DIR}/${APP_NAME}-x86_64.AppImage"

if [[ -f "${USER_CONFIG_BACKUP}" ]]; then
  cp "${USER_CONFIG_BACKUP}" "${USER_CONFIG_PATH}"
fi

echo "Built AppImage at ${BUILD_DIR}/${APP_NAME}-x86_64.AppImage"
