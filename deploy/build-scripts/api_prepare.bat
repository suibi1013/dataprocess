@echo off
set "PROJECT_ROOT=E:\projectcode\dataprocess"
set "PROJECT_Deploy_Dir=%PROJECT_ROOT%\deploy"
set "BUILD_DIR=%PROJECT_Deploy_Dir%\build_ready"
set "BUILD_BACKEND_DIR=%PROJECT_Deploy_Dir%\build_ready\backend"

set "API_CODE_DIR=%PROJECT_ROOT%\api"

rem first delete backend directory
if exist "%BUILD_BACKEND_DIR%" (
    rd /s /q "%BUILD_BACKEND_DIR%"
)

rem create backend directory again
mkdir %BUILD_BACKEND_DIR%

rem copy api code to backend directory
robocopy "%API_CODE_DIR%" "%BUILD_BACKEND_DIR%" /E
if %errorlevel% gtr 8 (
    echo [Backend API Preparation] Error: Failed to copy sourcecode to deploy directory
    exit /b 1
)
echo Python copied successfully

rem backup instruction data to JSON file
echo [Backend API Preparation] Backing up instruction data...
call %BUILD_DIR%\python-embed\python.exe %BUILD_DIR%\backend\build\backup_instruction_data.py
if %errorlevel% neq 0 (
    echo [Backend API Preparation] Warning: Failed to backup instruction data, continuing with build
)
echo [Backend API Preparation] Instruction data backup completed

call %BUILD_DIR%\python-embed\python.exe -m pip install --only-binary=:all: -r %BUILD_DIR%\backend\requirements.txt --target %BUILD_DIR%\site-packages