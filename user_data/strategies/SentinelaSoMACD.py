import talib.abstract as ta
from pandas import DataFrame

from freqtrade.strategy import IStrategy

# Testa SO o MACD (momentum/tendencia), isolado dos outros indicadores.
MACD_RAPIDA = 12
MACD_LENTA = 26
MACD_SINAL = 9


class SentinelaSoMACD(IStrategy):
    timeframe = "1h"
    can_short = False
    stoploss = -0.10
    minimal_roi = {"0": 0.10}
    use_exit_signal = False
    process_only_new_candles = True
    startup_candle_count = 210

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        macd = ta.MACD(
            dataframe,
            fastperiod=MACD_RAPIDA,
            slowperiod=MACD_LENTA,
            signalperiod=MACD_SINAL,
        )
        dataframe["macd"] = macd["macd"]
        dataframe["macdsignal"] = macd["macdsignal"]
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[dataframe["macd"] > dataframe["macdsignal"], "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe
