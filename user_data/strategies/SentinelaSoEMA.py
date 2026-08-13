import talib.abstract as ta
from pandas import DataFrame

from freqtrade.strategy import IStrategy

# Testa SO o cruzamento de medias moveis (tendencia), isolado dos outros
# indicadores, para veres se este sinal sozinho tem alguma vantagem real.
EMA_CURTA = 50
EMA_LONGA = 200


class SentinelaSoEMA(IStrategy):
    timeframe = "1h"
    can_short = False
    stoploss = -0.10
    minimal_roi = {"0": 0.10}
    use_exit_signal = False  # so ROI e stop-loss fecham posicoes
    process_only_new_candles = True
    startup_candle_count = 210

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema_curta"] = ta.EMA(dataframe, timeperiod=EMA_CURTA)
        dataframe["ema_longa"] = ta.EMA(dataframe, timeperiod=EMA_LONGA)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[dataframe["ema_curta"] > dataframe["ema_longa"], "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe
