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
particular, `exchange.key` e `exchange.secret` ficam vazios — só serão
preenchidos quando chegarmos à Fase 5 (modo real), e mesmo assim com
chaves sem permissão de levantamento.

### Passo 8 — Arrancar o Freqtrade

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

### Passo 9 — Confirmar no painel

Com o `start.ps1` a correr, abre o browser em **http://127.0.0.1:8080**
— deve aparecer o ecrã de login do FreqUI. Entra com o utilizador
`sentinela` e a password que geraste no Passo 7.

Neste ponto vais ver o painel vazio (sem trades — a estratégia
temporária desta fase não compra nada de propósito), mas o estado do bot
deve mostrar "running" e modo "Dry run".

### Para parar o bot

Volta à janela do PowerShell onde correste `start.ps1` e pressiona
`Ctrl+C`. Para arrancar de novo mais tarde, repete o Passo 8 (não
precisas de repetir os passos de instalação).

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
