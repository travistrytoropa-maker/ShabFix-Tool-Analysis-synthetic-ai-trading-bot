class StructureEngine:
    """
    Detects swing points, market structure and
    basic Break of Structure (BOS) / Change of Character (CHOCH).
    """

    def __init__(self, swing_window=2):
        self.swing_window = swing_window

    def find_swings(self, candles):
        """
        Find swing highs and swing lows.
        """

        swings = []

        window = self.swing_window

        if len(candles) < (window * 2 + 1):
            return swings

        for i in range(window, len(candles) - window):

            current = candles[i]

            left = candles[
                i - window:i
            ]

            right = candles[
                i + 1:i + window + 1
            ]

            is_swing_high = all(
                current["high"] > candle["high"]
                for candle in left + right
            )

            is_swing_low = all(
                current["low"] < candle["low"]
                for candle in left + right
            )

            if is_swing_high:
                swings.append({
                    "index": i,
                    "time": current["time"],
                    "type": "SWING_HIGH",
                    "price": current["high"]
                })

            if is_swing_low:
                swings.append({
                    "index": i,
                    "time": current["time"],
                    "type": "SWING_LOW",
                    "price": current["low"]
                })

        return swings

    def classify_swings(self, swings):
        """
        Classify swing highs and lows as:

        HH = Higher High
        LH = Lower High
        HL = Higher Low
        LL = Lower Low
        """

        classified = []

        highs = []
        lows = []

        for swing in swings:

            if swing["type"] == "SWING_HIGH":

                previous_high = (
                    highs[-1]
                    if highs
                    else None
                )

                if previous_high is None:
                    label = "HIGH"

                elif swing["price"] > previous_high["price"]:
                    label = "HH"

                else:
                    label = "LH"

                highs.append(swing)

            else:

                previous_low = (
                    lows[-1]
                    if lows
                    else None
                )

                if previous_low is None:
                    label = "LOW"

                elif swing["price"] > previous_low["price"]:
                    label = "HL"

                else:
                    label = "LL"

                lows.append(swing)

            item = dict(swing)
            item["label"] = label

            classified.append(item)

        return classified

    def determine_trend(self, classified_swings):
        """
        Determine broad market structure.
        """

        if not classified_swings:
            return "UNKNOWN"

        recent = classified_swings[-8:]

        bullish_points = sum(
            1
            for swing in recent
            if swing["label"] in {"HH", "HL"}
        )

        bearish_points = sum(
            1
            for swing in recent
            if swing["label"] in {"LH", "LL"}
        )

        if bullish_points >= bearish_points + 2:
            return "BULLISH"

        if bearish_points >= bullish_points + 2:
            return "BEARISH"

        return "RANGING"

    def detect_bos(
        self,
        candles,
        classified_swings
    ):
        """
        Detect basic bullish/bearish Break of Structure.
        """

        events = []

        if not candles or not classified_swings:
            return events

        swing_highs = [
            swing
            for swing in classified_swings
            if swing["type"] == "SWING_HIGH"
        ]

        swing_lows = [
            swing
            for swing in classified_swings
            if swing["type"] == "SWING_LOW"
        ]

        if swing_highs:

            latest_high = swing_highs[-1]

            for i in range(
                latest_high["index"] + 1,
                len(candles)
            ):

                candle = candles[i]

                if candle["close"] > latest_high["price"]:

                    events.append({
                        "index": i,
                        "time": candle["time"],
                        "type": "BULLISH_BOS",
                        "level": latest_high["price"]
                    })

                    break

        if swing_lows:

            latest_low = swing_lows[-1]

            for i in range(
                latest_low["index"] + 1,
                len(candles)
            ):

                candle = candles[i]

                if candle["close"] < latest_low["price"]:

                    events.append({
                        "index": i,
                        "time": candle["time"],
                        "type": "BEARISH_BOS",
                        "level": latest_low["price"]
                    })

                    break

        return events

    def analyze(self, candles):
        """
        Run complete structure analysis.
        """

        swings = self.find_swings(candles)

        classified = self.classify_swings(
            swings
        )

        trend = self.determine_trend(
            classified
        )

        bos = self.detect_bos(
            candles,
            classified
        )

        return {
            "trend": trend,
            "swings": classified,
            "bos": bos
        }