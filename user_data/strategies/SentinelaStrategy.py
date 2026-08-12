import talib.abstract as ta
from pandas import DataFrame

from freqtrade.strategy import IStrategy


# ============================================================================
# PESOS DOS INDICADORES E LIMIAR DE DECISAO
#
# Cada indicador "vota" a favor de comprar (positivo), a favor de vender
# (negativo) ou fica neutro (0) em cada vela. O peso abaixo multiplica esse
# voto. A soma de todos os votos ponderados e a "pontuacao":
#
#   pontuacao >= LIMIAR_DECISAO   -> sinal de COMPRA (sujeito ao filtro ADX)
#   pontuacao <= -LIMIAR_DECISAO  -> sinal de VENDA
#   caso contrario                -> nao faz nada
#
# Para dares mais importancia a um indicador, aumenta o peso dele. Para o
# desativares por completo, poe o peso a 0. Nao precisas de mexer em mais
# nada neste ficheiro para ajustar o comportamento da estrategia.
#
# NOTA: ATR e ADX nao estao nesta lista de pesos de proposito. Sao usados
# de forma diferente dos outros (ver mais abaixo) - ATR para o stop-loss
# dinamico, ADX como "filtro de regime" que liga/desliga as entradas,
# em vez de votarem a favor ou contra.
# ============================================================================
PESO_TENDENCIA_EMA = 1.0       # Cruzamento EMA curta / EMA longa
PESO_RSI = 1.0                 # RSI (sobrecompra / sobrevenda)
PESO_MACD = 1.0                # MACD
PESO_BANDAS_BOLLINGER = 1.0    # Bandas de Bollinger
PESO_VOLUME = 1.0              # Picos de volume anomalos
PESO_ICHIMOKU = 1.0            # Contexto Ichimoku (voto ja limitado a -2..+2)

# Soma minima (em valor absoluto) de votos ponderados para gerar um sinal.
# Quanto mais alto, mais indicadores precisam de concordar entre si. Com os
# pesos de partida acima, o maximo teorico da pontuacao e 7.0 (EMA, RSI,
# MACD, Bollinger e Volume contribuem ate 1 cada; Ichimoku ate 2). Este
# valor de partida (4.0) e so um ponto de partida - ajusta-o com base nos
# resultados do backtest, tal como o resto.
LIMIAR_DECISAO = 4.0

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

ICHIMOKU_TENKAN = 9
ICHIMOKU_KIJUN = 26
ICHIMOKU_SENKOU_B = 52
ICHIMOKU_DESLOCAMENTO = 26  # deslocamento da nuvem (Kumo), padrao tradicional

# ADX nao vota no score - funciona como "filtro de regime": abaixo deste
# valor, o mercado e considerado sem tendencia definida e NAO SE ABREM
# posicoes novas, seja qual for a pontuacao dos outros indicadores. Serve
# de referencia (nao usado diretamente no codigo):
#   ADX < 20    mercado fraco / lateral
#   20-25       transicao
#   25-35       tendencia interessante
#   > 35        tendencia forte
# Testa este valor no backtest antes de o dares como definitivo.
ADX_PERIODO = 14
ADX_LIMIAR_MINIMO = 20

# ATR tambem nao vota no score - alimenta o stop-loss dinamico (ver
# custom_stoploss mais abaixo): quanto mais volatil o mercado, mais largo
# o stop; quanto mais calmo, mais apertado. Fica sempre limitado entre
# ATR_STOPLOSS_MINIMO (nunca mais apertado do que isto, mesmo em mercados
# muito calmos - ATR de 1h sozinho e demasiado pequeno para servir de
# stop direto) e o `stoploss` fixo definido na classe (nunca mais largo
# do que isto - rede de seguranca final, sem excecao).
#
# USAR_STOP_DINAMICO_ATR: poe a False para desligar o stop dinamico e
# voltares ao stoploss fixo (-10%) em todas as posicoes - util para
# comparares em backtest se o stop dinamico esta a ajudar ou a atrapalhar,
# sem precisares de apagar codigo.
USAR_STOP_DINAMICO_ATR = True
ATR_PERIODO = 14
ATR_STOPLOSS_MULTIPLICADOR = 3.0
ATR_STOPLOSS_MINIMO = 0.03  # nunca mais apertado que 3%, seja qual for o ATR


