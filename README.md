# ATI Work Analytics

V1 mínima para piloto controlado: agente Windows → SQLite local → FastAPI → PostgreSQL → dashboard Next.js. O produto coleta somente processo em primeiro plano, título da janela, duração de sessão e tempo idle. Não possui keylogger, captura de texto, clipboard, screenshot ou leitura de conteúdo de páginas.

## Arquitetura e decisões

- `machine_uuid` persistido no SQLite é a identidade da instalação; hostname e IP são atributos atualizáveis.
- O agente separa coleta (5 s por padrão) da sincronização (60 s no piloto). Em falhas de rede, os registros ficam no SQLite.
- Cada sessão recebe `event_uuid`; a API ignora UUIDs já existentes, tornando reenvios seguros.
- Máquinas começam como `PENDING`; um administrador aprova e emite o token do agente. Tokens e segredos vêm de variáveis de ambiente.
- Autorização é feita no backend por permissões granulares, não apenas por elementos ocultos na interface.

## Executar o ambiente

1. Copie `.env.example` para `.env` e troque todos os segredos.
2. Execute `docker compose up --build`.
3. Na própria máquina, acesse `http://localhost:9001/login`. A partir de outro computador da rede, use `http://IP-DO-SERVIDOR:9001/login`; por exemplo, `http://10.36.30.100:9001/login`. A API estará em `http://IP-DO-SERVIDOR:9000` e o `/docs` é destinado somente à documentação técnica.
4. O login inicial é `admin`; a senha vem de `BOOTSTRAP_ADMIN_PASSWORD`. Também é criado o acesso `usuario` com a senha definida em `BOOTSTRAP_USER_PASSWORD` (neste piloto: `usu@rio@ti`).
5. Consulte `agent/README.md` para o piloto Windows. Após o primeiro registro, aprove a máquina em `POST /api/v1/machines/{machine_id}/approve`, reinicie o agente e ele sincronizará.

## Escopo deliberadamente posterior

Detecção de lock/unlock, cliques, processos em segundo plano, classificações, departamentos, administração visual completa, domínios/sites e distribuição por GPO são extensões planejadas. Sites exigem uma análise específica de privacidade e viabilidade antes de serem incluídos.

## Testes

Execute `pytest` no diretório `backend`. O conjunto inicial cobre registro pendente, autenticação e idempotência da sincronização.
