@echo off
title FastAPI Backend - DATN Chatbot
:: Kill any existing server on port 8000
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do taskkill /PID %%a /F >nul 2>&1
cd /d "%~dp0"
call "%~dp0venv\Scripts\activate.bat"
echo.
echo  ====================================
echo    DATN Chatbot - FastAPI Backend
echo    http://localhost:8000/docs
echo  ====================================
echo.
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
pause
