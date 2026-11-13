# Relatório do Dia 02 — Grupo 04

## Execuções

- Repositório: `MauroBrandolt/core-box-grupo-caixaverso`
- Branch principal: `main`
- Primeira execução (modo auditoria): **preencher com o link da primeira execução**
- Execução final em modo bloqueio: **preencher após o push final**
- Suíte local final antes da entrega: **20 passed**
- Deploy aprovado por: **preencher após aprovação da Etapa 8**
- Imagem implantada: **preencher com `ghcr.io/...@sha256:...` após o deploy**
- Destino previsto do laboratório: `deploy@3.142.97.137:8080`
- Diretório de produção: `/opt/core-box`

> Os campos de execução final, aprovador e digest somente serão preenchidos
> depois da evidência real. Nenhuma aprovação ou implantação é presumida.

---

## Placar da esteira

| Etapa | Achados / situação inicial | Corrigidos / evolução | Falsos positivos | Exceções / observações |
|---|---|---|---|---|
| 1 — Gitleaks | 6 ocorrências históricas conhecidas em 2 commits | Segredos removidos do código atual; produção usa Environment/variáveis; baseline histórica preservada | JWT de fixture permanece classificado como dado de teste, sujeito à confirmação final | Baseline não substitui rotação/revogação de credencial real |
| 2 — Semgrep | Execução anterior chegou a apresentar 8 findings no acompanhamento do grupo | Correções SAST aplicadas; 3 regras próprias adicionadas: TM-03, TM-04 e TM-06 | Nenhuma supressão `nosemgrep` aplicada | Validação final das regras próprias ocorrerá no runner GitHub |
| 3 — Build e testes | Execuções intermediárias apresentaram 15 passed / 5 failed | **20 passed** localmente após correções | Não se aplica | Nenhum abuse case removido ou marcado como xfail |
| 4 — Trivy FS / SBOM | Dependências vulneráveis foram identificadas durante o Dia 02 | Dependências atualizadas; gate de HIGH/CRITICAL corrigíveis ficou limpo na execução observada; SBOM CycloneDX gerado | Nenhum `.trivyignore` aplicado | Gate permanece bloqueante |
| 5 — Docker / GHCR | Imagem inicial possuía base antiga e hardening insuficiente | Base atualizada, COPY seletivo, usuário não-root, sem curl/ping, HEALTHCHECK, CMD exec | Não se aplica | Publicação por commit/tag e propagação do digest |
| 6 — Trivy Image | Imagem anterior apresentava CVEs corrigíveis em SO e pacotes Python | Debian observado evoluiu de 12.1 para 12.15; setuptools/wheel atualizados; gate corrigível passou | Nenhuma supressão aplicada | Scan realizado sobre o digest produzido na Etapa 5 |
| 7 — Homologação / ZAP | Cabeçalhos, CSRF, CSP/cookies e outras configurações web geraram alertas | Cabeçalhos, CSP, CSRF, cookies e isolamento reforçados | Nenhum WARN residual foi marcado genericamente como falso positivo | ZAP informativo por contrato; triagem registrada |
| 8 — Produção | Etapa ausente na versão inicial da esteira | Job de aprovação/deploy por digest implementado com Environment `producao` e smoke test | Não se aplica | Execução real depende de aprovação e conectividade SSH pública |

---

## Resultado final dos testes

Última validação local:

