@echo off
rem ================================================
rem Build Preparation Script
rem ================================================
set "PROJECT_ROOT=E:\projectcode\dataprocess"
set "PROJECT_Deploy_Dir=%PROJECT_ROOT%\deploy"
set "SOURCEFILES_DIR=%PROJECT_Deploy_Dir%\sourcefiles"
set "BUILD_READY_DIR=%PROJECT_Deploy_Dir%\build_ready"

rmdir /s /q %BUILD_READY_DIR%
if %errorlevel% neq 0 (
    echo Error: build-ready not found. Please install build-ready and ensure it's in PATH.
)

rem Create build-ready directory
mkdir %BUILD_READY_DIR%

rem Copy Python
echo Copying Python...
robocopy %SOURCEFILES_DIR%\python-3.13.0-embed-amd64 %BUILD_READY_DIR%\python-embed /E

rem Copy get-pip.py
copy %SOURCEFILES_DIR%\get-pip.py %BUILD_READY_DIR%\python-embed
call %BUILD_READY_DIR%\python-embed\python.exe %BUILD_READY_DIR%\python-embed\get-pip.py --target %BUILD_READY_DIR%\site-packages
call %BUILD_READY_DIR%\python-embed\python.exe -m pip --version

echo build prepare successfully
