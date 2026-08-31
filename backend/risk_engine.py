class RiskEngine:
    """
    Builds structured trade plans from a proposed entry
    and market structure.

    This engine does not execute trades.
    """

    def __init__(
        self,
        risk_reward_1=1.5,
        risk_reward_2=2.0,
        risk_reward_3=3.0,
        buffer_percent=0.001
    ):
        self.risk_reward_1 = risk_reward_1
        self.risk_reward_2 = risk_reward_2
        self.risk_reward_3 = risk_reward_3
        self.buffer_percent = buffer_percent

    def calculate_stop_loss(
        self,
        direction,
        entry,
        swing_high=None,
        swing_low=None
    ):
        """
        Calculate SL using the latest relevant swing.

        A small buffer is added to reduce the chance of
        placing SL exactly on an obvious swing level.
        """

        buffer = abs(entry) * self.buffer_percent

        if direction == "BUY":

            if swing_low is not None:
                return swing_low - buffer

            return entry - buffer

        if direction == "SELL":

            if swing_high is not None:
                return swing_high + buffer

            return entry + buffer

        return None

    def calculate_take_profits(
        self,
        direction,
        entry,
        stop_loss
    ):
        """
        Calculate three take-profit levels based
        on risk multiples.
        """

        risk = abs(entry - stop_loss)

        if risk <= 0:
            return {
                "TP1": None,
                "TP2": None,
                "TP3": None
            }

        if direction == "BUY":

            return {
                "TP1": entry + (
                    risk * self.risk_reward_1
                ),
                "TP2": entry + (
                    risk * self.risk_reward_2
                ),
                "TP3": entry + (
                    risk * self.risk_reward_3
                )
            }

        if direction == "SELL":

            return {
                "TP1": entry - (
                    risk * self.risk_reward_1
                ),
                "TP2": entry - (
                    risk * self.risk_reward_2
                ),
                "TP3": entry - (
                    risk * self.risk_reward_3
                )
            }

        return {
            "TP1": None,
            "TP2": None,
            "TP3": None
        }

    def calculate_risk_reward(
        self,
        entry,
        stop_loss,
        take_profit
    ):
        """
        Calculate risk/reward ratio.
        """

        risk = abs(
            entry - stop_loss
        )

        reward = abs(
            take_profit - entry
        )

        if risk <= 0:
            return 0.0

        return round(
            reward / risk,
            2
        )

    def build_trade_plan(
        self,
        market,
        timeframe,
        direction,
        entry,
        swing_high=None,
        swing_low=None,
        confidence=0,
        reason=None
    ):
        """
        Build a complete proposed trade plan.
        """

        entry = float(entry)

        stop_loss = self.calculate_stop_loss(
            direction=direction,
            entry=entry,
            swing_high=swing_high,
            swing_low=swing_low
        )

        if stop_loss is None:
            return {
                "success": False,
                "message": "Unable to calculate stop loss"
            }

        take_profits = self.calculate_take_profits(
            direction=direction,
            entry=entry,
            stop_loss=stop_loss
        )

        rr = self.calculate_risk_reward(
            entry=entry,
            stop_loss=stop_loss,
            take_profit=take_profits["TP2"]
        )

        return {
            "success": True,

            "market": market,
            "timeframe": timeframe,

            "direction": direction,

            "entry": round(
                entry,
                5
            ),

            "stop_loss": round(
                stop_loss,
                5
            ),

            "TP1": round(
                take_profits["TP1"],
                5
            ),

            "TP2": round(
                take_profits["TP2"],
                5
            ),

            "TP3": round(
                take_profits["TP3"],
                5
            ),

            "risk_reward": rr,

            "confidence": round(
                float(confidence),
                2
            ),

            "reason": reason or [],

            "status": "PROPOSED"
        }

    @staticmethod
    def validate_plan(plan):
        """
        Basic validation of a proposed trade plan.
        """

        if not plan.get("success"):
            return False

        entry = plan.get("entry")
        stop_loss = plan.get("stop_loss")
        tp1 = plan.get("TP1")

        direction = plan.get("direction")

        if None in (
            entry,
            stop_loss,
            tp1
        ):
            return False

        if direction == "BUY":

            if stop_loss >= entry:
                return False

            if tp1 <= entry:
                return False

        elif direction == "SELL":

            if stop_loss <= entry:
                return False

            if tp1 >= entry:
                return False

        else:
            return False

        return True