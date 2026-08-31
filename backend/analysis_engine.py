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

    # =========================================================
    # COMPLETE MARKET ANALYSIS
    # =========================================================

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

        data = self.candles.get_multi_timeframe_data(
            symbol=symbol,
            count=candle_count
        )

        # -----------------------------------------------------
        # IMPORTANT SAFETY CHECK
        # Prevents errors when candle engine returns
        # None, invalid data, or a failed response.
        # -----------------------------------------------------

        if not data or not data.get("success"):
            return {
                "success": False,
                "message": data.get(
                    "message",
                    "No market data returned"
                ) if isinstance(data, dict)
                else "No market data returned"
            }

        # -----------------------------------------------------
        # TIMEFRAME ANALYSIS
        # -----------------------------------------------------

        timeframe_results = {}

        for timeframe in ["H1", "M30", "M5"]:

            timeframe_data = (
                data.get("timeframes", {})
                .get(timeframe)
            )

            if not timeframe_data:
                timeframe_results[timeframe] = {
                    "success": False,
                    "message": "No timeframe data"
                }
                continue

            if not isinstance(timeframe_data, dict):
                timeframe_results[timeframe] = {
                    "success": False,
                    "message": "Invalid timeframe data"
                }
                continue

            if not timeframe_data.get("success"):
                timeframe_results[timeframe] = timeframe_data
                continue

            candles = timeframe_data.get(
                "candles",
                []
            )

            if not candles or len(candles) < 10:
                timeframe_results[timeframe] = {
                    "success": False,
                    "message": "Not enough candles"
                }
                continue

            # -------------------------------------------------
            # CANDLE PATTERN ANALYSIS
            # -------------------------------------------------

            try:
                detected_patterns = (
                    self.patterns.analyze(
                        candles
                    )
                )
            except Exception as error:
                detected_patterns = []

            # -------------------------------------------------
            # MARKET STRUCTURE ANALYSIS
            # -------------------------------------------------

            try:
                structure = (
                    self.structure.analyze(
                        candles
                    )
                )
            except Exception as error:
                structure = {
                    "trend": "UNKNOWN",
                    "message": str(error)
                }

            # -------------------------------------------------
            # SAVE TIMEFRAME RESULT
            # -------------------------------------------------

            timeframe_results[timeframe] = {
                "success": True,

                "candles": candles,

                "latest_price": candles[-1]["close"],

                "patterns": (
                    detected_patterns[-20:]
                    if isinstance(
                        detected_patterns,
                        list
                    )
                    else []
                ),

                "structure": structure
            }

        # -----------------------------------------------------
        # RETURN COMPLETE ANALYSIS
        # -----------------------------------------------------

        return {
            "success": True,
            "market": market_name,
            "symbol": symbol,
            "timeframes": timeframe_results
        }

    # =========================================================
    # DETERMINE MARKET DIRECTION
    # =========================================================

    def determine_direction(
        self,
        analysis
    ):
        """
        Determine overall direction using
        H1, M30 and M5 structure.
        """

        if not isinstance(analysis, dict):
            return "WAIT"

        timeframes = analysis.get(
            "timeframes",
            {}
        )

        h1 = timeframes.get("H1", {})
        m30 = timeframes.get("M30", {})
        m5 = timeframes.get("M5", {})

        h1_trend = (
            h1.get("structure", {})
            .get("trend", "UNKNOWN")
        )

        m30_trend = (
            m30.get("structure", {})
            .get("trend", "UNKNOWN")
        )

        m5_trend = (
            m5.get("structure", {})
            .get("trend", "UNKNOWN")
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

        # -----------------------------------------------------
        # BUY
        # -----------------------------------------------------

        if bullish >= 2 and bullish > bearish:
            return "BUY"

        # -----------------------------------------------------
        # SELL
        # -----------------------------------------------------

        if bearish >= 2 and bearish > bullish:
            return "SELL"

        # -----------------------------------------------------
        # NO CLEAR DIRECTION
        # -----------------------------------------------------

        return "WAIT"

    # =========================================================
    # CONFIDENCE CALCULATION
    # =========================================================

    def calculate_confidence(
        self,
        analysis,
        direction
    ):
        """
        Calculate initial confidence score.
        """

        if direction == "WAIT":
            return 0.0

        if not isinstance(analysis, dict):
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

        # -----------------------------------------------------
        # MULTI-TIMEFRAME AGREEMENT
        # -----------------------------------------------------

        for timeframe in [
            "H1",
            "M30",
            "M5"
        ]:

            result = timeframes.get(
                timeframe,
                {}
            )

            if not isinstance(result, dict):
                continue

            structure = result.get(
                "structure",
                {}
            )

            if not isinstance(structure, dict):
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

        # -----------------------------------------------------
        # CANDLE PATTERN CONFIRMATION
        # -----------------------------------------------------

        m5 = timeframes.get(
            "M5",
            {}
        )

        patterns = m5.get(
            "patterns",
            []
        )

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

        if isinstance(patterns, list):

            for item in reversed(patterns):

                if not isinstance(item, dict):
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

    # =========================================================
    # GENERATE TRADE PLAN
    # =========================================================

    def generate_trade_plan(
        self,
        analysis,
        direction,
        confidence
    ):
        """
        Generate a proposed trade plan from
        the latest M5 structure.
        """

        if direction == "WAIT":
            return {
                "success": False,
                "status": "WAIT",
                "message": "No valid directional setup"
            }

        if not isinstance(analysis, dict):
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

        # -----------------------------------------------------
        # ENTRY
        # -----------------------------------------------------

        entry = candles[-1]["close"]

        # -----------------------------------------------------
        # FIND RECENT SWINGS
        # -----------------------------------------------------

        swings = structure.get(
            "swings",
            []
        )

        swing_high = None
        swing_low = None

        if isinstance(swings, list):

            for swing in reversed(swings):

                if not isinstance(swing, dict):
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

                if not isinstance(swing, dict):
                    continue

                if (
                    swing.get("type")
                    == "SWING_LOW"
                ):

                    swing_low = swing.get(
                        "price"
                    )

                    break

        # -----------------------------------------------------
        # TRADE REASONS
        # -----------------------------------------------------

        reasons = []

        if direction == "BUY":

            reasons.append(
                "Overall bullish structure"
            )

        elif direction == "SELL":

            reasons.append(
                "Overall bearish structure"
            )

        # -----------------------------------------------------
        # BUILD RISK PLAN
        # -----------------------------------------------------

        try:

            return self.risk.build_trade_plan(
                market=analysis.get(
                    "market",
                    analysis.get(
                        "symbol",
                        "UNKNOWN"
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
                "message": (
                    f"Risk engine error: {error}"
                )
            }

    # =========================================================
    # MAIN ANALYSIS PIPELINE
    # =========================================================

    def run(
        self,
        symbol,
        market_name=None
    ):
        """
        Complete analysis pipeline.
        """

        # -----------------------------------------------------
        # STEP 1 — ANALYZE MARKET
        # -----------------------------------------------------

        analysis = self.analyze_market(
            symbol=symbol,
            market_name=market_name
        )

        if not isinstance(analysis, dict):
            return {
                "success": False,
                "message": "Invalid analysis response"
            }

        if not analysis.get("success"):
            return analysis

        # -----------------------------------------------------
        # STEP 2 — DETERMINE DIRECTION
        # -----------------------------------------------------

        direction = self.determine_direction(
            analysis
        )

        # -----------------------------------------------------
        # STEP 3 — CALCULATE CONFIDENCE
        # -----------------------------------------------------

        confidence = self.calculate_confidence(
            analysis,
            direction
        )

        # -----------------------------------------------------
        # STEP 4 — GENERATE TRADE PLAN
        # -----------------------------------------------------

        trade_plan = self.generate_trade_plan(
            analysis,
            direction,
            confidence
        )

        # -----------------------------------------------------
        # STEP 