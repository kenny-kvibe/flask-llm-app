@ECHO off
SETLOCAL

PUSHD "%~dp0app"
REM main.py Arg1 => DEV_MODE
REM main.py Arg2 => OPEN_BROWSER
python.exe -B web_app.py 0 1
POPD

ENDLOCAL
PAUSE
EXIT /B 0
