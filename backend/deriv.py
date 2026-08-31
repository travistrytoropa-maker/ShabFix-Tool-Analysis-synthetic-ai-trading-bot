import json
import websocket


class DerivClient:
    """
    Public Deriv market-data client.

    Authentication is not required for:
    - Active symbols
    - Historical candles
    - Public market data
    """

    def __init__(self, app_id=None):
        self.app_id = app_id
        self.ws = None

    def connect(self):
        """
        Connect to Deriv's public market-data WebSocket.
        """

        url = "wss://ws.binaryws.com/websockets/v3"

        try:
            self.ws = websocket.create_connection(
                url,
                timeout=15
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

    def send_request(self, request):
        """
        Send a request and return the decoded response.
        """

        if self.ws is None:

            connection = self.connect()

            if not connection["success"]:
                return connection

        try:

            self.ws.send(
                json.dumps(request)
            )

            response = self.ws.recv()

            data = json.loads(response)

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

            self.ws = None

            return {
                "success": False,
                "message": str(error)
            }

    def get_active_symbols(self):
        """
        Retrieve currently available Deriv markets.
        """

        request = {
            "active_symbols": "brief"
        }

        return self.send_request(request)

    def get_candles(
        self,
        symbol,
        granularity=300,
        count=200
    ):
        """
        Retrieve historical OHLC candles.

        M5  = 300 seconds
        M30 = 1800 seconds
        H1  = 3600 seconds
        """

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

        return {
            "success": True,
            "data": result["data"]
        }

    def close(self):
        """
        Close the WebSocket connection.
        """

        if self.ws:

            try:
                self.ws.close()

            except Exception:
                pass

            finally:
                self.ws = None