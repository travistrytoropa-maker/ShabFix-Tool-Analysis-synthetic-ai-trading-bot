from datetime import datetime


class CandleEngine:
    """
    Robust candle preparation engine.

    Retrieves and validates:
    - M5
    - M30
    - H1

    Designed to work with the DerivClient reconnect/retry system.
    """

    TIMEFRAMES = {
        "M5": 300,
        "M30": 1800,
        "H1": 3600
    }

    def __init__(self, deriv_client):
        self.deriv = deriv_client

    # --------------------------------------------------
    # GET CANDLES
    # --------------------------------------------------

    def get_candles(
        self,
        symbol,
        timeframe="M5",
        count=200
    ):
        """
        Retrieve and clean candles for one timeframe.
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
                "message": f"Candle request failed: {error}",
                "symbol": symbol,
                "timeframe": timeframe,
                "candles": []
            }

        if not result or not result.get("success"):

            return {
                "success": False,
                "message": result.get(
                    "message",
                    "Deriv returned no candle data"
                ) if isinstance(result, dict) else "Invalid Deriv response",

                "symbol": symbol,
                "timeframe": timeframe,
                "candles": []
            }

        raw_data = result.get("data", {})

        if not isinstance(raw_data, dict):

            return {
                "success": False,
                "message": "Invalid candle response format",
                "symbol": symbol,
                "timeframe": timeframe,
                "candles": []
            }

        raw_candles = raw_data.get("candles", [])

        if not isinstance(raw_candles, list):

            return {
                "success": False,
                "message": "Deriv candle data is not a list",
                "symbol": symbol,
                "timeframe": timeframe,
                "candles": []
            }

        cleaned = []

        for candle in raw_candles:

            try:

                epoch = int(candle["epoch"])

                open_price = float(candle["open"])
                high_price = float(candle["high"])
                low_price = float(candle["low"])
                close_price = float(candle["close"])

                # Basic OHLC validation
                if high_price < low_price:
                    continue

                if open_price < low_price or open_price > high_price:
                    continue

                if close_price < low_price or close_price > high_price:
                    continue

                cleaned.append({
                    "time": epoch,

                    "datetime": datetime.fromtimestamp(
                        epoch
                    ).isoformat(),

                    "open": open_price,
                    "high": high_price,
                    "low": low_price,
                    "close": close_price
                })

            except (
                KeyError,
                ValueError,
                TypeError,
                OverflowError
            ):
                continue

        # Oldest → newest
        cleaned.sort(
            key=lambda x: x["time"]
        )

        if not cleaned:

            return {
                "success": False,
                "message": (
                    f"No valid {timeframe} candles "
                    f"returned for {symbol}"
                ),
                "symbol": symbol,
                "timeframe": timeframe,
                "candles": []
            }

        return {
            "success": True,
            "symbol": symbol,
            "timeframe": timeframe,
            "count": len(cleaned),
            "candles": cleaned
        }

    # --------------------------------------------------
    # MULTI-TIMEFRAME DATA
    # --------------------------------------------------

    def get_multi_timeframe_data(
        self,
        symbol,
        count=200
    ):
        """
        Retrieve M5, M30 and H1 candles.

        Does not hide failed timeframe requests.
        """

        result = {
            "success": False,
            "symbol": symbol,
            "timeframes": {}
        }

        successful_timeframes = 0

        for timeframe in self.TIMEFRAMES:

            data = self.get_candles(
                symbol=symbol,
                timeframe=timeframe,
                count=count
            )

            result["timeframes"][timeframe] = data

            if data.get("success"):

                successful_timeframes += 1

        # At least one timeframe must work
        if successful_timeframes == 0:

            result["message"] = (
                f"No candle data available for {symbol}"
            )

            return result

        result["success"] = True

        result["successful_timeframes"] = (
            successful_timeframes
        )

        result["failed_timeframes"] = (
            len(self.TIMEFRAMES)
            - successful_timeframes
        )

        return result

    # --------------------------------------------------
    # CANDLE DIRECTION
    # --------------------------------------------------

    @staticmethod
    def candle_direction(candle):

        if candle["close"] > candle["open"]:
            return "BULLISH"

        if candle["close"] < candle["open"]:
            return "BEARISH"

        return "NEUTRAL"

    # --------------------------------------------------
    # CANDLE RANGE
    # --------------------------------------------------

    @staticmethod
    def candle_range(candle):

        return (
            candle["high"]
            - candle["low"]
        )

    # --------------------------------------------------
    # BODY
    # --------------------------------------------------

    @staticmethod
    def body_size(candle):

        return abs(
            candle["close"]
            - candle["open"]
        )

    # --------------------------------------------------
    # UPPER WICK
    # --------------------------------------------------

    @staticmethod
    def upper_wick(candle):

        return (
            candle["high"]
            - max(
                candle["open"],
                candle["close"]
            )
        )

    # --------------------------------------------------
    # LOWER WICK
    # --------------------------------------------------

    @staticmethod
    def lower_wick(candle):

        return (
            min(
                candle["open"],
                candle["close"]
            )
            - candle["low"]
        )

    # --------------------------------------------------
    # CANDLE METRICS
    # --------------------------------------------------

    @classmethod
    def candle_metrics(cls, candle):

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