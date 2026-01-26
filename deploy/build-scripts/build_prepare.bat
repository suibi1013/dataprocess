@echo off
rem ================================================
rem Build Preparation Script
rem ================================================
set "PROJECT_ROOT=E:\projectcode\dataprocess"
set "PROJECT_Deploy_Dir=%PROJECT_ROOT%\deploy"
set "SOURCEFILES_DIR=%PROJECT_Deploy_Dir%\sourcefiles"
set "BUILD_READY_DIR=%PROJECT_Deploy_Dir%\build_ready"

rem Don't clear build_ready directory, keep existing files
rem rmdir /s /q %BUILD_READY_DIR%
rem if %errorlevel% neq 0 (
rem     echo Error: build-ready not found.
rem )

rem delete build_ready/electron-dist-final directory
rmdir /s /q %BUILD_READY_DIR%\electron-dist-final
if %errorlevel% neq 0 (
    echo Error: build-ready/electron-dist-final not found. 
)

rem Ensure build_ready directory exists, create if it doesn't
if not exist "%BUILD_READY_DIR%" (
    rem Create build-ready directory if it doesn't exist
    mkdir %BUILD_READY_DIR%
)

rem Copy Python
echo Copying Python...
robocopy %SOURCEFILES_DIR%\python-3.13.0-embed-amd64 %BUILD_READY_DIR%\python-embed /E

rem Copy get-pip.py
copy %SOURCEFILES_DIR%\get-pip.py %BUILD_READY_DIR%\python-embed
call %BUILD_READY_DIR%\python-embed\python.exe %BUILD_READY_DIR%\python-embed\get-pip.py --target %BUILD_READY_DIR%\site-packages
call %BUILD_READY_DIR%\python-embed\python.exe -m pip --version

echo build prepare successfully