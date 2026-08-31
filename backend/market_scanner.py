import json


class MarketScanner:
    """
    Discovers and filters synthetic markets from Deriv.
    """

    def __init__(self, deriv_client):
        self.deriv = deriv_client

        self.target_markets = [
            "Volatility 10 Index",
            "Volatility 25 Index",
            "Volatility 50 Index",
            "Volatility 75 Index",
            "Volatility 100 Index",
            "Step Index",
            "Jump 10 Index",
            "Jump 25 Index",
            "Jump 50 Index",
            "Jump 75 Index",
        ]

    def get_markets(self):
        """
        Request active markets from Deriv.
        """

        if not self.deriv.ws:
            return {
                "success": False,
                "message": "Deriv connection is not active"
            }

        request = {
            "active_symbols": "brief",
            "product_type": "basic"
        }

        try:
            self.deriv.ws.send(json.dumps(request))

            response = self.deriv.ws.recv()

            data = json.loads(response)

            if "error" in data:
                return {
                    "success": False,
                    "message": data["error"].get(
                        "message",
                        "Unknown Deriv error"
                    )
                }

            symbols = data.get("active_symbols", [])

            return {
                "success": True,
                "markets": symbols
            }

        except Exception as error:
            return {
                "success": False,
                "message": str(error)
            }

    def find_target_markets(self):
        """
        Find the requested synthetic markets.
        """

        result = self.get_markets()

        if not result["success"]:
            return result

        found = []

        for market in result["markets"]:

            display_name = market.get(
                "display_name",
                ""
            )

            symbol = market.get(
                "symbol",
                ""
            )

            for target in self.target_markets:

                if target.lower() in display_name.lower():

                    found.append({
                        "name": display_name,
                        "symbol": symbol
                    })

                    break

        return {
            "success": True,
            "markets": found,
            "count": len(found)
        }