@echo off
TITLE Inventory Management System
ECHO ======================================================
ECHO Starting Stock and Customer Management Dashboard...
ECHO ======================================================
ECHO.

:: Check if Python is installed
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO [ERROR] Python is not installed or not found in your PATH.
    ECHO Please install Python from https://www.python.org/
    PAUSE
    EXIT /B
)

:: Run the application
streamlit run app.py

:: Keep window open in case of crash
PAUSE