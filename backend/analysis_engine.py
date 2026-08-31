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

        data = self.candles.get_multi_timeframe_data(
            symbol=symbol,
            count=candle_count
        )

        if not data:
            return {
                "success": False,
                "message": "No market data returned"
            }

        timeframe_results = {}

        for timeframe in ["H1", "M30", "M5"]:

            timeframe_data = (
                data["timeframes"].get(timeframe)
            )

            if not timeframe_data:
                timeframe_results[timeframe] = {
                    "success": False,
                    "message": "No timeframe data"
                }
                continue

            if not timeframe_data.get("success"):
                timeframe_results[timeframe] = timeframe_data
                continue

            candles = timeframe_data.get(
                "candles",
                []
            )

            if len(candles) < 10:
                timeframe_results[timeframe] = {
                    "success": False,
                    "message": "Not enough candles"
                }
                continue

            detected_patterns = (
                self.patterns.analyze(
                    candles
                )
            )

            structure = (
                self.structure.analyze(
                    candles
                )
            )

            timeframe_results[timeframe] = {
                "success": True,

                "candles": candles,

                "latest_price": candles[-1]["close"],

                "patterns": detected_patterns[-20:],

                "structure": structure
            }

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

        if bullish >= 2 and bullish > bearish:
            return "BUY"

        if bearish >= 2 and bearish > bullish:
            return "SELL"

        return "WAIT"

    def calculate_confidence(
        self,
        analysis,
        direction
    ):
        """
        Calculate an initial confidence score.

        This is a foundation. The scoring model will
        become more sophisticated as the project grows.
        """

        if direction == "WAIT":
            return 0.0

        score = 0.0

        timeframes = analysis.get(
            "timeframes",
            {}
        )

        # ----------------------------
        # Multi-timeframe agreement
        # ----------------------------

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

            trend = (
                result
                .get("structure", {})
                .get("trend")
            )

            if trend == expected:

                if timeframe == "H1":
                    score += 30

                elif timeframe == "M30":
                    score += 25

                elif timeframe == "M5":
                    score += 20

        # ----------------------------
        # Candle pattern confirmation
        # ----------------------------

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

        for item in reversed(patterns):

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
        Generate a proposed trade plan from
        the latest M5 structure.
        """

        if direction == "WAIT":
            return {
                "success": False,
                "status": "WAIT",
                "message": "No valid directional setup"
            }

        m5 = analysis["timeframes"].get(
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

        entry = candles[-1]["close"]

        swings = structure.get(
            "swings",
            []
        )

        swing_high = None
        swing_low = None

        for swing in reversed(swings):

            if swing["type"] == "SWING_HIGH":
                swing_high = swing["price"]
                break

        for swing in reversed(swings):

            if swing["type"] == "SWING_LOW":
                swing_low = swing["price"]
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

        return self.risk.build_trade_plan(
            market=analysis["market"],
            timeframe="M5",
            direction=direction,
            entry=entry,
            swing_high=swing_high,
            swing_low=swing_low,
            confidence=confidence,
            reason=reasons
        )

    def run(self, symbol, market_name=None):
        """
        Complete analysis pipeline.
        """

        analysis = self.analyze_market(
            symbol=symbol,
            market_name=market_name
        )

        if not analysis.get("success"):
            return analysis

        direction = self.determine_direction(
            analysis
        )

        confidence = self.calculate_confidence(
            analysis,
            direction
        )

        trade_plan = self.generate_trade_plan(
            analysis,
            direction,
            confidence
        )

        return {
            "success": True,

            "market": analysis["market"],

            "symbol": analysis["symbol"],

            "direction": direction,

            "confidence": confidence,

            "trade_plan": trade_plan,

            "analysis": analysis
        }