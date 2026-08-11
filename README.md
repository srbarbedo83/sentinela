# Sentinela — Trading automatizado de criptomoedas (Freqtrade)

Sistema de trading automatizado para criptomoedas (Binance/KuCoin, spot,
sem alavancagem), baseado no [Freqtrade](https://www.freqtrade.io/),
com estratégia de indicadores técnicos ponderados, gestão de risco
rigorosa e modos automático/semi-automático. Ver `docs/` para
documentação adicional (ex. migração futura para VPS).

Este repositório está a ser construído **fase a fase**. Não avances para
os passos de uma fase seguinte sem teres concluído e validado a anterior.

## Estado atual: Fase 1 — Instalação e configuração base

Nesta fase apenas instalamos o Freqtrade via Docker no teu PC Windows e
confirmamos que o painel web (FreqUI) funciona, em **modo de simulação
(dry-run)**, sem qualquer chave API real e sem qualquer estratégia de
compra/venda ativa ainda (isso é a Fase 2).

### O que vais precisar

- Windows 10 ou 11, de preferência atualizado.
- Ligação à internet.
- Cerca de 30-40 minutos.

### Passo 1 — Instalar o Docker Desktop

1. Vai a https://www.docker.com/products/docker-desktop/ e descarrega o
   Docker Desktop para Windows.
2. Corre o instalador. Quando perguntar, deixa a opção **"Use WSL 2
   instead of Hyper-V"** ativada (é a recomendada).
3. Reinicia o PC se o instalador pedir.
4. Abre o Docker Desktop. Pode pedir para instalar componentes do WSL2 —
   segue as instruções no ecrã (normalmente basta correr `wsl --update`
   numa janela que o próprio Windows abre, ou o Docker Desktop trata
   disso sozinho).
5. Espera que o Docker Desktop mostre o estado como "Running" (ícone
   verde).

### Passo 2 — Verificar a instalação

Abre o **PowerShell** (menu Iniciar → escreve "PowerShell" → Enter) e
corre:

```powershell
docker --version
docker compose version
```

Ambos os comandos devem devolver um número de versão, sem erros.

### Passo 3 — Obter este projeto no teu PC

Se ainda não tens o Git para Windows instalado, descarrega em
https://git-scm.com/download/win (instalação com as opções por defeito).

No PowerShell, escolhe uma pasta (ex. a tua pasta pessoal) e corre:

```powershell
cd $HOME
git clone https://github.com/srbarbedo83/sentinela.git
cd sentinela
git checkout claude/freqtrade-trading-plan-plv8ks
```

### Passo 4 — Criar o teu ficheiro de configuração local

O ficheiro `user_data/config.json.example` é um modelo, sem segredos.
Copia-o para criar o teu ficheiro real (que fica sempre só no teu PC,
nunca é enviado para o GitHub — está no `.gitignore`):

```powershell
copy user_data\config.json.example user_data\config.json
```

### Passo 5 — Gerar a password e o segredo do painel web

O painel FreqUI precisa de uma password tua e de uma chave interna
aleatória (`jwt_secret_key`). Gera duas strings aleatórias no PowerShell:

```powershell
-join ((48..57)+(65..90)+(97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
-join ((48..57)+(65..90)+(97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
```

Corre o comando duas vezes (uma para cada valor). Abre
`user_data\config.json` num editor de texto (ex. Bloco de Notas) e
substitui, dentro de `"api_server"`:

- `"jwt_secret_key": "SUBSTITUIR_POR_STRING_ALEATORIA"` pela primeira
  string gerada.
- `"password": "SUBSTITUIR_POR_PASSWORD_FORTE"` pela segunda string (esta
  é a password que vais usar para entrar no painel — guarda-a num gestor
  de passwords).

Não precisas de mexer em mais nada neste ficheiro por agora. Em
particular, `exchange.key` e `exchange.secret` ficam vazios — só serão
preenchidos quando chegarmos à Fase 5 (modo real), e mesmo assim com
chaves sem permissão de levantamento.

### Passo 6 — Arrancar o Freqtrade

Ainda dentro da pasta `sentinela`, no PowerShell:

```powershell
docker compose pull
docker compose up -d
```

O primeiro comando descarrega a imagem do Freqtrade (demora um pouco na
primeira vez). O segundo arranca o bot em segundo plano.

### Passo 7 — Confirmar que está tudo a funcionar

```powershell
docker compose logs -f
```

Deves ver linhas a indicar que o bot arrancou, ligou à Binance (dados
públicos, sem chaves) e está em modo `dry_run`. Pressiona `Ctrl+C` para
sair dos logs (o bot continua a correr em segundo plano).

Abre o browser em **http://127.0.0.1:8080** — deve aparecer o ecrã de
login do FreqUI. Entra com o utilizador `sentinela` e a password que
geraste no Passo 5.

Neste ponto vais ver o painel vazio (sem trades — a estratégia
temporária desta fase não compra nada de propósito), mas o estado do bot
deve mostrar "running" e modo "Dry run".

### Para parar o bot

```powershell
docker compose down
```

E para voltar a arrancar mais tarde: `docker compose up -d` (a partir da
pasta `sentinela`).

## Próximas fases (ainda não implementadas)

2. Estratégia real com indicadores técnicos ponderados (EMA, RSI, MACD,
   Bandas de Bollinger, Volume/OBV) e votação ponderada configurável.
3. Backtesting com dados históricos.
4. Dry-run prolongado (semanas) antes de dinheiro real.
5. Modo real com €100 e risco reduzido (2-3% por operação), incluindo
   Telegram, email para alertas críticos, orçamentos por estratégia e
   registo de operações para fins fiscais (IRS).

Ver a conversa/plano combinado para o detalhe de cada fase. A migração
futura para um VPS (para correr 24/7) está documentada, mas não
implementada, em `docs/vps-migration-futura.md`.
