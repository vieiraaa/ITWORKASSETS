# ATI Work Analytics Agent

The pilot agent is Windows-only. It observes only the foreground process name, its window title, and Windows idle duration. It does **not** collect keystrokes, text entered, clipboard content, screenshots, page content, or passwords.

1. Install Python 3.12 on the test Windows machine.
2. Run `pip install -r requirements.txt` in this folder.
3. Copy `config.example.json` to `config.json` and set the API URL.
4. Run `python -m ati_agent.main config.json`.
5. Approve the pending machine with the API/dashboard. Restart the agent once to obtain its token.

The SQLite file is stored under the configured `data_directory`; pending rows remain there while the server is unavailable.

## Gerar executável Windows

Na máquina de desenvolvimento, dentro desta pasta, execute no PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\build-exe.ps1
```

O arquivo será criado em `dist\ATI-Agent.exe`. No computador monitorado, execute o `.exe`; na primeira execução ele solicitará a URL da API, registrará a máquina como `PENDING` e manterá o terminal aberto para coleta e sincronização. A aprovação continua sendo feita no dashboard.

## Implantação por GPO: agente interativo por usuário

Para a coleta de aplicação em primeiro plano, título de janela e idle, use `ATI-Agent-Interactive.exe` como uma Scheduled Task de **logon do usuário** via GPO. Ele é compilado sem console, executa no contexto do usuário e não exibe janela. Antes, distribua o executável e a configuração executando `install-interactive-agent.ps1 -ApiUrl 'http://SERVIDOR:9000/api/v1'` como script de inicialização da máquina.

O GPO deve executar o agente a cada logon; assim, cada sessão interativa consegue enxergar somente sua própria área de trabalho. O `machine_uuid` no SQLite mantém a instalação reconhecível mesmo com alteração de IP.

### Roteiro de instalação para piloto

1. Na máquina de desenvolvimento, gere os executáveis:

   ```powershell
   Set-ExecutionPolicy -Scope Process Bypass
   .\build-exe.ps1
   ```

2. Copie estes dois arquivos da pasta `dist` para uma pasta compartilhada acessível aos computadores do domínio:

   - `ATI-Agent-Interactive.exe`
   - `install-interactive-agent.ps1`

3. No computador piloto, abra o PowerShell como administrador e execute o instalador, trocando o nome/IP pelo servidor real:

   ```powershell
   Set-ExecutionPolicy -Scope Process Bypass
   .\install-interactive-agent.ps1 -ApiUrl 'http://SERVIDOR-ATI:9000/api/v1'
   ```

   O instalador cria `C:\ProgramData\ATI Work Analytics\`, grava a configuração e a fila SQLite em `data`. Usuários comuns podem gravar somente nessa pasta de dados; não podem alterar o executável nem a URL da API.

4. Crie uma tarefa agendada de teste com gatilho **At log on**, configurada para executar no contexto do usuário conectado:

   ```text
   C:\ProgramData\ATI Work Analytics\ATI-Agent-Interactive.exe
   ```

   Marque a tarefa como oculta e não use uma conta de serviço para ela. O agente precisa estar na sessão interativa do colaborador para observar janela em primeiro plano e idle.

5. Faça logoff/logon no piloto. A máquina será registrada como `PENDING`. Aprove-a pela tela Máquinas. O agente tenta buscar o token novamente em até 60 segundos.

6. Confirme no dashboard que há heartbeat, sessões de aplicações e períodos idle. Só depois replique para um grupo pequeno via GPO.

### Configuração recomendada na GPO

Use uma política de computador para copiar os dois arquivos e executar `install-interactive-agent.ps1` como script de inicialização, com `-ApiUrl` fixo. Em seguida, use **Computer Configuration → Preferences → Control Panel Settings → Scheduled Tasks** para criar uma tarefa de logon que execute o caminho acima. A tarefa deve iniciar somente quando o usuário estiver conectado e ser executada com as permissões do usuário conectado.

Não use o serviço Windows para esta tarefa: serviços executam em uma sessão não interativa e não conseguem ler a janela ativa do colaborador.

## Serviço Windows

O build também cria `dist\ATI-Agent-Service.exe`. Copie esse arquivo e `install-service.ps1` para uma pasta no computador monitorado e abra o PowerShell **como administrador** nessa pasta:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install-service.ps1
```

Informe a URL da API quando solicitado. O serviço será instalado para iniciar automaticamente com o Windows, mesmo sem usuário logado. Aprove a máquina `PENDING` no dashboard. Para remover:

```powershell
.\uninstall-service.ps1
```

Um serviço do Windows não tem acesso à área de trabalho interativa. Por isso, ele não deve ser usado para a coleta de janelas, aplicações ou idle; mantenha-o somente como componente opcional de infraestrutura. A coleta detalhada é feita pelo agente interativo iniciado no logon.
