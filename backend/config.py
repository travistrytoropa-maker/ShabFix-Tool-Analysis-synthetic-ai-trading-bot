"""
Central configuration for the Synthetic AI Trading Bot.
"""

# ==========================================
# APPLICATION
# ==========================================

APP_NAME = "Synthetic AI Trading Bot"

APP_VERSION = "1.0.0"

DEBUG = False


# ==========================================
# DERIV
# ==========================================

DERIV_WS_URL = "wss://ws.derivws.com/websockets/v3"

# Optional.
# The application can use public market-data
# requests without authentication.
DERIV_APP_ID = None


# ==========================================
# TARGET MARKETS
# ==========================================

TARGET_MARKETS = [
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


# ==========================================
# TIMEFRAMES
# ==========================================

TIMEFRAMES = {
    "M5": 300,
    "M30": 1800,
    "H1": 3600
}


# ==========================================
# HISTORICAL DATA
# ==========================================

HISTORICAL_CANDLE_COUNT = 500

MINIMUM_CANDLES_REQUIRED = 50


# ==========================================
# ANALYSIS
# ==========================================

SWING_WINDOW = 2

ANALYSIS_INTERVAL_SECONDS = 20


# ==========================================
# SIGNAL ENGINE
# ==========================================

MINIMUM_CONFIDENCE = 70.0

MINIMUM_RISK_REWARD = 1.5


# ==========================================
# RISK ENGINE
# ==========================================

RISK_REWARD_TP1 = 1.5

RISK_REWARD_TP2 = 2.0

RISK_REWARD_TP3 = 3.0

STOP_LOSS_BUFFER_PERCENT = 0.001


# ==========================================
# SIGNAL CONTROL
# ==========================================

ALLOW_BUY_SIGNALS = True

ALLOW_SELL_SIGNALS = True

ALLOW_WAIT_SIGNALS = True


# ==========================================
# API
# ==========================================

HOST = "0.0.0.0"

PORT = 5000