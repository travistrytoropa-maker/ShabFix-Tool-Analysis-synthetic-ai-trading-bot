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
                "message": f"Unsupported timeframe: {timeframe}",
                "symbol": symbol,
                "timeframe": timeframe,
                "candles": []
            }

        granularity = self.TIMEFRAMES[timeframe]

        try:
            result = self.deriv.get_candles(
                symbol=symbol,
                granularity=granularity,
                count=count
            )
        except Exception as error:
            return {
                "success": False,
                "message": str(error),
                "symbol": symbol,
                "timeframe": timeframe,
                "candles": []
            }

        # ------------------------------------------------
        # Validate Deriv response
        # ------------------------------------------------

        if not result or not isinstance(result, dict):
            return {
                "success": False,
                "message": "Invalid response from Deriv",
                "symbol": symbol,
                "timeframe": timeframe,
                "candles": []
            }

        if not result.get("success"):
            return {
                "success": False,
                "message": result.get(
                    "message",
                    "Failed to retrieve candles"
                ),
                "symbol": symbol,
                "timeframe": timeframe,
                "candles": []
            }

        raw_data = result.get("data")

        if not raw_data or not isinstance(raw_data, dict):
            return {
                "success": False,
                "message": "No candle data returned by Deriv",
                "symbol": symbol,
                "timeframe": timeframe,
                "candles": []
            }

        candles = raw_data.get("candles", [])

        if not isinstance(candles, list):
            return {
                "success": False,
                "message": "Invalid candle format returned by Deriv",
                "symbol": symbol,
                "timeframe": timeframe,
                "candles": []
            }

        # ------------------------------------------------
        # Clean candle data
        # ------------------------------------------------

        cleaned = []

        for candle in candles:

            try:
                epoch = int(candle["epoch"])

                cleaned.append({
                    "time": epoch,

                    "datetime": datetime.fromtimestamp(
                        epoch
                    ).isoformat(),

                    "open": float(candle["open"]),
                    "high": float(candle["high"]),
                    "low": float(candle["low"]),
                    "close": float(candle["close"])
                })

            except (
                KeyError,
                ValueError,
                TypeError
            ):
                continue

        # ------------------------------------------------
        # Sort oldest -> newest
        # ------------------------------------------------

        cleaned.sort(
            key=lambda x: x["time"]
        )

        # ------------------------------------------------
        # Return cleaned candles
        # ------------------------------------------------

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

        Returns a consistent response containing
        success, symbol and timeframe data.
        """

        result = {
            "success": True,
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

        # ------------------------------------------------
        # Check whether at least one timeframe worked
        # ------------------------------------------------

        successful_timeframes = 0

        for timeframe_data in result["timeframes"].values():

            if (
                isinstance(timeframe_data, dict)
                and timeframe_data.get("success") is True
                and len(
                    timeframe_data.get("candles", [])
                ) > 0
            ):
                successful_timeframes += 1

        if successful_timeframes == 0:

            result["success"] = False

            result["message"] = (
                "No candle data available for "
                "M5, M30 or H1"
            )

        else:

            result["success"] = True

            result["message"] = (
                f"Retrieved candle data for "
                f"{successful_timeframes}/3 timeframes"
            )

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

        return (
            candle["high"]
            - candle["low"]
        )

    @staticmethod
    def body_size(candle):
        """
        Calculate candle body size.
        """

        return abs(
            candle["close"]
            - candle["open"]
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

        candle_range = cls.candle_range(
            candle
        )

        body = cls.body_size(
            candle
        )

        return {
            "direction": cls.candle_direction(
                candle
            ),

            "range": candle_range,

            "body": body,

            "upper_wick": cls.upper_wick(
                candle
            ),

            "lower_wick": cls.lower_wick(
                candle
            ),

            "body_ratio": (
                body / candle_range
                if candle_range > 0
                else 0
            )
        }