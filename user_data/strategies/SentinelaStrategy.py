import talib.abstract as ta
from pandas import DataFrame

from freqtrade.strategy import IStrategy


# ============================================================================
# PESOS DOS INDICADORES E LIMIAR DE DECISAO
#
# Cada indicador "vota" +1 (a favor de comprar), -1 (a favor de vender) ou
# 0 (neutro) em cada vela. O peso abaixo multiplica esse voto. A soma de
# todos os votos ponderados é a "pontuacao":
#
#   pontuacao >= LIMIAR_DECISAO   -> sinal de COMPRA
#   pontuacao <= -LIMIAR_DECISAO  -> sinal de VENDA
#   caso contrario                -> nao faz nada
#
# Para dares mais importancia a um indicador, aumenta o peso dele. Para o
# desativares por completo, poe o peso a 0. Nao precisas de mexer em mais
# nada neste ficheiro para ajustar o comportamento da estrategia.
# ============================================================================
PESO_TENDENCIA_EMA = 1.0       # Cruzamento EMA curta / EMA longa
PESO_RSI = 1.0                 # RSI (sobrecompra / sobrevenda)
PESO_MACD = 1.0                # MACD
PESO_BANDAS_BOLLINGER = 1.0    # Bandas de Bollinger
PESO_VOLUME = 1.0              # Picos de volume anomalos

# Soma minima (em valor absoluto) de votos ponderados para gerar um sinal.
# Quanto mais alto, mais indicadores precisam de concordar entre si.
# Com os 5 pesos a 1.0 acima, o maximo possivel e 5.0 (todos a votar no
# mesmo sentido) e o minimo para gerar sinal com este LIMIAR e "3 de 5"
# indicadores concordarem.
LIMIAR_DECISAO = 3.0

# ============================================================================
# PARAMETROS DE CADA INDICADOR
# ============================================================================
EMA_CURTA = 50
EMA_LONGA = 200

RSI_PERIODO = 14
RSI_SOBRECOMPRA = 70
RSI_SOBREVENDA = 30

MACD_RAPIDA = 12
MACD_LENTA = 26
MACD_SINAL = 9

BOLLINGER_PERIODO = 20
BOLLINGER_DESVIO = 2.0

VOLUME_MEDIA_PERIODO = 20
VOLUME_MULTIPLICADOR_PICO = 1.5  # volume > media * este valor conta como "pico"


class SentinelaStrategy(IStrategy):
    """
    Estrategia de votacao ponderada entre 5 indicadores tecnicos.
    Ajusta os pesos e o LIMIAR_DECISAO no topo deste ficheiro para
    mudares o comportamento, sem tocar no resto do codigo.
    """

    INTERFACE_VERSION = 3

    # Timeframe de analise - muda livremente (ex. "1m", "5m", "15m", "30m", "1h").
    timeframe = "1h"

    # Nunca vender a descoberto - alinhado com spot, sem alavancagem.
    can_short = False

    # Valores de partida conservadores; revistos em detalhe na fase de
    # gestao de risco (stake sizing, stop-loss, limites diarios).
    stoploss = -0.10
    minimal_roi = {"0": 0.10}

    process_only_new_candles = True
    startup_candle_count = 210  # cobre a EMA mais longa (200) com margem

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # --- Tendencia: cruzamento de medias moveis ---
        dataframe["ema_curta"] = ta.EMA(dataframe, timeperiod=EMA_CURTA)
        dataframe["ema_longa"] = ta.EMA(dataframe, timeperiod=EMA_LONGA)

        # --- Momentum: RSI ---
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=RSI_PERIODO)

        # --- Momentum/tendencia: MACD ---
        macd = ta.MACD(
            dataframe,
            fastperiod=MACD_RAPIDA,
            slowperiod=MACD_LENTA,
            signalperiod=MACD_SINAL,
        )
        dataframe["macd"] = macd["macd"]
        dataframe["macdsignal"] = macd["macdsignal"]

        # --- Volatilidade: Bandas de Bollinger ---
        bollinger = ta.BBANDS(
            dataframe,
            timeperiod=BOLLINGER_PERIODO,
            nbdevup=BOLLINGER_DESVIO,
            nbdevdn=BOLLINGER_DESVIO,
        )
        dataframe["bb_superior"] = bollinger["upperband"]
        dataframe["bb_inferior"] = bollinger["lowerband"]

        # --- Volume: deteção de picos anomalos ---
        dataframe["volume_media"] = dataframe["volume"].rolling(VOLUME_MEDIA_PERIODO).mean()
        dataframe["volume_pico"] = dataframe["volume"] > (
            dataframe["volume_media"] * VOLUME_MULTIPLICADOR_PICO
        )

        # ------------------------------------------------------------------
        # Voto individual de cada indicador: +1 compra, -1 venda, 0 neutro
        # ------------------------------------------------------------------
        dataframe["voto_ema"] = 0
        dataframe.loc[dataframe["ema_curta"] > dataframe["ema_longa"], "voto_ema"] = 1
        dataframe.loc[dataframe["ema_curta"] < dataframe["ema_longa"], "voto_ema"] = -1

        dataframe["voto_rsi"] = 0
        dataframe.loc[dataframe["rsi"] < RSI_SOBREVENDA, "voto_rsi"] = 1
        dataframe.loc[dataframe["rsi"] > RSI_SOBRECOMPRA, "voto_rsi"] = -1

        dataframe["voto_macd"] = 0
        dataframe.loc[dataframe["macd"] > dataframe["macdsignal"], "voto_macd"] = 1
        dataframe.loc[dataframe["macd"] < dataframe["macdsignal"], "voto_macd"] = -1

        dataframe["voto_bollinger"] = 0
        dataframe.loc[dataframe["close"] <= dataframe["bb_inferior"], "voto_bollinger"] = 1
        dataframe.loc[dataframe["close"] >= dataframe["bb_superior"], "voto_bollinger"] = -1

        dataframe["voto_volume"] = 0
        dataframe.loc[
            dataframe["volume_pico"] & (dataframe["close"] > dataframe["close"].shift(1)),
            "voto_volume",
        ] = 1
        dataframe.loc[
            dataframe["volume_pico"] & (dataframe["close"] < dataframe["close"].shift(1)),
            "voto_volume",
        ] = -1

        # ------------------------------------------------------------------
        # Pontuacao final: soma dos votos, cada um multiplicado pelo seu peso
        # ------------------------------------------------------------------
        dataframe["pontuacao"] = (
            dataframe["voto_ema"] * PESO_TENDENCIA_EMA
            + dataframe["voto_rsi"] * PESO_RSI
            + dataframe["voto_macd"] * PESO_MACD
            + dataframe["voto_bollinger"] * PESO_BANDAS_BOLLINGER
            + dataframe["voto_volume"] * PESO_VOLUME
        )

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            dataframe["pontuacao"] >= LIMIAR_DECISAO,
            ["enter_long", "enter_tag"],
        ] = (1, "votacao_ponderada")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            dataframe["pontuacao"] <= -LIMIAR_DECISAO,
            ["exit_long", "exit_tag"],
        ] = (1, "votacao_ponderada")
        return dataframe
