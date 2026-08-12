# Sentinela — Trading automatizado de criptomoedas (Freqtrade)

Sistema de trading automatizado para criptomoedas (Binance/KuCoin, spot,
sem alavancagem), baseado no [Freqtrade](https://www.freqtrade.io/),
com estratégia de indicadores técnicos ponderados, gestão de risco
rigorosa e modos automático/semi-automático. Ver `docs/` para
documentação adicional (ex. migração futura para VPS).

Este repositório está a ser construído **fase a fase**. Não avances para
os passos de uma fase seguinte sem teres concluído e validado a anterior.

## Estado atual: Fase 1 — Instalação e configuração base

Nesta fase instalamos o Freqtrade diretamente no teu PC Windows (sem
Docker, sem WSL2, sem mexer em virtualização na BIOS) e confirmamos que o
painel web (FreqUI) funciona, em **modo de simulação (dry-run)**, sem
qualquer chave API real e sem qualquer estratégia de compra/venda ativa
ainda (isso é a Fase 2).

**Nota importante desta via (sem Docker):** o bot só corre enquanto a
janela do PowerShell onde o arrancaste estiver aberta. Não há um serviço
em segundo plano automático como haveria com Docker — fechar a janela (ou
desligar o PC) para o bot. Isto é coerente com o que já combinámos: aceitas
perder sinais quando o PC está desligado nesta fase.

### O que vais precisar

- Windows 10 ou 11, de preferência atualizado.
- Ligação à internet.
- Cerca de 30-40 minutos.

### Passo 1 — Confirmar o Python

Já tens o Python 3.13 instalado — serve perfeitamente, não precisas de
instalar o 3.11 nem nenhuma outra versão. O Freqtrade e o TA-Lib (Passo 5)
já suportam o 3.13 diretamente, com instalação pré-compilada.

### Passo 2 — Verificar a instalação

Abre o **PowerShell** (menu Iniciar → escreve "PowerShell" → Enter) e
corre:

```powershell
python --version
python -m pip --version
```

Deves ver `Python 3.13.x` e um número de versão do pip, sem erros.
Usamos sempre `python -m pip` em vez de `pip` sozinho — funciona mesmo
que o `pip` não esteja diretamente no PATH do Windows.

### Passo 3 — Obter este projeto no teu PC

Se ainda não tens o Git para Windows instalado, descarrega em
https://git-scm.com/download/win (instalação com as opções por defeito).

Já criaste a pasta `D:\Projetos\sentinela` — usa-a:

```powershell
cd D:\Projetos\sentinela
git clone https://github.com/srbarbedo83/sentinela.git .
git checkout claude/freqtrade-trading-plan-plv8ks
```

### Passo 4 — Criar e ativar o ambiente virtual

Um "ambiente virtual" é só uma pasta isolada onde o Freqtrade e as suas
dependências ficam instalados, sem misturar com o resto do teu sistema.

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

- O `Set-ExecutionPolicy ... -Scope Process` só afeta esta janela do
  PowerShell (não é uma alteração permanente ao sistema) e é necessário
  porque o Windows bloqueia scripts `.ps1` por defeito.
- Depois de ativado, o início da linha no PowerShell passa a mostrar
  `(.venv)` — é assim que sabes que está ativo. **Sempre que abrires uma
  nova janela do PowerShell para mexer no projeto, repete o
  `.venv\Scripts\Activate.ps1`** (a partir da pasta do projeto).

### Passo 5 — Instalar o TA-Lib e o Freqtrade

Com o ambiente virtual ativo (`(.venv)` visível):

```powershell
python -m pip install --upgrade pip
python -m pip install TA-Lib
python -m pip install freqtrade
```

O `TA-Lib` é a biblioteca que calcula os indicadores técnicos (EMA, RSI,
MACD, etc.). Para Python 3.13 no Windows já existe um pacote
pré-compilado, por isso o `pip install TA-Lib` deve simplesmente
funcionar, sem precisar de compilar nada. Se ainda assim falhar, avisa-me
com a mensagem de erro.

Confirma no fim:

```powershell
freqtrade --version
```

### Passo 6 — Criar o teu ficheiro de configuração local

O ficheiro `user_data/config.json.example` é um modelo, sem segredos.
Copia-o para criar o teu ficheiro real (que fica sempre só no teu PC,
nunca é enviado para o GitHub — está no `.gitignore`):

```powershell
copy user_data\config.json.example user_data\config.json
```

### Passo 7 — Gerar a password e o segredo do painel web

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
particular, `exchange.key` e `exchange.secret` ficam com valores de
preenchimento óbviamente falsos (`dryrun-placeholder-key` /
`dryrun-placeholder-secret`) — o CCXT exige que estes campos não estejam
vazios mesmo só para consultar dados públicos, mas o seu conteúdo não
importa em dry-run. As tuas chaves reais só serão preenchidas quando
chegarmos à Fase 5 (modo real), e mesmo assim sem permissão de
levantamento.

### Passo 8 — Instalar o painel (FreqUI)

O painel web não vem instalado por defeito — é um passo à parte. Com o
ambiente virtual ativo (`(.venv)` visível):

```powershell
freqtrade install-ui
```

### Passo 9 — Arrancar o Freqtrade

O repositório já tem um script `start.ps1` que ativa o ambiente virtual e
arranca o bot com a configuração certa. A partir da pasta do projeto:

```powershell
.\start.ps1
```

Se o PowerShell recusar correr o script (erro sobre "execution
policy"), corre primeiro `Set-ExecutionPolicy -Scope Process
-ExecutionPolicy Bypass` nessa janela e tenta de novo.

Esta janela fica "presa" a mostrar os logs do bot em direto — é normal,
é assim que sabes que está a correr. Deves ver linhas a indicar que o bot
arrancou, ligou à Binance (dados públicos, sem chaves) e está em modo
`dry_run`.

### Passo 10 — Confirmar no painel

Com o `start.ps1` a correr, abre o browser em **http://127.0.0.1:8080**
— deve aparecer o ecrã de login do FreqUI. Entra com o utilizador
`sentinela` e a password que geraste no Passo 7.

Neste ponto vais ver o painel vazio (sem trades — a estratégia
temporária desta fase não compra nada de propósito), mas o estado do bot
deve mostrar "running" e modo "Dry run".

### Para parar o bot

Volta à janela do PowerShell onde correste `start.ps1` e pressiona
`Ctrl+C`. Para arrancar de novo mais tarde, repete o Passo 9 (não
precisas de repetir os passos de instalação, incluindo o `install-ui`).

## Fase 2 — Estratégia com indicadores ponderados

O ficheiro `user_data/strategies/SentinelaStrategy.py` implementa uma
votação ponderada entre indicadores técnicos. **Todos os pesos e limiares
estão isolados num único bloco no topo do ficheiro**, com comentários em
português — é aí que ajustas o comportamento, sem precisares de mexer no
resto do código. Estrutura em três camadas:

- **Votos ponderados** (entram na pontuação): EMA 50/200 (tendência),
  RSI (momentum), MACD (momentum/tendência), Bandas de Bollinger
  (volatilidade), picos de volume, e Ichimoku (Tenkan/Kijun/nuvem, como
  voto de contexto limitado a ±2 para não dominar os outros).
- **Filtro de regime** (não entra na pontuação): ADX — só permite abrir
  posições novas quando há tendência suficiente no mercado, mesmo que a
  pontuação dos outros indicadores atinja o limiar. Não afeta saídas.
- **Gestão de risco** (não entra na pontuação): ATR — alimenta um
  stop-loss dinâmico (mais apertado em mercados calmos, mais largo em
  mercados voláteis), sempre limitado pelo `stoploss` fixo definido na
  estratégia, que continua obrigatório sem exceção em qualquer posição.

Esta estratégia ainda não está a correr (o `start.ps1` continua a usar a
`SentinelaPlaceholderStrategy` da Fase 1, que não compra nada). Antes de
a pormos a correr, mesmo em dry-run, vamos validá-la com dados
históricos reais — isso é a Fase 3 (backtesting), a seguir.

## Fase 3 — Backtesting

Testar a estratégia contra dados históricos reais, sem dinheiro nenhum
envolvido (nem sequer simulado em tempo real — é só matemática sobre o
passado).

### Passo 1 — Descarregar dados históricos

```powershell
.\download-data.ps1
```

Descarrega 180 dias (~6 meses) de velas de 1 hora para os 4 pares
(`BTC/USDT`, `ETH/USDT`, `SOL/USDT`, `PENDLE/USDT`) diretamente da
Binance, usando as ferramentas nativas do Freqtrade. Fica guardado em
`user_data/data/binance/` (não vai para o Git — é só dados, recriáveis a
qualquer momento).

### Passo 2 — Correr o backtest

```powershell
.\backtest.ps1
```

No final, o Freqtrade imprime uma tabela-resumo por par e uma tabela
total. As colunas mais importantes:

- **Trades** — quantas operações a estratégia teria feito.
- **Tot Profit %** — resultado total no período, em percentagem.
- **Win %** — percentagem de operações fechadas com lucro.
- **Avg Duration** — duração média de cada operação.
- **Max Drawdown** — a maior queda (pico a vale) da carteira simulada
  durante o período. É um dos números mais importantes para avaliar
  risco, não só retorno.

### Passo 3 — Ajustar e repetir

Se os resultados não parecerem bons (poucas operações, drawdown muito
alto, prejuízo), volta a `user_data/strategies/SentinelaStrategy.py`,
ajusta os pesos ou o `LIMIAR_DECISAO`, e corre `.\backtest.ps1` outra
vez — não precisas de descarregar os dados de novo, só repetir este
passo. Isto é normal e esperado: a Fase 3 existe exatamente para
experimentar antes de arriscar dinheiro, mesmo simulado.

**Nota importante:** um bom resultado em backtesting não garante nada
sobre o futuro — serve para eliminar estratégias claramente más antes de
gastarmos semanas em dry-run. A validação a sério vem nas Fases 4 e 5.

## Próximas fases (ainda não implementadas)

4. Dry-run prolongado (semanas) antes de dinheiro real.
5. Modo real com €100 e risco reduzido (2-3% por operação), incluindo
   Telegram, email para alertas críticos, orçamentos por estratégia e
   registo de operações para fins fiscais (IRS).

Ver a conversa/plano combinado para o detalhe de cada fase. A migração
futura para um VPS (para correr 24/7) está documentada, mas não
implementada, em `docs/vps-migration-futura.md`.