```text
....................                                                     [100%]
20 passed



A suíte contém testes funcionais e abuse cases derivados do Threat Model.

Nenhum teste de segurança foi removido para obter resultado verde.

## Ameaças do Threat Model cobertas pela esteira
Cobertas por ferramentas
TM-15 / TM-16 — Gitleaks e gestão de segredos.
TM-31 — Trivy filesystem, dependências, SBOM e Trivy Image.
TM-07 — Semgrep, testes e validação de configuração.
TM-12 — teste de hash de senha.
TM-29 — teste de SQL Injection.
Configurações HTTP — OWASP ZAP Baseline.
Cobertas por regras Semgrep próprias

O arquivo .semgrep/box-regras.yml contém 3 regras com metadata.threat_model:

box.tm03.conta-origem-controlada-pelo-cliente → TM-03;
box.tm04.limite-override-controlado-pelo-cliente → TM-04;
box.tm06.credencial-ou-token-em-log → TM-06.

As três regras são ERROR.

A execução local do semgrep-core na VPS apresentou limitação de criação de threads do runtime. A validação final será realizada pelo runner do GitHub Actions, onde o Semgrep já executou anteriormente.

Cobertas por abuse cases
TM-01 — bloqueio de tentativas;
TM-03 — BOLA no Pix;
TM-04 — limite Pix;
TM-07 — erros e stack trace;
TM-08 — autorização de comprovantes;
TM-10 — justificativa e alçada;
TM-12 — hash de senha;
TM-20 — idempotência;
TM-23 — enumeração de CPF;
TM-29 — SQL Injection.
Achado novo no Dia 02

Foi encontrada injeção de comando (CWE-78) na função de diagnóstico do backoffice.

Correção:

subprocess.run;
argumentos fornecidos como lista;
sem concatenação em shell;
allowlist de destinos;
timeout;
tratamento controlado de erro.

O achado deve receber o próximo TM-ID livre no workbook do Dia 01.

Os TM-IDs existentes não devem ser renumerados.

## Correções e controles implementados
TM-01 — limitação de tentativas

Foi utilizado o armazenamento tentativas_login para contabilizar falhas por CPF.

Após cinco tentativas inválidas:

o acesso é temporariamente bloqueado;
a API retorna HTTP 429;
o bloqueio possui duração temporária;
autenticação válida limpa a contagem.
TM-03 — BOLA no Pix

A conta de origem efetiva é derivada do usuário autenticado.

Uma conta_origem informada pelo cliente que não pertença ao usuário é rejeitada.

A autorização depende do servidor, não da interface ou de parâmetro fornecido pelo cliente.

TM-04 — limite_override

O cliente não pode usar limite_override para superar o limite Pix.

O limite vigente é calculado e imposto no servidor.

TM-06 — credencial/token em logs

O log do Pix deixou de registrar:

cabeçalho Authorization;
cookie box_token;
token JWT;
payload completo;
CPF como identificador operacional do evento.

O log atual utiliza apenas usuario_id e canal api ou web.

TM-07 — debug, erros e exposição

Foram realizadas as seguintes mudanças:

respostas de erro interno não expõem stack trace ao cliente;
/health não divulga versão, ambiente ou debug;
erros HTTP normais não são convertidos indevidamente em 500;
valores Pix inválidos são tratados;
DEBUG fica desabilitado por padrão;
ativação de debug exige BOX_DEBUG=true.
TM-08 — comprovantes

Comprovantes exigem autenticação e autorização.

A transação é verificada em relação à conta do usuário autenticado antes de ser apresentada.

TM-10 — backoffice

Foram adicionados:

justificativa obrigatória;
validação de tipo;
validação de valor;
validação da existência da conta;
restauração do acesso correto ao banco;
alçada de R$ 10.000.

Acima da alçada:

resposta HTTP 202;
saldo não é alterado imediatamente;
evento AJUSTE_PENDENTE_APROVACAO é registrado.

O fluxo maker-checker completo permanece evolução futura.

TM-12 — hash de senha

O armazenamento de senha utiliza as funções seguras do Werkzeug:

generate_password_hash;
check_password_hash.
TM-20 — idempotência

A Idempotency-Key passou a ser utilizada para recuperar a transação anterior da mesma conta.

Uma repetição sequencial da mesma chave não provoca novo débito.

Controle forte de concorrência/transação poderá ser evoluído posteriormente.

TM-23 — enumeração de CPF

Usuário inexistente e senha incorreta utilizam resposta de autenticação genérica, reduzindo enumeração direta por mensagem/status.

TM-29 — SQL Injection

A busca do backoffice utiliza consulta parametrizada.

A entrada do usuário não é concatenada à instrução SQL.

## Segredos e Gitleaks

A baseline atual contém:

6 ocorrências históricas conhecidas;
2 commits históricos;
regras generic-api-key e jwt.

Segredos de aplicação foram retirados do código atual.

Produção utiliza o Environment producao.

Secrets configurados pelo nome:

BOX_SECRET_KEY;
BOX_JWT_SECRET;
BOX_PSTI_API_KEY;
BOX_SMS_GATEWAY_TOKEN;
PROD_SSH_KEY;
PROD_KNOWN_HOSTS.

Valores dos Secrets não são registrados no relatório.

A baseline do Gitleaks:

não autoriza novos segredos;
não substitui rotação/revogação;
não transforma automaticamente uma credencial real em falso positivo.

A revogação/rotação de qualquer credencial histórica real deve permanecer registrada na evidência final.

## Docker e segurança da imagem

O Dockerfile final foi endurecido para utilizar:

python:3.11-slim-bookworm;
COPY seletivo;
usuário corebox não-root;
diretórios /app/data e /app/uploads graváveis pelo usuário da aplicação;
ausência de curl;
ausência de ping;
HEALTHCHECK usando Python stdlib;
CMD em formato exec;
instalação sem cache de dependências;
atualização de setuptools e wheel.

Validações executadas:

A .dockerignore também foi ampliada para excluir ambientes virtuais, artefatos, testes, dados locais, chaves, backups e arquivos temporários do contexto de build.

## Homologação e OWASP ZAP

A Etapa 7 utiliza OWASP ZAP Baseline em modo informativo:

Melhorias implementadas ao longo da triagem:

X-Frame-Options: DENY;
X-Content-Type-Options: nosniff;
CSP;
Permissions Policy;
Referrer Policy;
políticas de isolamento entre origens;
Cache-Control: no-store para conteúdo não estático;
remoção de unsafe-inline da CSP por migração dos estilos;
tokens CSRF nos formulários POST;
cookies com HttpOnly e SameSite=Lax;
opção de Secure parametrizada para futura migração HTTPS.

Último resumo observado antes do lote final:

Triagem dos WARNs:

Non-Storable Content: mantido, pois no-store é intencional;
Session Management Response Identified: informativo;
User Controllable HTML Element Attribute: mantido sem supressão até evidência conclusiva.
## Exceções vigentes

As exceções completas estão registradas em EXCECOES.md.

Resumo:

ID	TM	Risco	Prazo
EXC-001	TM-13	HTTP sem TLS no laboratório	Dia 04
EXC-002	TM-14	SSH TCP/8080 para deploy	Dia 04
EXC-003	TM-15 / TM-31	Chave SSH persistente	Dia 04

Plano do Dia 04:

AWS SSM;
OIDC;
ALB com TLS;
WAF.

O campo de aprovação nominal será preenchido somente após aprovação real.

## Decisões de política
Etapa 1 — Gitleaks

Bloqueante.

Novo segredo não tratado deve impedir a continuidade da pipeline.

O checkout utiliza histórico completo (fetch-depth: 0).

Etapa 2 — Semgrep

Bloqueante para as regras configuradas como erro.

A pipeline carrega:

p/python;
p/security-audit;
.semgrep/.

As regras próprias foram relacionadas a TM-03, TM-04 e TM-06.

Etapa 3 — Build e testes

Bloqueante.

Qualquer falha de instalação, build ou Pytest interrompe a cadeia.

Resultado local final:

Etapa 4 — Trivy FS / SCA

Bloqueante para HIGH/CRITICAL com correção disponível.

O relatório completo permanece informativo para demais severidades.

SBOM CycloneDX é produzido como artefato.

Etapa 5 — Docker / GHCR

Bloqueante.

Falha de build ou publicação impede a continuidade.

A referência da imagem e o digest são propagados como outputs.

Etapa 6 — Trivy Image

Bloqueante para HIGH/CRITICAL com correção disponível.

A imagem analisada é exatamente a referência por digest produzida na Etapa 5.

Etapa 7 — Homologação / ZAP

Informativa para findings do ZAP.

Falha na inicialização da aplicação continua sendo erro.

O ZAP não recebe permissão para criar issues automaticamente.

Etapa 8 — Aprovação e produção

Protegida por Environment.

A etapa foi preparada para:

executar somente após push/merge na main;
usar environment: producao;
utilizar reviewers e prevent_self_review;
implantar a mesma imagem aprovada por digest;
usar usuário SSH dedicado deploy;
trabalhar em /opt/core-box;
executar Docker Compose;
realizar smoke tests de /health e /login;
produzir artefato deploy-producao.

A execução efetiva permanece dependente da conectividade externa SSH e da aprovação de um revisor autorizado.

Environment producao

Configuração validada:

branch de deploy permitida: main;
prevent_self_review: true;
required reviewers configurados;
PROD_HOST=3.142.97.137;
segredos armazenados no Environment;
nenhum Repository Secret utilizado para os valores de produção consultados.

Usuário SSH previsto pelo contrato do laboratório:

Porta:

Diretório:

A identidade do servidor é verificada por PROD_KNOWN_HOSTS.

A chave privada permanece em PROD_SSH_KEY; somente a pública é instalada no authorized_keys da conta deploy.

## Atualização do Workbook do Dia 01

O workbook é mantido pelo grupo e não será recriado neste repositório.

Os colegas responsáveis devem utilizar o material consolidado em:

Orientações:

não renumerar TM-IDs existentes;
atualizar a coluna/plano Dia 02;
registrar controle, arquivo, critério de aceite e situação;
associar as exceções TM-13, TM-14 e TM-15/TM-31;
cadastrar Command Injection/CWE-78 com o próximo TM-ID livre real.
## Lições aprendidas

Ferramentas são complementares. Gitleaks, Semgrep, Trivy e ZAP não substituem abuse cases de autorização e lógica de negócio.

Pipeline verde precisa de contexto. Modo auditoria, severidade, baseline, exceções e políticas de gate alteram o significado de um resultado verde.

Correção precisa de teste de regressão. Mudanças legítimas durante o laboratório chegaram a introduzir regressões funcionais; testes e logs foram utilizados para localizar e corrigir essas regressões antes da entrega.

## Evidências e artefatos

Artefatos produzidos ou esperados pela pipeline:

relatorio-gitleaks;
relatorio-semgrep;
relatorio-03-build;
relatorio-04-trivy-sca;
docker-build;
trivy-image;
homologacao-zap;
homologacao-logs;
deploy-producao após a Etapa 8.

Evidências auxiliares locais foram consolidadas em:

## Pendências antes da entrega
Executar o lote final no GitHub Actions.
Confirmar as 3 regras próprias no runner do Semgrep.
Confirmar novamente os 20 testes no runner.
Confirmar Trivy FS e Image após o Docker hardening.
Confirmar ZAP após o lote final.
Resolver conectividade externa TCP/22 da VPS para o runner.
Fazer merge/push na main.
Ter a Etapa 8 aprovada por pessoa diferente do autor do último commit.
Executar o deploy por digest e smoke test.
Preencher neste relatório:
link da execução inicial;
link da execução final;
nome do aprovador;
data/hora;
digest implantado.
Incorporar no workbook do grupo as informações do Dia 02.
## Situação

Situação técnica antes do run final:

suíte local: 20/20;
gates 1–6 configurados em modo bloqueio;
três regras próprias Semgrep adicionadas;
Docker endurecido;
Environment de produção configurado;
exceções documentadas;
Etapa 8 implementada;
execução final e aprovação de produção ainda pendentes.

A entrega somente será considerada final após o run bloqueante, a aprovação da Etapa 8 e o registro das evidências acima.
