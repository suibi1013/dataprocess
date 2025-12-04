@echo off
rem ================================================
rem dataprocess Project Build Automation Script
rem This script runs all build scripts in sequence
rem ================================================

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=E:\projectcode\dataprocess"
set "LOG_FILE=%SCRIPT_DIR%\build_all.log"

echo ================================================
echo dataprocess Project Build Started
echo Start Time: %date% %time%
echo ================================================

rem Clear previous log
del "%LOG_FILE%" 2>nul

echo.>>"%LOG_FILE%"
echo ================================================>>"%LOG_FILE%"
echo dataprocess Project Build Started>>"%LOG_FILE%"
echo Start Time: %date% %time%>>"%LOG_FILE%"
echo ================================================>>"%LOG_FILE%"
echo.>>"%LOG_FILE%"

rem 1. Environment Check
echo [1/5] Running Environment Check...
echo [1/5] Running Environment Check...>>"%LOG_FILE%"
call "%SCRIPT_DIR%\env_check.bat" >>"%LOG_FILE%" 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Environment Check Failed! Check build_all.log for details.
    echo [ERROR] Environment Check Failed!>>"%LOG_FILE%"
    goto BUILD_FAILED
)
echo [1/5] Environment Check Passed!
echo [1/5] Environment Check Passed!>>"%LOG_FILE%"
echo.>>"%LOG_FILE%"

rem 2. Build Preparation
echo [2/5] Running Build Preparation...
echo [2/5] Running Build Preparation...>>"%LOG_FILE%"
call "%SCRIPT_DIR%\build_prepare.bat" >>"%LOG_FILE%" 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Build Preparation Failed! Check build_all.log for details.
    echo [ERROR] Build Preparation Failed!>>"%LOG_FILE%"
    goto BUILD_FAILED
)
echo [2/5] Build Preparation Completed!
echo [2/5] Build Preparation Completed!>>"%LOG_FILE%"
echo.>>"%LOG_FILE%"

rem 3. Frontend Build
echo [3/5] Building Frontend...
echo [3/5] Building Frontend...>>"%LOG_FILE%"
call "%SCRIPT_DIR%\front_build.bat" >>"%LOG_FILE%" 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Frontend Build Failed! Check build_all.log for details.
    echo [ERROR] Frontend Build Failed!>>"%LOG_FILE%"
    goto BUILD_FAILED
)
echo [3/5] Frontend Build Completed!
echo [3/5] Frontend Build Completed!>>"%LOG_FILE%"
echo.>>"%LOG_FILE%"

rem 4. API Preparation
echo [4/5] Preparing Backend API...
echo [4/5] Preparing Backend API...>>"%LOG_FILE%"
call "%SCRIPT_DIR%\api_prepare.bat" >>"%LOG_FILE%" 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] API Preparation Failed! Check build_all.log for details.
    echo [ERROR] API Preparation Failed!>>"%LOG_FILE%"
    goto BUILD_FAILED
)
echo [4/5] API Preparation Completed!
echo [4/5] API Preparation Completed!>>"%LOG_FILE%"
echo.>>"%LOG_FILE%"

rem 5. Electron Packaging
echo [5/5] Packaging Electron Application...
echo [5/5] Packaging Electron Application...>>"%LOG_FILE%"
call "%SCRIPT_DIR%\electron_package.bat" >>"%LOG_FILE%" 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Electron Packaging Failed! Check build_all.log for details.
    echo [ERROR] Electron Packaging Failed!>>"%LOG_FILE%"
    goto BUILD_FAILED
)
echo [5/5] Electron Packaging Completed!
echo [5/5] Electron Packaging Completed!>>"%LOG_FILE%"
echo.>>"%LOG_FILE%"

echo ================================================
echo dataprocess Project Build Successful!
echo End Time: %date% %time%
echo Build log saved to: %LOG_FILE%
echo ================================================

echo.>>"%LOG_FILE%"
echo ================================================>>"%LOG_FILE%"
echo dataprocess Project Build Successful!>>"%LOG_FILE%"
echo End Time: %date% %time%>>"%LOG_FILE%"
echo ================================================>>"%LOG_FILE%"

goto :EOF

:BUILD_FAILED
echo.>>"%LOG_FILE%"
echo ================================================>>"%LOG_FILE%"
echo dataprocess Project Build Failed!>>"%LOG_FILE%"
echo End Time: %date% %time%>>"%LOG_FILE%"
echo ================================================>>"%LOG_FILE%"

echo ================================================
echo dataprocess Project Build Failed!
echo End Time: %date% %time%
echo Check build log for details: %LOG_FILE%
echo ================================================
exit /b 1