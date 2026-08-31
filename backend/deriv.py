import json
import websocket


class DerivClient:
    def __init__(self, app_id=None):
        self.app_id = app_id
        self.ws = None

    def connect(self):
        """
        Connect to Deriv WebSocket API.
        """
        url = "wss://ws.derivws.com/websockets/v3"

        if self.app_id:
            url += f"?app_id={self.app_id}"

        try:
            self.ws = websocket.create_connection(url, timeout=10)

            return {
                "success": True,
                "message": "Connected to Deriv"
            }

        except Exception as error:
            return {
                "success": False,
                "message": str(error)
            }

    def get_candles(
        self,
        symbol,
        granularity=300,
        count=200
    ):
        """
        Request historical OHLC candles.

        granularity:
        300  = M5
        1800 = M30
        3600 = H1
        """

        if not self.ws:
            return {
                "success": False,
                "message": "Deriv connection is not active"
            }

        request = {
            "ticks_history": symbol,
            "adjust_start_time": 1,
            "count": count,
            "end": "latest",
            "start": 1,
            "style": "candles",
            "granularity": granularity
        }

        try:
            self.ws.send(json.dumps(request))

            response = self.ws.recv()

            data = json.loads(response)

            if "error" in data:
                return {
                    "success": False,
                    "message": data["error"].get(
                        "message",
                        "Unknown Deriv error"
                    )
                }

            return {
                "success": True,
                "data": data
            }

        except Exception as error:
            return {
                "success": False,
                "message": str(error)
            }

    def close(self):
        """
        Close the Deriv connection.
        """
        if self.ws:
            self.ws.close()
            self.ws = None