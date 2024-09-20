import win32serviceutil
import win32service
import win32event
import servicemanager
import subprocess
import os
 
class MyService(win32serviceutil.ServiceFramework):
    _svc_name_ = "CASTGHAppService"
    _svc_display_name_ = "CAST GitHub App Service"
    _svc_description_ = "This service runs the Python app and sets up ngrok tunnel."
 
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
 
    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
 
    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, "")
        )
        self.main()
 
    def main(self):
        # Get the current directory of the service script
        current_dir = os.path.dirname(os.path.abspath(__file__))
 
        # Command to run waitress-serve
        waitress_cmd = ["waitress-serve", "--port=5001", "app:app"]
 
        # Command to run ngrok with the domain and config
        ngrok_cmd = [
            os.path.join(current_dir, "ngrok.exe"),
            "http",
            f"--domain=cast.gh.ngrok.app", "5001",
            f"--config={os.path.join(current_dir, 'ngrok-config.yaml')}",
            f"--log={os.path.join(current_dir, 'ngrok.log')}",
            "--log-level=debug"
        ]
 
        # Start the waitress server
        waitress_process = subprocess.Popen(waitress_cmd, cwd=current_dir)
 
        # Start ngrok tunnel
        ngrok_process = subprocess.Popen(ngrok_cmd, cwd=current_dir)
 
        # Wait for the service to be stopped
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)
 
        # If service is stopped, terminate both processes
        waitress_process.terminate()
        ngrok_process.terminate()
 
if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(MyService)