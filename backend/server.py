import os

from flask import Flask, jsonify

from .config import (
    APP_NAME,
    APP_VERSION,
    HOST,
    PORT,
    DERIV_APP_ID,
    TARGET_MARKETS
)

from .deriv import DerivClient
from .market_scanner import MarketScanner
from .analysis_engine import AnalysisEngine
from .signal_engine import SignalEngine


app = Flask(__name__)


# ==========================================
# ENGINE INITIALIZATION
# ==========================================

deriv = DerivClient(
    app_id=DERIV_APP_ID
)

scanner = MarketScanner(
    deriv
)

analyzer = AnalysisEngine(
    deriv
)

signal_engine = SignalEngine()


# ==========================================
# HOME
# ==========================================

@app.route("/")
def home():

    return jsonify({
        "application": APP_NAME,
        "version": APP_VERSION,
        "status": "online",
        "message": (
            "Synthetic AI Trading Bot backend "
            "is running."
        )
    })


# ==========================================
# HEALTH
# ==========================================

@app.route("/health")
def health():

    connected = (
        deriv.ws is not None
    )

    return jsonify({
        "status": "healthy",
        "deriv_connected": connected
    })


# ==========================================
# CONNECT TO DERIV
# ==========================================

@app.route("/connect")
def connect_deriv():

    result = deriv.connect()

    return jsonify(result)


# ==========================================
# DISCOVER MARKETS
# ==========================================

@app.route("/markets")
def markets():

    if deriv.ws is None:

        connection = deriv.connect()

        if not connection.get("success"):

            return jsonify({
                "success": False,
                "message": (
                    "Unable to connect to Deriv"
                ),
                "connection": connection
            }), 503

    result = scanner.find_target_markets()

    return jsonify(result)


# ==========================================
# ANALYZE ONE MARKET
# ==========================================

@app.route("/analysis/<symbol>")
def analysis(symbol):

    if deriv.ws is None:

        connection = deriv.connect()

        if not connection.get("success"):

            return jsonify({
                "success": False,
                "message": (
                    "Unable to connect to Deriv"
                ),
                "connection": connection
            }), 503

    result = analyzer.run(
        symbol=symbol
    )

    if not result.get("success"):

        return jsonify(result), 500

    signal = signal_engine.evaluate(
        result
    )

    return jsonify({
        "success": True,
        "analysis": result,
        "signal": signal
    })


# ==========================================
# CONFIGURATION
# ==========================================

@app.route("/config")
def configuration():

    return jsonify({
        "application": APP_NAME,
        "version": APP_VERSION,
        "markets": TARGET_MARKETS,
        "timeframes": [
            "M5",
            "M30",
            "H1"
        ],
        "status": "ready"
    })


# ==========================================
# SERVER
# ==========================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            PORT
        )
    )

    app.run(
        host=HOST,
        port=port,
        debug=False
    )