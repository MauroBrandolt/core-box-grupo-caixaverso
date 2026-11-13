# Registro de exceções de segurança — Core Box — Grupo 04

Este arquivo registra somente riscos conscientemente aceitos no Dia 02.

Correções realizadas, falsos positivos e alertas meramente informativos são
documentados no RELATORIO-DIA02.md e não são tratados automaticamente como
exceções.

Nenhuma exceção pode ser usada para desligar um gate sem justificativa.
As etapas 1 a 6 permanecem bloqueantes.

## Exceções vigentes

| ID | Gate / componente | Achado | Ameaça | Decisão | Justificativa | Controle compensatório | Dono | Prazo | Aprovado por |
|---|---|---|---|---|---|---|---|---|---|
| EXC-001 | Produção / transporte | Aplicação publicada em HTTP sem TLS | TM-13 | Aceitar temporariamente | O laboratório do Dia 02 utiliza acesso HTTP direto à VPS e a evolução de TLS está prevista para a arquitetura posterior | Environment `producao` protegido por revisão; deploy somente da `main`; imagem implantada por digest; aplicação não expõe segredos em `/health`; acesso estritamente de laboratório | Grupo 04 | Dia 04 | Pendente de aprovação na Etapa 8 |
| EXC-002 | Produção / deploy | Porta SSH TCP/22 exposta para realização do deploy | TM-14 | Aceitar temporariamente | O mecanismo de deploy definido para o laboratório usa SSH na porta 22 | Usuário dedicado `deploy`; autenticação por Ed25519; sem senha no workflow; `PROD_KNOWN_HOSTS` com verificação estrita do host; Environment protegido; `prevent_self_review` habilitado | Grupo 04 | Dia 04 | Pendente de aprovação na Etapa 8 |
| EXC-003 | Produção / credencial de deploy | Chave SSH Ed25519 de longa duração armazenada como Secret do Environment | TM-15 / TM-31 | Aceitar temporariamente | O mecanismo de deploy do Dia 02 utiliza uma chave SSH de deploy persistente | Somente a chave pública permanece na VPS; privada armazenada como `PROD_SSH_KEY` no Environment `producao`; sem Repository Secret correspondente; acesso restrito ao usuário `deploy`; rotação planejada | Grupo 04 | Dia 04 | Pendente de aprovação na Etapa 8 |

## Plano de tratamento — Dia 04

As exceções EXC-001, EXC-002 e EXC-003 devem ser substituídas pela arquitetura
prevista para o Dia 04:

- AWS SSM para administração/deploy sem SSH público;
- OIDC entre GitHub Actions e AWS, eliminando credencial SSH de longa duração;
- ALB com TLS para terminação HTTPS;
- WAF na borda conforme arquitetura aprovada.

## Triagem que NÃO constitui exceção

### Gitleaks — baseline histórica

A baseline `.gitleaks-baseline.json` contém seis ocorrências históricas
identificadas em dois commits antigos.

A baseline serve para distinguir achados históricos conhecidos de novos
vazamentos. Ela não substitui rotação ou revogação de uma credencial real.

Situação para a entrega:

- novos segredos não podem ser aceitos pela baseline;
- valores de produção permanecem fora do repositório;
- segredos de produção são fornecidos pelo Environment `producao`;
- o token JWT de fixture deve permanecer classificado como dado de teste;
- qualquer credencial histórica real deve estar rotacionada/revogada.

Nenhum novo segredo pode ser suprimido apenas para deixar o gate verde.

### OWASP ZAP — Non-Storable Content [10049]

Decisão: **manter o comportamento**.

O alerta foi observado em respostas protegidas com `Cache-Control: no-store`.
A remoção desse controle apenas para zerar o ZAP enfraqueceria a proteção de
conteúdo potencialmente sensível.

O ZAP é informativo na Etapa 7. O alerta permanece documentado na triagem e
não constitui motivo para alterar a política segura de cache.

### OWASP ZAP — Session Management Response Identified [10112]

Decisão: **informativo**.

A regra identifica respostas relacionadas ao gerenciamento de sessão. A
presença do alerta, isoladamente, não demonstra uma vulnerabilidade.

Os cookies tiveram `HttpOnly` e `SameSite=Lax` configurados e a proteção CSRF
foi validada separadamente.

### OWASP ZAP — User Controllable HTML Element Attribute [10031]

Decisão: **pendente de triagem conclusiva, sem supressão**.

O alerta ocorreu em `/abrir-conta`, mas o resumo disponível não apresentou
evidência suficiente para classificá-lo como XSS explorável nem como falso
positivo.

Por isso:

- não foi adicionada supressão genérica;
- a aplicação mantém escaping dos templates;
- a CSP permanece restritiva;
- a ocorrência será mantida no relatório final como WARN informativo até que
  exista evidência suficiente para classificação definitiva.

## Achados corrigidos — não são exceções

Os seguintes itens foram corrigidos e devem permanecer cobertos por testes ou
gates, não por supressões:

- TM-01 — bloqueio após tentativas inválidas;
- TM-03 — autorização da conta de origem do Pix;
- TM-04 — limite Pix imposto no servidor;
- TM-06 — remoção de token, Authorization e payload completo dos logs;
- TM-07 — tratamento seguro de erros e valores inválidos;
- TM-08 — autorização de comprovantes;
- TM-10 — justificativa e alçada do backoffice;
- TM-12 — hash seguro de senha;
- TM-20 — idempotência básica do Pix;
- TM-23 — mensagem de autenticação não enumerável;
- TM-29 — consulta SQL parametrizada;
- TM-31 — dependências e imagem atualizadas;
- injeção de comando do diagnóstico — substituição do comando concatenado por
  execução parametrizada e allowlist.

## Regras para novas exceções

Uma nova exceção somente será aceita se possuir:

1. identificação do achado ou teste;
2. TM-ID relacionado;
3. decisão explícita;
4. justificativa;
5. controle compensatório;
6. dono;
7. prazo;
8. aprovador.

Não serão aceitos como mecanismo de conveniência:

- `nosemgrep` sem ID e justificativa;
- `.trivyignore` sem risco documentado;
- exclusão de abuse case;
- `xfail` sem motivo e prazo;
- inclusão de segredo real em baseline;
- `continue-on-error` nos gates 1 a 6 em modo bloqueio.
