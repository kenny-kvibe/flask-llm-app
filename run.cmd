@ECHO off
SETLOCAL

PUSHD "%~dp0app"
REM main.py Arg1 => OPEN_BROWSER
REM main.py Arg2 => DEV_MODE
python.exe -B main.py 1 0
POPD

ENDLOCAL
PAUSE
EXIT /B 0