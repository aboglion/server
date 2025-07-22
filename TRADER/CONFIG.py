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
    CYCLE_INTERVAL = 10
    HISTORY_LIMIT = int((15 * 60) / CYCLE_INTERVAL)
    
    # -- Technical Indicator Windows --
    MOMENTUM_WINDOW = min(15, HISTORY_LIMIT)  
    PRESSURE_WINDOW = min(30, HISTORY_LIMIT)
    MOMENTUM_WINDOW_LONG = 30
    VOLUME_WINDOW = 60
    VOLATILITY_WINDOW = int(HISTORY_LIMIT / 1.5)

    # -- Trade Decision Thresholds --
    BASE_DECISION_THRESHOLD = 2  #momentum threshold for trade decisions
    
    # -- Risk Management Parameters (UPDATED) --
    FEE = 0.001                     # 0.1% fee per trade

    TAKE_PROFIT_PCT = 0.005         # ✅ יעד רווח של 1.2%
    STOP_LOSS_PCT = 0.017           # ✅ סטופ-לוס הורחב ל-1.0% למניעת יציאה מוקדמת
    MIN_RISK_REWARD_RATIO = 1.0     # ✅ סף מינימלי של 1:1 ליחס סיכון-סיכוי

    # -- Volatility Filter for Scalping (NEW) --
    MIN_VOLATILITY_FOR_SCALPING = 0.0001  # 📉 לא לסחור אם התנודתיות נמוכה-0.
    MAX_VOLATILITY_FOR_SCALPING = 2  # 📈 לא לסחור אם התנודתיות גבוהה-2.

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