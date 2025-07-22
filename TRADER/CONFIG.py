# CONFIG.py
import os
from enum import Enum
from COIN.exchange_Connectors_Data import BinanceConnector, BybitConnector, OKXConnector

# =====================================================
# קונפיגורציה – דינמית ומוכנה ל־API/N8N
# =====================================================
class Config:
    """
    Class to hold all configuration parameters for the trading bot.
    Allows for easy tuning and dynamic adjustments.
    """
    # -- Exchange and Symbol Configuration --
    EXCHANGES = {"binance": BinanceConnector(), "bybit": BybitConnector(), "okx": OKXConnector()}
    SYMBOLS = ["BTCUSDT", "ETHUSDT", "XRPUSDT", "SOLUSDT"]

    # -- Timing and Data History --
    CYCLE_INTERVAL = 10  # Interval in seconds for processing coins.
    HISTORY_LIMIT = int((15 * 60) / CYCLE_INTERVAL)  # Data retention for 15 minutes.
    
    # -- Technical Indicator Windows --
    # Shorter window for recent, fast-changing momentum
    MOMENTUM_WINDOW =min(15,HISTORY_LIMIT)  
    # Medium window for pressure calculation, to get a stable trend
    PRESSURE_WINDOW = min(30, HISTORY_LIMIT)  # 30 seconds
    # Longer window for long-term momentum, to capture broader trends
    MOMENTUM_WINDOW_LONG = 30
    # Longer window for volume trend, to identify significant market activity shifts
    VOLUME_WINDOW = 60
    # Window for volatility calculation, based on historical price changes
    VOLATILITY_WINDOW = int(HISTORY_LIMIT / 1.5)

    # -- Trade Decision Thresholds --
    # The base score required to trigger a signal. Range: 0 to 1.
    # Higher value means the bot is more "picky" and waits for stronger signals.
    BASE_DECISION_THRESHOLD = 1.7
    
    # -- Risk Management Parameters (CRITICAL) --
    # The fee per trade (buy or sell). 0.1% = 0.001
    FEE = 0.001 
    # Take Profit percentage. A 1.2% target profit from the entry price.
    TAKE_PROFIT_PCT = 0.012 # 1.2%
    # Stop Loss percentage. A 0.8% max loss from the entry price.
    STOP_LOSS_PCT = 0.008 # 0.8%
    # Minimum required Risk/Reward ratio to enter a trade.
    # 0.25 means the potential profit must be at least 4 times the potential loss.
    MIN_RISK_REWARD_RATIO = 0.25  # 0.25 = 1:4הפסד ratio

    # -- System and Database --
    DB_NAME = os.path.join(os.path.dirname(__file__), "dashboard_data", "DashboardData.db")
    PORT = 7070
    DEBUG = True


# =====================================================
# Signal Types Enum
# =====================================================
class SignalType(Enum):
    """
    Represents the possible trading signals.
    """
    BUY = "BUY"
    SELL = "SELL"
    NEUTRAL = "NEUTRAL"