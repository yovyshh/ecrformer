@echo off
title ECRformer Satellite Cloud Removal Demo
cd /d "%~dp0"

echo ========================================================
echo  Starting ECRformer Interactive Web Demonstration
echo  Models: Sweet-Spot PatchGAN + Baseline ECRformer-Lite
echo ========================================================
echo.

"C:\Users\Windows 11 Pro\AppData\Local\Programs\Python\Python312\python.exe" -m streamlit run app.py --server.port 8501 --server.headless false

pause
