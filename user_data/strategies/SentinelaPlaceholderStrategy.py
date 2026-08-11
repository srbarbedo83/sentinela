from pandas import DataFrame

from freqtrade.strategy import IStrategy


class SentinelaPlaceholderStrategy(IStrategy):
    """
    Estrategia temporaria da Fase 1, usada apenas para validar a instalacao
    (ligacao a exchange, dry-run, painel FreqUI). Nao gera nenhum sinal de
    compra ou venda de proposito.

    Sera substituida na Fase 2 pela estrategia real com os indicadores
    ponderados (EMA, RSI, MACD, Bandas de Bollinger, Volume/OBV).
    """

    timeframe = "1h"
    stoploss = -0.10
    minimal_roi = {"0": 0.10}

    process_only_new_candles = True
    startup_candle_count = 200

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[:, "enter_long"] = 0
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[:, "exit_long"] = 0
        return dataframe
