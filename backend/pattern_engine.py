class PatternEngine:
    """
    Detects candlestick patterns from OHLC data.
    """

    def __init__(self):
        self.patterns = []

    @staticmethod
    def _body(candle):
        return abs(
            candle["close"] - candle["open"]
        )

    @staticmethod
    def _range(candle):
        return (
            candle["high"] - candle["low"]
        )

    @staticmethod
    def _upper_wick(candle):
        return (
            candle["high"]
            - max(
                candle["open"],
                candle["close"]
            )
        )

    @staticmethod
    def _lower_wick(candle):
        return (
            min(
                candle["open"],
                candle["close"]
            )
            - candle["low"]
        )

    @staticmethod
    def _bullish(candle):
        return candle["close"] > candle["open"]

    @staticmethod
    def _bearish(candle):
        return candle["close"] < candle["open"]

    def detect_single_candle_patterns(self, candle):
        """
        Detect patterns involving one candle.
        """

        patterns = []

        candle_range = self._range(candle)
        body = self._body(candle)
        upper = self._upper_wick(candle)
        lower = self._lower_wick(candle)

        if candle_range <= 0:
            return patterns

        body_ratio = body / candle_range

        # Doji
        if body_ratio <= 0.10:
            patterns.append("DOJI")

        # Hammer
        if (
            lower >= body * 2
            and upper <= body
            and body_ratio < 0.45
        ):
            patterns.append("HAMMER")

        # Shooting Star
        if (
            upper >= body * 2
            and lower <= body
            and body_ratio < 0.45
        ):
            patterns.append("SHOOTING_STAR")

        # Strong bullish momentum candle
        if (
            self._bullish(candle)
            and body_ratio >= 0.70
        ):
            patterns.append("BULLISH_MOMENTUM")

        # Strong bearish momentum candle
        if (
            self._bearish(candle)
            and body_ratio >= 0.70
        ):
            patterns.append("BEARISH_MOMENTUM")

        # Bullish rejection
        if (
            self._bullish(candle)
            and lower > body * 1.5
        ):
            patterns.append("BULLISH_REJECTION")

        # Bearish rejection
        if (
            self._bearish(candle)
            and upper > body * 1.5
        ):
            patterns.append("BEARISH_REJECTION")

        return patterns

    def detect_two_candle_patterns(
        self,
        previous,
        current
    ):
        """
        Detect patterns involving two candles.
        """

        patterns = []

        # Bullish Engulfing
        if (
            self._bearish(previous)
            and self._bullish(current)
            and current["open"] <= previous["close"]
            and current["close"] >= previous["open"]
        ):
            patterns.append("BULLISH_ENGULFING")

        # Bearish Engulfing
        if (
            self._bullish(previous)
            and self._bearish(current)
            and current["open"] >= previous["close"]
            and current["close"] <= previous["open"]
        ):
            patterns.append("BEARISH_ENGULFING")

        # Inside Bar
        if (
            current["high"] <= previous["high"]
            and current["low"] >= previous["low"]
        ):
            patterns.append("INSIDE_BAR")

        return patterns

    def detect_three_candle_patterns(
        self,
        first,
        second,
        third
    ):
        """
        Detect three-candle formations.
        """

        patterns = []

        first_bearish = self._bearish(first)
        second_bearish = self._bearish(second)
        third_bullish = self._bullish(third)

        first_bullish = self._bullish(first)
        second_bullish = self._bullish(second)
        third_bearish = self._bearish(third)

        # Simplified Morning Star
        if (
            first_bearish
            and self._body(second) < self._body(first) * 0.5
            and third_bullish
            and third["close"] > (
                first["open"]
                + first["close"]
            ) / 2
        ):
            patterns.append("MORNING_STAR")

        # Simplified Evening Star
        if (
            first_bullish
            and self._body(second) < self._body(first) * 0.5
            and third_bearish
            and third["close"] < (
                first["open"]
                + first["close"]
            ) / 2
        ):
            patterns.append("EVENING_STAR")

        return patterns

    def analyze(self, candles):
        """
        Analyze an entire candle series.

        Returns detected patterns with their
        candle indexes.
        """

        results = []

        if not candles:
            return results

        for i, candle in enumerate(candles):

            single_patterns = (
                self.detect_single_candle_patterns(
                    candle
                )
            )

            for pattern in single_patterns:
                results.append({
                    "index": i,
                    "time": candle["time"],
                    "pattern": pattern,
                    "direction": self.pattern_direction(
                        pattern
                    )
                })

            if i >= 1:

                two_patterns = (
                    self.detect_two_candle_patterns(
                        candles[i - 1],
                        candle
                    )
                )

                for pattern in two_patterns:
                    results.append({
                        "index": i,
                        "time": candle["time"],
                        "pattern": pattern,
                        "direction": self.pattern_direction(
                            pattern
                        )
                    })

            if i >= 2:

                three_patterns = (
                    self.detect_three_candle_patterns(
                        candles[i - 2],
                        candles[i - 1],
                        candle
                    )
                )

                for pattern in three_patterns:
                    results.append({
                        "index": i,
                        "time": candle["time"],
                        "pattern": pattern,
                        "direction": self.pattern_direction(
                            pattern
                        )
                    })

        return results

    @staticmethod
    def pattern_direction(pattern):

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

        if pattern in bullish_patterns:
            return "BULLISH"

        if pattern in bearish_patterns:
            return "BEARISH"

        return "NEUTRAL"