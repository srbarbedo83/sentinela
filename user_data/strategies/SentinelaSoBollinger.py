import talib.abstract as ta
from pandas import DataFrame

from freqtrade.strategy import IStrategy

# Testa SO as Bandas de Bollinger (volatilidade), isolado dos outros
# indicadores: compra quando o preco toca a banda inferior.
BOLLINGER_PERIODO = 20
BOLLINGER_DESVIO = 2.0


class SentinelaSoBollinger(IStrategy):
    timeframe = "1h"
    can_short = False
    stoploss = -0.10
    minimal_roi = {"0": 0.10}
    use_exit_signal = False
    process_only_new_candles = True
    startup_candle_count = 210

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        bollinger = ta.BBANDS(
            dataframe,
            timeperiod=BOLLINGER_PERIODO,
            nbdevup=BOLLINGER_DESVIO,
            nbdevdn=BOLLINGER_DESVIO,
        )
        dataframe["bb_inferior"] = bollinger["lowerband"]
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[dataframe["close"] <= dataframe["bb_inferior"], "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe
