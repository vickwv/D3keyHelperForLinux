#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${ROOT_DIR}/build/appimage"
DIST_DIR="${ROOT_DIR}/dist"
APP_NAME="D3keyHelper-Linux"
APPDIR="${BUILD_DIR}/AppDir"
PYTHON_BIN="${PYTHON_BIN:-python}"

mkdir -p "${BUILD_DIR}"
rm -rf "${APPDIR}" "${DIST_DIR}/${APP_NAME}" "${ROOT_DIR}/build/${APP_NAME}.spec"

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

echo "Built AppImage at ${BUILD_DIR}/${APP_NAME}-x86_64.AppImage"
