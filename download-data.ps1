# Descarrega dados historicos da Binance para os pares configurados no
# config.json, para usar no backtesting (Fase 3).
#
# Corre com: .\download-data.ps1
# Repete sempre que quiseres dados mais recentes.

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

& ".\.venv\Scripts\Activate.ps1"

freqtrade download-data `
    --config user_data\config.json `
    --timeframe 1h `
    --days 365
