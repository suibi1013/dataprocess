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
echo [1/6] Running Environment Check...
echo [1/6] Running Environment Check...>>"%LOG_FILE%"
call :timer_start
call "%SCRIPT_DIR%\env_check.bat" >>"%LOG_FILE%" 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Environment Check Failed! Check build_all.log for details.
    echo [ERROR] Environment Check Failed!>>"%LOG_FILE%"
    goto BUILD_FAILED
)
echo [1/6] Environment Check Passed!>>"%LOG_FILE%"
call :timer_stop
echo.>>"%LOG_FILE%"

rem 2. Version Bump
echo [2/6] Running Version Bump...
echo [2/6] Running Version Bump...>>"%LOG_FILE%"
call :timer_start
rem 进入 sourcefiles 目录执行版本号更新脚本
pushd "%PROJECT_ROOT%\deploy\sourcefiles"
node bump-version.js >>"%LOG_FILE%" 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Version Bump Failed! Check build_all.log for details.
    echo [ERROR] Version Bump Failed!>>"%LOG_FILE%"
    popd
    goto BUILD_FAILED
)
popd
echo [2/6] Version Bump Completed!>>"%LOG_FILE%"
call :timer_stop
echo.>>"%LOG_FILE%"

rem 3. Build Preparation
echo [3/6] Running Build Preparation...
echo [3/6] Running Build Preparation...>>"%LOG_FILE%"
call :timer_start
call "%SCRIPT_DIR%\build_prepare.bat" >>"%LOG_FILE%" 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Build Preparation Failed! Check build_all.log for details.
    echo [ERROR] Build Preparation Failed!>>"%LOG_FILE%"
    goto BUILD_FAILED
)
echo [3/6] Build Preparation Completed!>>"%LOG_FILE%"
call :timer_stop
echo.>>"%LOG_FILE%"

rem 4. Frontend Build
echo [4/6] Building Frontend...
echo [4/6] Building Frontend...>>"%LOG_FILE%"
call :timer_start
call "%SCRIPT_DIR%\front_build.bat" >>"%LOG_FILE%" 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Frontend Build Failed! Check build_all.log for details.
    echo [ERROR] Frontend Build Failed!>>"%LOG_FILE%"
    goto BUILD_FAILED
)
echo [4/6] Frontend Build Completed!>>"%LOG_FILE%"
call :timer_stop
echo.>>"%LOG_FILE%"

rem 5. API Preparation
echo [5/6] Preparing Backend API...
echo [5/6] Preparing Backend API...>>"%LOG_FILE%"
call :timer_start
call "%SCRIPT_DIR%\api_prepare.bat" >>"%LOG_FILE%" 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] API Preparation Failed! Check build_all.log for details.
    echo [ERROR] API Preparation Failed!>>"%LOG_FILE%"
    goto BUILD_FAILED
)
echo [5/6] API Preparation Completed!>>"%LOG_FILE%"
call :timer_stop
echo.>>"%LOG_FILE%"

rem 6. Electron Packaging
echo [6/6] Packaging Electron Application...
echo [6/6] Packaging Electron Application...>>"%LOG_FILE%"
call :timer_start
call "%SCRIPT_DIR%\electron_package.bat" >>"%LOG_FILE%" 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Electron Packaging Failed! Check build_all.log for details.
    echo [ERROR] Electron Packaging Failed!>>"%LOG_FILE%"
    goto BUILD_FAILED
)
echo [6/6] Electron Packaging Completed!>>"%LOG_FILE%"
call :timer_stop
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


:timer_start
set timer_start=%time%
echo 开始时间： %timer_start%
exit /b

:timer_stop
set timer_end=%time%
echo 结束时间：%timer_end%
set /a timer_start_int = %timer_start:~0,2%*3600 + %timer_start:~3,2%*60 + %timer_start:~6,2%
set /a timer_end_int   = %timer_end:~0,2%*3600 + %timer_end:~3,2%*60 + %timer_end:~6,2%
if %timer_end_int% lss %timer_start_int% (
    set /a timer_end_int += 86400
)
set /a duration = timer_end_int - timer_start_int
echo 阶段耗时: %duration% 秒
exit /b