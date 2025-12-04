@echo off
rem ================================================
rem PPT2HTML Project Environment Check and Preparation Script
rem ================================================

rem Check Node.js environment
echo Checking Node.js environment...
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Node.js not found. Please install Node.js and ensure it's in PATH.
    exit /b 1
)

call node --version
rem Check npm environment
echo Checking npm environment...
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: npm not found. Please install Node.js and ensure npm is in PATH.
    exit /b 1
)

call npm --version
