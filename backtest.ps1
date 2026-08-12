# Corre um backtest da SentinelaStrategy sobre os dados historicos
# ja descarregados (ver download-data.ps1).
#
# Corre com: .\backtest.ps1

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

& ".\.venv\Scripts\Activate.ps1"

freqtrade backtesting `
    --config user_data\config.json `
    --strategy SentinelaStrategy `
    --timeframe 1h
