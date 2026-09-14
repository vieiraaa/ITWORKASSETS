import json
import os
import threading
import traceback
from pathlib import Path

import win32event
import win32service
import win32serviceutil

from ati_agent.main import Agent

APP_DIR = Path(os.environ.get('PROGRAMDATA', r'C:\ProgramData')) / 'ATI Work Analytics'
CONFIG_PATH = APP_DIR / 'config.json'
LOG_PATH = APP_DIR / 'service.log'


def log(message):
    APP_DIR.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open('a', encoding='utf-8') as file:
        file.write(message + '\n')


class ATIWorkAnalyticsService(win32serviceutil.ServiceFramework):
    _svc_name_ = 'ATIWorkAnalytics'
    _svc_display_name_ = 'ATI Work Analytics Agent'
    _svc_description_ = 'Coleta e sincroniza atividade observável do Windows com a API ATI.'

    def __init__(self, args):
        super().__init__(args)
        self.stop_event = threading.Event()
        self.wait_handle = win32event.CreateEvent(None, 0, 0, None)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.stop_event.set()
        win32event.SetEvent(self.wait_handle)

    def SvcDoRun(self):
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        worker = threading.Thread(target=self.run_agent, name='ati-agent', daemon=True)
        worker.start()
        win32event.WaitForSingleObject(self.wait_handle, win32event.INFINITE)

    def run_agent(self):
        try:
            if not CONFIG_PATH.exists():
                raise FileNotFoundError(f'Configuração ausente: {CONFIG_PATH}')
            config = json.loads(CONFIG_PATH.read_text(encoding='utf-8-sig'))
            log('Serviço iniciado.')
            Agent(config).run(self.stop_event)
        except Exception:
            log(traceback.format_exc())


def main():
    APP_DIR.mkdir(parents=True, exist_ok=True)
    win32serviceutil.HandleCommandLine(ATIWorkAnalyticsService)


if __name__ == '__main__':
    main()
