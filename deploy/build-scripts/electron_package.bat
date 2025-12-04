@echo off

rem ================================================
rem PPT2HTML Project Electron Packaging Script
rem ================================================
set "PROJECT_Deploy_Dir=E:\projectcode\ppt2html\deploy"
set "SOURCEFILES_DIR=%PROJECT_Deploy_Dir%\sourcefiles"
set "BUILD_READY_DIR=%PROJECT_Deploy_Dir%\build_ready"

rem Copy files,main.js,preload.js,package.json
copy %SOURCEFILES_DIR%\main.js %BUILD_READY_DIR%
copy %SOURCEFILES_DIR%\preload.js %BUILD_READY_DIR%
copy %SOURCEFILES_DIR%\package.json %BUILD_READY_DIR%
rem Copy icon-resources
robocopy %SOURCEFILES_DIR%\icon-resources %BUILD_READY_DIR%\icon-resources /E

cd /d "%BUILD_READY_DIR%"
call npm install electron-builder --save-dev
if %errorlevel% neq 0 (
    echo [Electron Packaging] Error: Failed to install electron-builder
    exit /b 1
)

rem Execute electron-builder
call npx electron-builder
if %errorlevel% neq 0 (
    echo [Electron Packaging] Error: Electron packaging failed
    exit /b 1
)