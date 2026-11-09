@echo off
REM VideoGen One-Click Runner (9:16 1080p Short Video Builder)
set "PY_EXE=%~dp0.venv\Scripts\python.exe"
if not exist "%PY_EXE%" set "PY_EXE=python"

if "%~1"=="" (
    "%PY_EXE%" "%~dp0videogen.py" build "projects\project_azorian\project.json"
) else (
    "%PY_EXE%" "%~dp0videogen.py" %*
)
