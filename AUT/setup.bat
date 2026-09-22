@echo off
cd /d "%~dp0"
echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
  echo.
  echo Failed to create venv. Is "python" on your PATH and pointing at the interpreter you want?
  pause
  exit /b 1
)
echo.
echo Upgrading pip, setuptools, wheel inside the venv...
call venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
  echo.
  echo pip/setuptools/wheel upgrade failed.
  pause
  exit /b 1
)
echo.
echo Installing project requirements...
call venv\Scripts\pip.exe install -r requirements.txt
if errorlevel 1 (
  echo.
  echo requirements install failed.
  pause
  exit /b 1
)
echo.
echo Done. Venv is ready at venv\Scripts\python.exe
echo In PyCharm: Settings ^> Project ^> Python Interpreter ^> Add Interpreter ^> Existing environment,
echo then browse to that path.
pause
