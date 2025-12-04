@echo off
set "PROJECT_ROOT=E:\projectcode\ppt2html"
set "PROJECT_Deploy_Dir=E:\projectcode\ppt2html\deploy"
set "BUILD_DIR=%PROJECT_Deploy_Dir%\build_ready"
set "BUILD_BACKEND_DIR=%PROJECT_Deploy_Dir%\build_ready\backend"

set "API_CODE_DIR=%PROJECT_ROOT%\api"

mkdir %BUILD_BACKEND_DIR%
robocopy "%API_CODE_DIR%" "%BUILD_BACKEND_DIR%" /E
if %errorlevel% gtr 8 (
    echo [Backend API Preparation] Error: Failed to copy sourcecode to deploy directory
    exit /b 1
)
echo Python copied successfully

call %BUILD_DIR%\python-embed\python.exe -m pip install --only-binary=:all: -r %BUILD_DIR%\backend\requirements.txt --target %BUILD_DIR%\site-packages