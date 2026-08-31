from datetime import datetime


class CandleEngine:
    """
    Converts and prepares Deriv candle data
    for M5, M30 and H1 analysis.
    """

    TIMEFRAMES = {
        "M5": 300,
        "M30": 1800,
        "H1": 3600
    }

    def __init__(self, deriv_client):
        self.deriv = deriv_client

    def get_candles(
        self,
        symbol,
        timeframe="M5",
        count=200
    ):
        """
        Retrieve candles for a selected timeframe.
        """

        if timeframe not in self.TIMEFRAMES:
            return {
                "success": False,
                "message": f"Unsupported timeframe: {timeframe}"
            }

        granularity = self.TIMEFRAMES[timeframe]

        result = self.deriv.get_candles(
            symbol=symbol,
            granularity=granularity,
            count=count
        )

        if not result["success"]:
            return result

        raw_data = result["data"]

        candles = raw_data.get("candles", [])

        cleaned = []

        for candle in candles:

            try:
                cleaned.append({
                    "time": int(candle["epoch"]),
                    "datetime": datetime.fromtimestamp(
                        int(candle["epoch"])
                    ).isoformat(),

                    "open": float(candle["open"]),
                    "high": float(candle["high"]),
                    "low": float(candle["low"]),
                    "close": float(candle["close"])
                })

            except (KeyError, ValueError, TypeError):
                continue

        cleaned.sort(
            key=lambda x: x["time"]
        )

        return {
            "success": True,
            "symbol": symbol,
            "timeframe": timeframe,
            "count": len(cleaned),
            "candles": cleaned
        }

    def get_multi_timeframe_data(
        self,
        symbol,
        count=200
    ):
        """
        Retrieve M5, M30 and H1 candles.
        """

        result = {
            "symbol": symbol,
            "timeframes": {}
        }

        for timeframe in self.TIMEFRAMES:

            data = self.get_candles(
                symbol=symbol,
                timeframe=timeframe,
                count=count
            )

            result["timeframes"][timeframe] = data

        return result

    @staticmethod
    def candle_direction(candle):
        """
        Determine whether a candle is bullish,
        bearish or neutral.
        """

        if candle["close"] > candle["open"]:
            return "BULLISH"

        if candle["close"] < candle["open"]:
            return "BEARISH"

        return "NEUTRAL"

    @staticmethod
    def candle_range(candle):
        """
        Calculate total candle range.
        """

        return candle["high"] - candle["low"]

    @staticmethod
    def body_size(candle):
        """
        Calculate candle body size.
        """

        return abs(
            candle["close"] - candle["open"]
        )

    @staticmethod
    def upper_wick(candle):
        """
        Calculate upper wick size.
        """

        return (
            candle["high"]
            - max(
                candle["open"],
                candle["close"]
            )
        )

    @staticmethod
    def lower_wick(candle):
        """
        Calculate lower wick size.
        """

        return (
            min(
                candle["open"],
                candle["close"]
            )
            - candle["low"]
        )

    @classmethod
    def candle_metrics(cls, candle):
        """
        Return useful candle measurements.
        """

        candle_range = cls.candle_range(candle)

        return {
            "direction": cls.candle_direction(candle),
            "range": candle_range,
            "body": cls.body_size(candle),
            "upper_wick": cls.upper_wick(candle),
            "lower_wick": cls.lower_wick(candle),
            "body_ratio": (
                cls.body_size(candle) / candle_range
                if candle_range > 0
                else 0
            )
        }