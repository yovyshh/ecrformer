@echo off
title ECRformer Gradio Web Demo
cd /d "%~dp0"

echo ========================================================
echo  Starting ECRformer Gradio Web Demo (Port 7860)
echo ========================================================
echo.

"C:\Users\Windows 11 Pro\AppData\Local\Programs\Python\Python312\python.exe" gradio_app.py

pause
