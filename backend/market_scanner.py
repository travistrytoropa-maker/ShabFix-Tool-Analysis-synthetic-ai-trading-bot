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
            "Jump 75 Index"
        ]

    def get_markets(self):
        """
        Request active markets from Deriv.
        """

        result = (
            self.deriv.get_active_symbols()
        )

        if not result["success"]:
            return result

        data = result["data"]

        symbols = data.get(
            "active_symbols",
            []
        )

        return {
            "success": True,
            "markets": symbols,
            "count": len(symbols)
        }

    def find_target_markets(self):
        """
        Find requested synthetic markets.
        """

        result = self.get_markets()

        if not result["success"]:
            return result

        found = []

        for market in result["markets"]:

            display_name = market.get(
                "underlying_symbol_name",
                ""
            )

            symbol = market.get(
                "underlying_symbol",
                ""
            )

            if not display_name:
                continue

            for target in self.target_markets:

                if target.lower() == display_name.lower():

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