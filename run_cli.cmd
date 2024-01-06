@ECHO off
SETLOCAL

PUSHD "%~dp0app"
REM main.py Arg1 => OPEN_BROWSER  (no effect)
REM main.py Arg2 => DEV_MODE
python.exe -B cli_app.py 0 0
POPD

ENDLOCAL
PAUSE
EXIT /B 0
