import talib.abstract as ta
from pandas import DataFrame

from freqtrade.strategy import IStrategy

# Testa SO o RSI (momentum/sobrevenda), isolado dos outros indicadores.
RSI_PERIODO = 14
RSI_SOBREVENDA = 30


class SentinelaSoRSI(IStrategy):
    timeframe = "1h"
    can_short = False
    stoploss = -0.10
    minimal_roi = {"0": 0.10}
    use_exit_signal = False
    process_only_new_candles = True
    startup_candle_count = 210

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=RSI_PERIODO)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[dataframe["rsi"] < RSI_SOBREVENDA, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe
