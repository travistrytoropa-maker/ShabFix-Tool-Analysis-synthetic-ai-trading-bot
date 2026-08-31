from collections import defaultdict


class HistoricalEngine:
    """
    Stores historical trade setups and evaluates
    how similar setups performed afterward.

    This engine does NOT assume that historical
    performance guarantees future results.
    """

    def __init__(self):
        self.history = []

    def record_setup(
        self,
        market,
        timeframe,
        direction,
        pattern,
        trend,
        entry,
        stop_loss,
        take_profit,
        outcome=None
    ):
        """
        Record a historical setup.
        """

        setup = {
            "market": market,
            "timeframe": timeframe,
            "direction": direction,
            "pattern": pattern,
            "trend": trend,
            "entry": float(entry),
            "stop_loss": float(stop_loss),
            "take_profit": float(take_profit),
            "outcome": outcome
        }

        self.history.append(setup)

        return setup

    def find_similar(
        self,
        market,
        timeframe,
        direction=None,
        pattern=None,
        trend=None
    ):
        """
        Find previously recorded setups with
        similar characteristics.
        """

        matches = []

        for setup in self.history:

            if setup["market"] != market:
                continue

            if setup["timeframe"] != timeframe:
                continue

            if direction is not None:
                if setup["direction"] != direction:
                    continue

            if pattern is not None:
                if setup["pattern"] != pattern:
                    continue

            if trend is not None:
                if setup["trend"] != trend:
                    continue

            matches.append(setup)

        return matches

    def calculate_statistics(self, setups):
        """
        Calculate historical outcome statistics.
        """

        if not setups:
            return {
                "sample_size": 0,
                "wins": 0,
                "losses": 0,
                "pending": 0,
                "win_rate": 0.0
            }

        wins = 0
        losses = 0
        pending = 0

        for setup in setups:

            outcome = setup.get("outcome")

            if outcome == "WIN":
                wins += 1

            elif outcome == "LOSS":
                losses += 1

            else:
                pending += 1

        completed = wins + losses

        win_rate = (
            (wins / completed) * 100
            if completed > 0
            else 0.0
        )

        return {
            "sample_size": len(setups),
            "wins": wins,
            "losses": losses,
            "pending": pending,
            "win_rate": round(
                win_rate,
                2
            )
        }

    def analyze_pattern(
        self,
        market,
        timeframe,
        pattern,
        direction,
        trend=None
    ):
        """
        Analyze historical performance of a
        specific pattern/setup.
        """

        setups = self.find_similar(
            market=market,
            timeframe=timeframe,
            direction=direction,
            pattern=pattern,
            trend=trend
        )

        statistics = self.calculate_statistics(
            setups
        )

        return {
            "market": market,
            "timeframe": timeframe,
            "pattern": pattern,
            "direction": direction,
            "trend": trend,
            "statistics": statistics
        }

    def group_by_pattern(self):
        """
        Group historical setups by pattern.
        """

        groups = defaultdict(list)

        for setup in self.history:

            key = (
                setup["market"],
                setup["timeframe"],
                setup["pattern"],
                setup["direction"]
            )

            groups[key].append(setup)

        results = []

        for key, setups in groups.items():

            market, timeframe, pattern, direction = key

            statistics = self.calculate_statistics(
                setups
            )

            results.append({
                "market": market,
                "timeframe": timeframe,
                "pattern": pattern,
                "direction": direction,
                "statistics": statistics
            })

        return results

    def get_history(self):
        """
        Return all stored historical setups.
        """

        return self.history

    def clear(self):
        """
        Clear stored historical setups.
        """

        self.history.clear()