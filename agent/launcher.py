import json
import os
import sys
from pathlib import Path

from ati_agent.main import Agent

APP_DIR = Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'ATI Work Analytics'
CONFIG_PATH = APP_DIR / 'config.json'
DEFAULT_CONFIG = {
    'api_url': 'http://localhost:9000/api/v1',
    'collection_interval_seconds': 5,
    'sync_interval_seconds': 60,
    'idle_threshold_seconds': 60,
    'data_directory': str(APP_DIR / 'data'),
}


def load_config():
    APP_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding='utf-8'))

    print('Configuração inicial do ATI Work Analytics')
    print('Informe o endereço da API do computador servidor.')
    api_url = input('API [http://localhost:9000/api/v1]: ').strip() or DEFAULT_CONFIG['api_url']
    config = {**DEFAULT_CONFIG, 'api_url': api_url.rstrip('/')}
    CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding='utf-8')
    print(f'Configuração salva em: {CONFIG_PATH}')
    return config


def main():
    try:
        config = load_config()
        agent = Agent(config)
        agent.run()
    except KeyboardInterrupt:
        print('\nAgente encerrado.')
    except Exception as error:
        print(f'Erro: {error}')
        input('Pressione Enter para fechar...')


if __name__ == '__main__':
    main()
