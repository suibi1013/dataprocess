@echo off

rem ================================================
rem dataprocess Project Electron Packaging Script
rem ================================================
set "PROJECT_ROOT=E:\projectcode\dataprocess"
set "PROJECT_Deploy_Dir=%PROJECT_ROOT%\deploy"
set "SOURCEFILES_DIR=%PROJECT_Deploy_Dir%\sourcefiles"
set "BUILD_READY_DIR=%PROJECT_Deploy_Dir%\build_ready"

rem Copy files,main.js,preload.js,package.json
copy %SOURCEFILES_DIR%\main.js %BUILD_READY_DIR%
copy %SOURCEFILES_DIR%\preload.js %BUILD_READY_DIR%
copy %SOURCEFILES_DIR%\package.json %BUILD_READY_DIR%
rem Copy icon-resources
robocopy %SOURCEFILES_DIR%\icon-resources %BUILD_READY_DIR%\icon-resources /E

cd /d "%BUILD_READY_DIR%"

rem 检查electron-builder是否已经安装，避免每次重新安装
if not exist "node_modules/electron-builder" (
    echo [Electron Packaging] Installing electron-builder...
    call npm install electron-builder --save-dev --no-package-lock
    if %errorlevel% neq 0 (
        echo [Electron Packaging] Error: Failed to install electron-builder
        exit /b 1
    )
) else (
    echo [Electron Packaging] electron-builder already installed, skipping...
)

rem 执行electron-builder，只构建Windows平台
call npx electron-builder --win --x64
if %errorlevel% neq 0 (
    echo [Electron Packaging] Error: Electron packaging failed
    exit /b 1
)