from .candle_engine import CandleEngine
from .pattern_engine import PatternEngine
from .structure_engine import StructureEngine
from .historical_engine import HistoricalEngine
from .risk_engine import RiskEngine


class AnalysisEngine:
    """
    Central analysis engine.

    Combines:
    - Multi-timeframe candle data
    - Candlestick patterns
    - Market structure
    - Historical setup statistics
    - Trade-plan generation
    """

    def __init__(self, deriv_client):

        self.deriv = deriv_client

        self.candles = CandleEngine(
            deriv_client
        )

        self.patterns = PatternEngine()

        self.structure = StructureEngine()

        self.history = HistoricalEngine()

        self.risk = RiskEngine()

    def analyze_market(
        self,
        symbol,
        market_name=None,
        candle_count=200
    ):
        """
        Run complete multi-timeframe analysis.
        """

        market_name = market_name or symbol

        try:

            data = self.candles.get_multi_timeframe_data(
                symbol=symbol,
                count=candle_count
            )

        except Exception as error:

            return {
                "success": False,
                "message": f"Candle engine error: {error}",
                "market": market_name,
                "symbol": symbol
            }

        # -----------------------------------------
        # Validate candle engine response
        # -----------------------------------------

        if not data or not isinstance(data, dict):

            return {
                "success": False,
                "message": "No market data returned",
                "market": market_name,
                "symbol": symbol
            }

        if not data.get("success"):

            return {
                "success": False,
                "message": data.get(
                    "message",
                    "No market data returned"
                ),
                "market": market_name,
                "symbol": symbol
            }

        # -----------------------------------------
        # Get timeframe data
        # -----------------------------------------

        timeframes = data.get(
            "timeframes",
            {}
        )

        if not isinstance(timeframes, dict):

            return {
                "success": False,
                "message": "Invalid timeframe data",
                "market": market_name,
                "symbol": symbol
            }

        timeframe_results = {}

        # -----------------------------------------
        # Analyze each timeframe
        # -----------------------------------------

        for timeframe in [
            "H1",
            "M30",
            "M5"
        ]:

            timeframe_data = timeframes.get(
                timeframe
            )

            if not timeframe_data:

                timeframe_results[timeframe] = {
                    "success": False,
                    "message": "No timeframe data",
                    "candles": [],
                    "patterns": [],
                    "structure": {}
                }

                continue

            if not isinstance(
                timeframe_data,
                dict
            ):

                timeframe_results[timeframe] = {
                    "success": False,
                    "message": "Invalid timeframe response",
                    "candles": [],
                    "patterns": [],
                    "structure": {}
                }

                continue

            if not timeframe_data.get(
                "success"
            ):

                timeframe_results[timeframe] = {
                    **timeframe_data,
                    "patterns": [],
                    "structure": {}
                }

                continue

            candles = timeframe_data.get(
                "candles",
                []
            )

            if not isinstance(
                candles,
                list
            ):

                candles = []

            if len(candles) < 10:

                timeframe_results[timeframe] = {
                    "success": False,
                    "message": "Not enough candles",
                    "candles": candles,
                    "patterns": [],
                    "structure": {}
                }

                continue

            # -------------------------------------
            # Pattern analysis
            # -------------------------------------

            try:

                detected_patterns = (
                    self.patterns.analyze(
                        candles
                    )
                )

            except Exception as error:

                detected_patterns = []

            if not isinstance(
                detected_patterns,
                list
            ):

                detected_patterns = []

            # -------------------------------------
            # Structure analysis
            # -------------------------------------

            try:

                structure = (
                    self.structure.analyze(
                        candles
                    )
                )

            except Exception as error:

                structure = {
                    "trend": "UNKNOWN",
                    "error": str(error)
                }

            if not isinstance(
                structure,
                dict
            ):

                structure = {
                    "trend": "UNKNOWN"
                }

            # -------------------------------------
            # Store timeframe result
            # -------------------------------------

            timeframe_results[timeframe] = {

                "success": True,

                "candles": candles,

                "latest_price": candles[-1]["close"],

                "patterns": detected_patterns[-20:],

                "structure": structure
            }

        # -----------------------------------------
        # Return complete analysis
        # -----------------------------------------

        return {

            "success": True,

            "market": market_name,

            "symbol": symbol,

            "timeframes": timeframe_results
        }

    def determine_direction(
        self,
        analysis
    ):
        """
        Determine overall direction using
        H1, M30 and M5 structure.
        """

        if not analysis or not isinstance(
            analysis,
            dict
        ):
            return "WAIT"

        timeframes = analysis.get(
            "timeframes",
            {}
        )

        if not isinstance(
            timeframes,
            dict
        ):
            return "WAIT"

        h1 = timeframes.get(
            "H1",
            {}
        )

        m30 = timeframes.get(
            "M30",
            {}
        )

        m5 = timeframes.get(
            "M5",
            {}
        )

        h1_trend = (
            h1.get(
                "structure",
                {}
            ).get(
                "trend",
                "UNKNOWN"
            )
        )

        m30_trend = (
            m30.get(
                "structure",
                {}
            ).get(
                "trend",
                "UNKNOWN"
            )
        )

        m5_trend = (
            m5.get(
                "structure",
                {}
            ).get(
                "trend",
                "UNKNOWN"
            )
        )

        bullish = 0
        bearish = 0

        for trend in [
            h1_trend,
            m30_trend,
            m5_trend
        ]:

            if trend == "BULLISH":

                bullish += 1

            elif trend == "BEARISH":

                bearish += 1

        if (
            bullish >= 2
            and bullish > bearish
        ):

            return "BUY"

        if (
            bearish >= 2
            and bearish > bullish
        ):

            return "SELL"

        return "WAIT"

    def calculate_confidence(
        self,
        analysis,
        direction
    ):
        """
        Calculate confidence score.
        """

        if direction == "WAIT":

            return 0.0

        if not analysis or not isinstance(
            analysis,
            dict
        ):

            return 0.0

        score = 0.0

        timeframes = analysis.get(
            "timeframes",
            {}
        )

        expected = (
            "BULLISH"
            if direction == "BUY"
            else "BEARISH"
        )

        for timeframe in [
            "H1",
            "M30",
            "M5"
        ]:

            result = timeframes.get(
                timeframe,
                {}
            )

            if not isinstance(
                result,
                dict
            ):
                continue

            structure = result.get(
                "structure",
                {}
            )

            if not isinstance(
                structure,
                dict
            ):
                continue

            trend = structure.get(
                "trend"
            )

            if trend == expected:

                if timeframe == "H1":

                    score += 30

                elif timeframe == "M30":

                    score += 25

                elif timeframe == "M5":

                    score += 20

        # -----------------------------------------
        # Pattern confirmation
        # -----------------------------------------

        m5 = timeframes.get(
            "M5",
            {}
        )

        patterns = m5.get(
            "patterns",
            []
        )

        if not isinstance(
            patterns,
            list
        ):

            patterns = []

        bullish_patterns = {
            "HAMMER",
            "BULLISH_MOMENTUM",
            "BULLISH_REJECTION",
            "BULLISH_ENGULFING",
            "MORNING_STAR"
        }

        bearish_patterns = {
            "SHOOTING_STAR",
            "BEARISH_MOMENTUM",
            "BEARISH_REJECTION",
            "BEARISH_ENGULFING",
            "EVENING_STAR"
        }

        for item in reversed(patterns):

            if not isinstance(
                item,
                dict
            ):
                continue

            pattern = item.get(
                "pattern"
            )

            if (
                direction == "BUY"
                and pattern in bullish_patterns
            ):

                score += 15
                break

            if (
                direction == "SELL"
                and pattern in bearish_patterns
            ):

                score += 15
                break

        return min(
            round(score, 2),
            100.0
        )

    def generate_trade_plan(
        self,
        analysis,
        direction,
        confidence
    ):
        """
        Generate a proposed trade plan.
        """

        if direction == "WAIT":

            return {
                "success": False,
                "status": "WAIT",
                "message": "No valid directional setup"
            }

        if not analysis or not isinstance(
            analysis,
            dict
        ):

            return {
                "success": False,
                "status": "WAIT",
                "message": "Invalid analysis data"
            }

        m5 = analysis.get(
            "timeframes",
            {}
        ).get(
            "M5",
            {}
        )

        if not isinstance(
            m5,
            dict
        ):

            return {
                "success": False,
                "status": "WAIT",
                "message": "No M5 analysis available"
            }

        candles = m5.get(
            "candles",
            []
        )

        structure = m5.get(
            "structure",
            {}
        )

        if not candles:

            return {
                "success": False,
                "status": "WAIT",
                "message": "No M5 candles available"
            }

        entry = candles[-1].get(
            "close"
        )

        if entry is None:

            return {
                "success": False,
                "status": "WAIT",
                "message": "Invalid M5 closing price"
            }

        swings = structure.get(
            "swings",
            []
        )

        if not isinstance(
            swings,
            list
        ):

            swings = []

        swing_high = None
        swing_low = None

        for swing in reversed(swings):

            if not isinstance(
                swing,
                dict
            ):
                continue

            if (
                swing.get("type")
                == "SWING_HIGH"
            ):

                swing_high = swing.get(
                    "price"
                )

                break

        for swing in reversed(swings):

            if not isinstance(
                swing,
                dict
            ):
                continue

            if (
                swing.get("type")
                == "SWING_LOW"
            ):

                swing_low = swing.get(
                    "price"
                )

                break

        reasons = []

        if direction == "BUY":

            reasons.append(
                "Overall bullish structure"
            )

        elif direction == "SELL":

            reasons.append(
                "Overall bearish structure"
            )

        # -----------------------------------------
        # Risk engine
        # -----------------------------------------

        try:

            plan = self.risk.build_trade_plan(

                market=analysis.get(
                    "market",
                    analysis.get(
                        "symbol",
                        ""
                    )
                ),

                timeframe="M5",

                direction=direction,

                entry=entry,

                swing_high=swing_high,

                swing_low=swing_low,

                confidence=confidence,

                reason=reasons
            )

        except Exception as error:

            return {
                "success": False,
                "status": "WAIT",
                "message": f"Risk engine error: {error}"
            }

        # -----------------------------------------
        # Protect against None from RiskEngine
        # -----------------------------------------

        if plan is None:

            return {
                "success": False,
                "status": "WAIT",
                "message": "Risk engine returned no trade plan"
            }

        return plan

    def run(
        self,
        symbol,
        market_name=None
    ):
        """
        Complete analysis pipeline.

        IMPORTANT:
        This method always returns a dictionary.
        """

        try:

            analysis = self.analyze_market(
                symbol=symbol,
                market_name=market_name
            )

            # -------------------------------------
            # Protect against None
            # -------------------------------------

            if not analysis or not isinstance(
                analysis,
                dict
            ):

                return {
                    "success": False,
                    "market": market_name or symbol,
                    "symbol": symbol,
                    "direction": "WAIT",
                    "confidence": 0.0,
                    "trade_plan": {
                        "success": False,
                        "status": "WAIT",
                        "message": "Analysis returned no data"
                    },
                    "message": "Analysis engine returned no result"
                }

            if not analysis.get(
                "success"
            ):

                return {
                    "success": False,
                    "market": analysis.get(
                        "market",
                        market_name or symbol
                    ),
                    "symbol": symbol,
                    "direction": "WAIT",
                    "confidence": 0.0,
                    "trade_plan": {
                        "success": False,
                        "status": "WAIT",
                        "message": analysis.get(
                            "message",
                            "Market analysis failed"
                        )
                    },
                    "message": analysis.get(
                        "message",
                        "Market analysis failed"
                    ),
                    "analysis": analysis
                }

            # -------------------------------------
            # Direction
            # -------------------------------------

            direction = self.determine_direction(
                analysis
            )

            # -------------------------------------
            # Confidence
            # -------------------------------------

            confidence = self.calculate_confidence(
                analysis,
                direction
            )

            # -------------------------------------
            # Trade plan
            # -------------------------------------

            trade_plan = self.generate_trade_plan(
                analysis,
                direction,
                confidence
            )

            if trade_plan is None:

                trade_plan = {
                    "success": False,
                    "status": "WAIT",
                    "message": "No trade plan generated"
                }

            # -------------------------------------
            # FINAL RESULT
            # -------------------------------------

            return {
                "success": True,

                "market": analysis.get(
                    "market",
                    market_name or symbol
                ),

                "symbol": analysis.get(
                    "symbol",
                    symbol
                ),

                "direction": direction,

                "confidence": confidence,

                "trade_plan": trade_plan,

                "analysis": analysis
            }

        except Exception as error:

            # -------------------------------------
            # NEVER return None
            # -------------------------------------

            return {
                "success": False,

                "market": market_name or symbol,

                "symbol": symbol,

                "direction": "WAIT",

                "confidence": 0.0,

                "trade_plan": {
                    "success": False,
                    "status": "WAIT",
                    "message": "Analysis engine error"
                },

                "message": str(error)
            }