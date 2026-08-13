from pandas import DataFrame

from freqtrade.strategy import IStrategy

# Ideia diferente dos indicadores tecnicos classicos: aproveitar quedas
# subitas ("agulhadas") e vender assim que recupera uma percentagem.
#
# Compra quando o preco cai QUEDA_MINIMA_PARA_COMPRA (ou mais) desde o
# maximo das ultimas JANELA_MAXIMO_HORAS horas. Vende assim que o lucro
# desde a compra atinge ALVO_SUBIDA (isso e feito atraves do minimal_roi,
# nao precisa de logica extra).
QUEDA_MINIMA_PARA_COMPRA = 0.05  # 5% de queda desde o maximo recente
JANELA_MAXIMO_HORAS = 24  # "no dia" = ultimas 24 velas de 1h
ALVO_SUBIDA = 0.03  # vende ao subir 3% desde a compra


class SentinelaCompraQueda(IStrategy):
    timeframe = "1h"
    can_short = False
    stoploss = -0.10
    minimal_roi = {"0": ALVO_SUBIDA}
    use_exit_signal = False  # so ROI (ALVO_SUBIDA) e stop-loss fecham posicoes
    process_only_new_candles = True
    startup_candle_count = JANELA_MAXIMO_HORAS + 10

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["maximo_recente"] = dataframe["high"].rolling(JANELA_MAXIMO_HORAS).max()
        dataframe["queda_desde_maximo"] = (
            dataframe["maximo_recente"] - dataframe["close"]
        ) / dataframe["maximo_recente"]
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            dataframe["queda_desde_maximo"] >= QUEDA_MINIMA_PARA_COMPRA,
            "enter_long",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe
