import json
import time
import websocket


class DerivClient:
    """
    Robust Deriv public market-data client.

    Features:
    - Automatic WebSocket connection
    - Automatic reconnect
    - Automatic request retry
    - Active market discovery
    - Historical OHLC candles
    - Public market data only
    """

    WS_URL = "wss://api.derivws.com/trading/v1/options/ws/public"

    def __init__(self, app_id=None, timeout=20, max_retries=3):
        self.app_id = app_id
        self.timeout = timeout
        self.max_retries = max_retries
        self.ws = None
        self.req_id = 0

    # --------------------------------------------------
    # REQUEST ID
    # --------------------------------------------------

    def _next_req_id(self):
        self.req_id += 1
        return self.req_id

    # --------------------------------------------------
    # CONNECT
    # --------------------------------------------------

    def connect(self):

        self.close()

        try:

            self.ws = websocket.create_connection(
                self.WS_URL,
                timeout=self.timeout
            )

            return {
                "success": True,
                "message": "Connected to Deriv public market data"
            }

        except Exception as error:

            self.ws = None

            return {
                "success": False,
                "message": str(error)
            }

    # --------------------------------------------------
    # CONNECTION CHECK
    # --------------------------------------------------

    def _ensure_connection(self):

        if self.ws is None:

            return self.connect()

        return {
            "success": True,
            "message": "Connection already available"
        }

    # --------------------------------------------------
    # SEND REQUEST
    # --------------------------------------------------

    def send_request(self, request):

        last_error = None

        for attempt in range(self.max_retries):

            connection = self._ensure_connection()

            if not connection["success"]:

                last_error = connection["message"]

                time.sleep(1)

                continue

            try:

                # Always generate a fresh request ID
                request = dict(request)
                request["req_id"] = self._next_req_id()

                # Send request
                self.ws.send(
                    json.dumps(request)
                )

                # Wait for response
                response = self.ws.recv()

                if not response:

                    raise ConnectionError(
                        "Empty response received from Deriv"
                    )

                data = json.loads(response)

                # Deriv API error
                if "error" in data:

                    error = data["error"]

                    return {
                        "success": False,
                        "message": error.get(
                            "message",
                            "Deriv API error"
                        ),
                        "error": error
                    }

                return {
                    "success": True,
                    "data": data
                }

            except Exception as error:

                last_error = str(error)

                # Destroy broken connection
                self.close()

                # Small delay before reconnect
                time.sleep(0.5)

        return {
            "success": False,
            "message": last_error or "Deriv request failed"
        }

    # --------------------------------------------------
    # ACTIVE SYMBOLS
    # --------------------------------------------------

    def get_active_symbols(self):

        request = {
            "active_symbols": "brief"
        }

        return self.send_request(request)

    # --------------------------------------------------
    # HISTORICAL CANDLES
    # --------------------------------------------------

    def get_candles(
        self,
        symbol,
        granularity=300,
        count=200
    ):

        request = {
            "ticks_history": symbol,
            "adjust_start_time": 1,
            "count": count,
            "end": "latest",
            "style": "candles",
            "granularity": granularity
        }

        result = self.send_request(request)

        if not result["success"]:

            return result

        data = result.get("data", {})

        candles = data.get("candles")

        if not candles:

            return {
                "success": False,
                "message": (
                    f"No candle data returned for {symbol}"
                ),
                "data": data
            }

        return {
            "success": True,
            "data": data,
            "candles": candles,
            "symbol": symbol,
            "granularity": granularity
        }

    # --------------------------------------------------
    # CLOSE
    # --------------------------------------------------

    def close(self):

        if self.ws:

            try:
                self.ws.close()

            except Exception:
                pass

        self.ws = None

    # --------------------------------------------------
    # CONTEXT MANAGER
    # --------------------------------------------------

    def __enter__(self):

        self.connect()

        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback
    ):

        self.close()