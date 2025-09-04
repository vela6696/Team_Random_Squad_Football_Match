@echo off
set SCRIPT_NAME=%~n1
pyinstaller --onefile --noconsole %1

echo Build finished!
echo Waiting for .exe to appear...

:waitloop
if not exist dist\%SCRIPT_NAME%.exe (
    timeout /t 1 >nul
    goto waitloop
)

echo Copying .exe to run folder...
copy /Y dist\%SCRIPT_NAME%.exe ..\run\

echo Done!
pause
