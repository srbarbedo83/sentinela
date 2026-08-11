# Ativa o ambiente virtual e arranca o Sentinela (Freqtrade).
# Corre com: botao direito -> "Executar com o PowerShell",
# ou dentro de uma janela do PowerShell: .\start.ps1
#
# Esta janela tem de ficar aberta enquanto quiseres que o bot corra.
# Fechar a janela (ou Ctrl+C) para o bot.

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

& ".\.venv\Scripts\Activate.ps1"

freqtrade trade `
    --config user_data\config.json `
    --strategy SentinelaPlaceholderStrategy `
    --logfile user_data\logs\freqtrade.log `
    --db-url sqlite:///user_data/tradesv3.sqlite
