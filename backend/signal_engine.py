class SignalEngine:
    """
    Final signal decision layer.

    Converts analysis into:
    BUY
    SELL
    WAIT

    This engine does not execute trades.
    """

    def __init__(
        self,
        minimum_confidence=70.0,
        minimum_risk_reward=1.5
    ):
        self.minimum_confidence = (
            minimum_confidence
        )

        self.minimum_risk_reward = (
            minimum_risk_reward
        )

    def validate_direction(
        self,
        direction
    ):
        return direction in {
            "BUY",
            "SELL"
        }

    def validate_confidence(
        self,
        confidence
    ):
        return (
            float(confidence)
            >= self.minimum_confidence
        )

    def validate_risk_reward(
        self,
        trade_plan
    ):
        if not trade_plan:
            return False

        if not trade_plan.get("success"):
            return False

        rr = trade_plan.get(
            "risk_reward",
            0
        )

        return (
            float(rr)
            >= self.minimum_risk_reward
        )

    def check_timeframe_alignment(
        self,
        analysis,
        direction
    ):
        """
        Check whether H1, M30 and M5 agree
        with the proposed direction.
        """

        expected = (
            "BULLISH"
            if direction == "BUY"
            else "BEARISH"
        )

        timeframes = analysis.get(
            "timeframes",
            {}
        )

        aligned = 0

        for timeframe in [
            "H1",
            "M30",
            "M5"
        ]:

            result = timeframes.get(
                timeframe,
                {}
            )

            trend = (
                result
                .get("structure", {})
                .get("trend")
            )

            if trend == expected:
                aligned += 1

        return aligned >= 2

    def find_confirming_pattern(
        self,
        analysis,
        direction
    ):
        """
        Look for a recent M5 pattern that
        agrees with the proposed direction.
        """

        m5 = (
            analysis
            .get("timeframes", {})
            .get("M5", {})
        )

        patterns = m5.get(
            "patterns",
            []
        )

        if direction == "BUY":

            valid = {
                "HAMMER",
                "BULLISH_MOMENTUM",
                "BULLISH_REJECTION",
                "BULLISH_ENGULFING",
                "MORNING_STAR"
            }

        elif direction == "SELL":

            valid = {
                "SHOOTING_STAR",
                "BEARISH_MOMENTUM",
                "BEARISH_REJECTION",
                "BEARISH_ENGULFING",
                "EVENING_STAR"
            }

        else:
            return None

        for item in reversed(patterns):

            pattern = item.get(
                "pattern"
            )

            if pattern in valid:
                return pattern

        return None

    def evaluate(
        self,
        analysis_result
    ):
        """
        Evaluate the complete analysis result.
        """

        if not analysis_result:
            return {
                "signal": "WAIT",
                "approved": False,
                "reasons": [
                    "No analysis result"
                ]
            }

        direction = analysis_result.get(
            "direction",
            "WAIT"
        )

        confidence = float(
            analysis_result.get(
                "confidence",
                0
            )
        )

        trade_plan = (
            analysis_result.get(
                "trade_plan"
            )
        )

        analysis = (
            analysis_result.get(
                "analysis",
                {}
            )
        )

        reasons = []

        if not self.validate_direction(
            direction
        ):

            reasons.append(
                "No valid market direction"
            )

            return {
                "signal": "WAIT",
                "approved": False,
                "confidence": confidence,
                "reasons": reasons
            }

        if not self.validate_confidence(
            confidence
        ):

            reasons.append(
                f"Confidence below "
                f"{self.minimum_confidence}%"
            )

        else:

            reasons.append(
                "Confidence threshold passed"
            )

        aligned = (
            self.check_timeframe_alignment(
                analysis,
                direction
            )
        )

        if not aligned:

            reasons.append(
                "Timeframes are not sufficiently aligned"
            )

        else:

            reasons.append(
                "M5/M30/H1 structure aligned"
            )

        pattern = (
            self.find_confirming_pattern(
                analysis,
                direction
            )
        )

        if pattern:

            reasons.append(
                f"Confirming pattern: {pattern}"
            )

        else:

            reasons.append(
                "No strong M5 confirmation pattern"
            )

        if self.validate_risk_reward(
            trade_plan
        ):

            reasons.append(
                "Minimum risk/reward passed"
            )

        else:

            reasons.append(
                "Risk/reward requirement failed"
            )

        approved = (
            self.validate_confidence(
                confidence
            )
            and aligned
            and pattern is not None
            and self.validate_risk_reward(
                trade_plan
            )
        )

        if approved:

            return {
                "signal": direction,
                "approved": True,
                "confidence": confidence,
                "pattern": pattern,
                "trade_plan": trade_plan,
                "reasons": reasons,
                "status": "SIGNAL_READY"
            }

        return {
            "signal": "WAIT",
            "approved": False,
            "confidence": confidence,
            "pattern": pattern,
            "trade_plan": trade_plan,
            "reasons": reasons,
            "status": "NO_TRADE"
        }