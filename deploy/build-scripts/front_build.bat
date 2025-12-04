@echo off

rem Calculate project root directory from script path instead of using hardcoded path
set "PROJECT_ROOT=E:\projectcode\ppt2html"
set "PROJECT_Deploy_Dir=E:\projectcode\ppt2html\deploy"
set "BUILD_FRONT_DIR=%PROJECT_Deploy_Dir%\build_ready\front"

set "VUE_DIR=%PROJECT_ROOT%\vue"
set "VUE_DIST_DIR=%VUE_DIR%\dist"

cd /d "%VUE_DIR%"

rem Install dependencies
call npm install --legacy-peer-deps
if %errorlevel% neq 0 (
    echo [Frontend Build] Error: Dependency installation failed
    exit /b 1
)

rem Build frontend project
call npm run build
if %errorlevel% neq 0 (
    echo [Frontend Build] Error: Frontend build failed
    exit /b 1
)

rem Create deploy directory if it doesn't exist
mkdir "%BUILD_FRONT_DIR%" 2>nul

rem Copy build results to deploy directory
robocopy "%VUE_DIST_DIR%" "%BUILD_FRONT_DIR%" /E
if %errorlevel% gtr 8 (
    echo [Frontend Build] Error: Failed to copy build results
    exit /b 1
)

cd /d "%PROJECT_Deploy_Dir%"
echo [Frontend Build] Build results copied successfully