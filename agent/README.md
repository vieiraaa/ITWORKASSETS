# ATI Work Analytics — instalação do agente (piloto)

Este é o procedimento único para testar em um computador Windows. O agente roda invisivelmente na sessão do usuário conectado, o que permite medir idle e identificar aplicação/janela em primeiro plano. Ele não registra teclas, texto digitado, clipboard, screenshot ou conteúdo de sites.

## Antes de começar

- Na máquina de desenvolvimento, descubra o IP atual com `ipconfig`. Use o IPv4 da rede conectada, por exemplo `10.36.30.100`.
- O computador piloto e a máquina de desenvolvimento precisam estar na mesma rede ou ter rota até ela.
- A API precisa responder em `http://IP-DO-SERVIDOR:9000/health` a partir do computador piloto.
- Não use `localhost` no piloto: ele aponta para o próprio piloto, não para a máquina de desenvolvimento.
- Comece com uma máquina e uma conta com administrador local.

## 1. Gerar o pacote

Na máquina de desenvolvimento, instale Python **3.12 x64**, abra PowerShell na pasta `agent` e execute:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\build-exe.ps1
```

O resultado será `dist\ATI-Work-Analytics-Agent\`, contendo:

- `ATI-Agent-Interactive.exe`
- `install-interactive-agent.ps1`
- `uninstall-interactive-agent.ps1`
- `README.md`

Se o executável não existir, pare: o pacote não está pronto. O build imprime o SHA-256. Se o arquivo desaparecer após o build, solicite à TI/SecOps a análise ou allowlist do hash; não tente contornar antivírus/EDR.

## 2. Testar a rede no computador piloto

Antes de instalar, abra o PowerShell no piloto e substitua `10.36.30.100` pelo IP atual da máquina de desenvolvimento:

```powershell
Test-NetConnection 10.36.30.100 -Port 9000
Invoke-RestMethod 'http://10.36.30.100:9000/health'
```

O primeiro comando deve mostrar `TcpTestSucceeded : True` e o segundo deve retornar `status : ok`. Se falhar, corrija firewall, rota, Wi-Fi/cabo ou IP antes de continuar. Não use a porta `8000`: neste ambiente, a API é publicada na porta `9000` e o dashboard na `9001`.

## 3. Instalar no computador piloto

1. Copie a pasta inteira `ATI-Work-Analytics-Agent` para o piloto, por exemplo na Área de Trabalho.
2. Abra PowerShell **como Administrador**.
3. Entre na pasta copiada. Ajuste o caminho se o usuário ou local forem diferentes:

```powershell
Set-Location 'C:\Users\SEU_USUARIO\Desktop\ATI-Work-Analytics-Agent'
```

4. Execute usando o IP atual do servidor:

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
.\install-interactive-agent.ps1 -ApiUrl 'http://10.36.30.100:9000/api/v1'
```

O instalador testa primeiro `http://10.36.30.100:9000/health`; se não houver resposta, não instala nada. Corrija rede, DNS, firewall ou URL e tente novamente.

Ele cria:

- executável e configuração em `C:\ProgramData\ATI Work Analytics\`;
- SQLite e log em `C:\ProgramData\ATI Work Analytics\data\`;
- um atalho comum de inicialização, que inicia o agente invisivelmente no próximo logon de qualquer usuário.
- uma tarefa agendada que verifica o agente a cada minuto, ajudando a recuperá-lo após suspensão, retomada ou desbloqueio.

## 4. Iniciar, aprovar e validar

O instalador prepara o agente para o próximo logon, mas para validar imediatamente inicie-o uma vez:

```powershell
Start-Process 'C:\ProgramData\ATI Work Analytics\ATI-Agent-Interactive.exe' -WindowStyle Hidden
```

1. No computador de desenvolvimento, abra `http://10.36.30.100:9001`, entre no dashboard e acesse **Máquinas**.
2. Aguarde a máquina aparecer como `PENDING` e clique em **Aprovar**.
3. Aguarde até 60 segundos para o agente buscar o token e começar a enviar heartbeat.
4. Confirme que o status mudou para `ONLINE` e use o computador por alguns minutos.
5. Depois da validação, faça logoff/logon e suspenda/retome o piloto para confirmar que o atalho e o watchdog iniciam o agente automaticamente.

Se o agente já estava instalado, reinstale usando este pacote atualizado para criar o watchdog. A instalação preserva a identidade e a fila local em `C:\ProgramData\ATI Work Analytics\data\`.

Em caso de falha, execute no piloto:

```powershell
Get-Process ATI-Agent-Interactive -ErrorAction SilentlyContinue
Get-Content 'C:\ProgramData\ATI Work Analytics\config.json'
Get-Content 'C:\ProgramData\ATI Work Analytics\data\interactive-agent.log' -Tail 50
```

O `config.json` deve conter o IP atual em `api_url`. Se o IP do servidor mudar, repita os testes de rede e execute novamente o instalador com o novo IP.

## Remover

No PowerShell como administrador:

```powershell
.\uninstall-interactive-agent.ps1
```

Isso remove atalho, executável, configuração e fila SQLite local.

## GPO — após o piloto

Use uma GPO de computador para copiar o pacote de uma origem interna e executar `install-interactive-agent.ps1` como script de inicialização, com a `-ApiUrl` apontando para um DNS ou IP fixo do servidor. O atalho criado pelo instalador já inicia o agente no contexto interativo do usuário. Não use Windows Service para a coleta de janela/aplicação/idle.