class SentinelaStrategy(IStrategy):
    """
    Estrategia de votacao ponderada entre indicadores tecnicos, com um
    filtro de regime (ADX) e stop-loss dinamico (ATR).

    Ajusta os pesos, o LIMIAR_DECISAO e o ADX_LIMIAR_MINIMO no topo deste
    ficheiro para mudares o comportamento, sem tocar no resto do codigo.
    """

    INTERFACE_VERSION = 3

    # Timeframe de analise - muda livremente (ex. "1m", "5m", "15m", "30m", "1h").
    timeframe = "1h"

    # Nunca vender a descoberto - alinhado com spot, sem alavancagem.
    can_short = False

    # Valores de partida conservadores; revistos em detalhe na fase de
    # gestao de risco (stake sizing, limites diarios). O stoploss aqui e
    # sempre o limite maximo absoluto - o stop dinamico do ATR nunca o
    # ultrapassa (ver custom_stoploss).
    stoploss = -0.10
    minimal_roi = {"0": 0.10}

    # Ativa o stop-loss dinamico baseado em ATR (ver custom_stoploss).
    use_custom_stoploss = True

    # DESLIGADO DE PROPOSITO PARA TESTE: em todos os backtests feitos ate
    # agora, a saida por sinal contrario (populate_exit_trend, tag
    # "votacao_ponderada") teve sempre uma taxa de acerto muito baixa
    # (~16-17%) e perda media de ~-2.6% - sistematicamente pior do que as
    # saidas por ROI ou stop-loss. Hipotese: o sinal de saida exige tanta
    # concordancia como o de entrada, por isso chega tarde, depois do
    # preco ja ter virado contra a posicao. Com isto a False, so o ROI e
    # o stop-loss fecham posicoes - populate_exit_trend fica no codigo,
    # mas ignorado, para testarmos a diferenca. Poe a True para reativar.
    use_exit_signal = False

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

        # --- Volatilidade (voto): Bandas de Bollinger ---
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

        # --- Contexto: Ichimoku (Tenkan, Kijun, nuvem/Kumo) ---
        dataframe["ichimoku_tenkan"] = (
            dataframe["high"].rolling(ICHIMOKU_TENKAN).max()
            + dataframe["low"].rolling(ICHIMOKU_TENKAN).min()
        ) / 2
        dataframe["ichimoku_kijun"] = (
            dataframe["high"].rolling(ICHIMOKU_KIJUN).max()
            + dataframe["low"].rolling(ICHIMOKU_KIJUN).min()
        ) / 2
        senkou_a = (dataframe["ichimoku_tenkan"] + dataframe["ichimoku_kijun"]) / 2
        senkou_b = (
            dataframe["high"].rolling(ICHIMOKU_SENKOU_B).max()
            + dataframe["low"].rolling(ICHIMOKU_SENKOU_B).min()
        ) / 2
        # A nuvem e projetada para a frente - por isso o desvio (shift).
        dataframe["ichimoku_senkou_a"] = senkou_a.shift(ICHIMOKU_DESLOCAMENTO)
        dataframe["ichimoku_senkou_b"] = senkou_b.shift(ICHIMOKU_DESLOCAMENTO)

        # --- Regime: ADX (forca da tendencia, nao a direcao) ---
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=ADX_PERIODO)
        dataframe["regime_com_tendencia"] = dataframe["adx"] > ADX_LIMIAR_MINIMO

        # --- Risco: ATR (usado no stop-loss dinamico, nao no score) ---
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=ATR_PERIODO)

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

        # Ichimoku: 3 sub-condicoes simples somadas, depois limitadas (clip)
        # a -2..+2 - para nao deixar este indicador, sozinho, dominar a
        # pontuacao final so por ter varias componentes internas.
        nuvem_topo = dataframe[["ichimoku_senkou_a", "ichimoku_senkou_b"]].max(axis=1)
        nuvem_base = dataframe[["ichimoku_senkou_a", "ichimoku_senkou_b"]].min(axis=1)

        dataframe["ichimoku_voto_preco_nuvem"] = 0
        dataframe.loc[dataframe["close"] > nuvem_topo, "ichimoku_voto_preco_nuvem"] = 1
        dataframe.loc[dataframe["close"] < nuvem_base, "ichimoku_voto_preco_nuvem"] = -1

        dataframe["ichimoku_voto_tenkan_kijun"] = 0
        dataframe.loc[
            dataframe["ichimoku_tenkan"] > dataframe["ichimoku_kijun"],
            "ichimoku_voto_tenkan_kijun",
        ] = 1
        dataframe.loc[
            dataframe["ichimoku_tenkan"] < dataframe["ichimoku_kijun"],
            "ichimoku_voto_tenkan_kijun",
        ] = -1

        dataframe["ichimoku_voto_chikou"] = 0
        dataframe.loc[
            dataframe["close"] > dataframe["close"].shift(ICHIMOKU_DESLOCAMENTO),
            "ichimoku_voto_chikou",
        ] = 1
        dataframe.loc[
            dataframe["close"] < dataframe["close"].shift(ICHIMOKU_DESLOCAMENTO),
            "ichimoku_voto_chikou",
        ] = -1

        dataframe["voto_ichimoku"] = (
            dataframe["ichimoku_voto_preco_nuvem"]
            + dataframe["ichimoku_voto_tenkan_kijun"]
            + dataframe["ichimoku_voto_chikou"]
        ).clip(-2, 2)

        # ------------------------------------------------------------------
        # Pontuacao final: soma dos votos, cada um multiplicado pelo seu peso
        # ------------------------------------------------------------------
        dataframe["pontuacao"] = (
            dataframe["voto_ema"] * PESO_TENDENCIA_EMA
            + dataframe["voto_rsi"] * PESO_RSI
            + dataframe["voto_macd"] * PESO_MACD
            + dataframe["voto_bollinger"] * PESO_BANDAS_BOLLINGER
            + dataframe["voto_volume"] * PESO_VOLUME
            + dataframe["voto_ichimoku"] * PESO_ICHIMOKU
        )

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # O filtro de regime (ADX) so permite entradas quando ha tendencia
        # suficiente - mesmo que a pontuacao dos outros indicadores atinja
        # o limiar, sem isto nao se abre posicao.
        condicao_entrada = (dataframe["pontuacao"] >= LIMIAR_DECISAO) & dataframe[
            "regime_com_tendencia"
        ]
        dataframe.loc[condicao_entrada, ["enter_long", "enter_tag"]] = (1, "votacao_ponderada")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # As saidas NAO ficam sujeitas ao filtro de regime - queremos
        # poder sair de uma posicao a qualquer momento, tendencia ou nao.
        dataframe.loc[
            dataframe["pontuacao"] <= -LIMIAR_DECISAO,
            ["exit_long", "exit_tag"],
        ] = (1, "votacao_ponderada")
        return dataframe

    def custom_stoploss(
        self, pair: str, trade, current_time, current_rate: float, current_profit: float, **kwargs
    ) -> float:
        """
        Stop-loss dinamico baseado no ATR: mais apertado em mercados
        calmos, mais largo em mercados volateis - mas sempre dentro dos
        limites ATR_STOPLOSS_MINIMO..stoploss definidos acima. Sem este
        limite minimo, um ATR de 1h sozinho da uma distancia demasiado
        pequena e o stop dispara por ruido normal do mercado, nao por
        reversao real (foi exatamente isto que o backtest revelou).
        """
        if not USAR_STOP_DINAMICO_ATR:
            return self.stoploss

        dataframe, _ = self.dp.get_analyzed_dataframe(pair=pair, timeframe=self.timeframe)
        if dataframe is None or dataframe.empty:
            return self.stoploss

        atr_atual = dataframe["atr"].iat[-1]
        if atr_atual is None or atr_atual <= 0 or trade.open_rate <= 0:
            return self.stoploss

        distancia_atr = (atr_atual * ATR_STOPLOSS_MULTIPLICADOR) / trade.open_rate
        distancia_atr = max(distancia_atr, ATR_STOPLOSS_MINIMO)  # nunca mais apertado que o minimo

        # max() entre dois numeros negativos devolve o mais proximo de
        # zero (o mais apertado) - por isso isto garante que o resultado
        # nunca fica mais LARGO do que o stoploss fixo (-10% por
        # defeito), que assim continua a ser o limite maximo absoluto.
        return max(-distancia_atr, self.stoploss)
