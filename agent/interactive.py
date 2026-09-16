"""Silent agent intended for a GPO logon task, running in the user's interactive session."""
import ctypes, json, os
from pathlib import Path
from ati_agent.main import Agent

APP_DIR = Path(os.environ.get('PROGRAMDATA', r'C:\ProgramData')) / 'ATI Work Analytics'
CONFIG_PATH = APP_DIR / 'config.json'
LOG_PATH = APP_DIR / 'data' / 'interactive-agent.log'
MUTEX_NAME = 'Global\\ATI-Work-Analytics-Interactive-Agent'

def log(message):
    with LOG_PATH.open('a', encoding='utf-8') as file: file.write(message + '\n')
def main():
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, MUTEX_NAME)
    if ctypes.windll.kernel32.GetLastError() == 183:
        return
    try:
        if not CONFIG_PATH.exists():
            log('Configuração ausente; agente interativo não iniciado.'); return
        log('Agente iniciado.')
        Agent(json.loads(CONFIG_PATH.read_text(encoding='utf-8-sig'))).run()
    except Exception as error: log(f'Falha no agente interativo: {error!r}')
if __name__ == '__main__': main()
