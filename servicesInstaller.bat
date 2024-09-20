@echo off
REM Change directory to the folder where the batch file is located
cd /d %~dp0

REM Install the Python service
python MyService.py install

REM Start the Python service
python MyService.py start

REM Configure the service to auto-start on boot
sc config CASTGHAppService start= auto

echo Service installation and startup complete.
pause
