from pandas import DataFrame

from freqtrade.strategy import IStrategy

# Testa SO os picos de volume anomalos, isolado dos outros indicadores:
# compra quando ha um pico de volume com o preco a subir.
VOLUME_MEDIA_PERIODO = 20
VOLUME_MULTIPLICADOR_PICO = 1.5


class SentinelaSoVolume(IStrategy):
    timeframe = "1h"
    can_short = False
    stoploss = -0.10
    minimal_roi = {"0": 0.10}
    use_exit_signal = False
    process_only_new_candles = True
    startup_candle_count = 210

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["volume_media"] = dataframe["volume"].rolling(VOLUME_MEDIA_PERIODO).mean()
        dataframe["volume_pico"] = dataframe["volume"] > (
            dataframe["volume_media"] * VOLUME_MULTIPLICADOR_PICO
        )
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            dataframe["volume_pico"] & (dataframe["close"] > dataframe["close"].shift(1)),
            "enter_long",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe
