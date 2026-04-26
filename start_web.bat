@echo off
title Next.js Frontend - DATN Chatbot
taskkill /F /IM node.exe >nul 2>&1
SET PATH=C:\Program Files\nodejs\;%PATH%
cd /d "%~dp0frontend-web"
echo.
echo  ====================================
echo    DATN Chatbot - Next.js Frontend
echo    http://localhost:3000
echo  ====================================
echo.
npm run dev
pause
