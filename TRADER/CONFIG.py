import  os
from enum import Enum
from COIN.exchange_Connectors_Data import BinanceConnector, BybitConnector, OKXConnector

# =====================================================
# קונפיגורציה – דינמית ומוכנה ל־API/N8N
# =====================================================
class Config:

    EXCHANGES = {"binance": BinanceConnector(),"bybit": BybitConnector(),"okx": OKXConnector() }
    SYMBOLS =  ["BTCUSDT", "ETHUSDT", "XRPUSDT", "SOLUSDT"]

    CYCLE_INTERVAL = 10  # Interval in seconds for processing coins
    HISTORY_LIMIT = int((7*60)/CYCLE_INTERVAL)  # Default retention time for graph data (7 minutes)

    MOMENTUM_WINDOW = int(HISTORY_LIMIT/4)
    VOLATILITY_WINDOW = int(HISTORY_LIMIT/2)  # Number of price points to calculate volatility
    BASE_THRESHOLD = 1.12
    MAX_VOL_ADJ = 0.25 # Maximum volatility adjustment to the base threshold

    Last_signals_len=6 # Number of last signals to consider for momentum calculation
    MIN_CONSEC_SIGNALS_postive = 3  # Minimum consecutive signals to consider a trade
    MIN_CONSEC_SIGNALS_negative = 4  # Minimum consecutive signals to consider a trade
    
    FEE = (0.15)/100  # Trading fee (0.15% for Binance, Bybit, OKX)
    TAKE_profit_PCT = (0.6)/100 # 0.6% take profit (profit after fee)
    STOP_LOSS_PCT = (1.7)/100 # 1.7% stop loss

    DB_NAME = os.path.join(os.path.dirname(__file__), "dashboard_data", "DashboardData.db")
    PORT = 7070
    DEBUG = True



# =====================================================
# איתותים
# =====================================================
class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    NEUTRAL = "NEUTRAL"





# MOMENTUM_WINDOW:
# לדוג' אם MOMENTUM_WINDOW=12, נשמרים 12 אותות אחרונים. אם רובם BUY, הבוט ייטה להוציא אות BUY.
# self.recent_signals = deque([SignalType.NEUTRAL] * Config.MOMENTUM_WINDOW, maxlen=Config.MOMENTUM_WINDOW)
# אם יש פחות מ־12 אותות, הבוט לא ייתן החלטה.
# אם יש יותר מ־12, הבוט ישמור רק את 12 האחרונים.
# =====================================================
# VOLATILITY_WINDOW:
# לדוג' אם VOLATILITY_WINDOW=24, הבוט יחשב תנודתיות על 24 מחירים ממוצעים אחרונים. אם יש פחות, לא תתבצע החלטה.
# if history_len < Config.VOLATILITY_WINDOW:
#     self.last_decision = SignalType.NEUTRAL
# =====================================================
# BASE_THRESHOLD:
# לדוג' אם BASE_THRESHOLD=1.08, לחץ קנייה צריך להיות מעל 1.08 כדי להוציא BUY.
# # אם לחץ מכירה מעל 1.08, הבוט ייתן אות SELL.
# אם לחץ קנייה ומכירה שניהם מעל 1.08, הבוט י
# threshold = Config.BASE_THRESHOLD + min(self.volatility * 100, Config.MAX_VOL_ADJ) * (1 + self.momentum)
# =====================================================
# MAX_VOL_ADJ:
# # לדוג' אם MAX_VOL_ADJ=0.25, התנודתיות לא תעלה את הסף יותר מ־0.25.
# אם התנודתיות גבוהה, הבוט יוסיף את התנודתיות לסף הבסיס, אך לא יעלה אותו יותר מ־0.25.
# לדוג' אם התנודתיות גבוהה, MAX_VOL_ADJ=0.25 מגביל את ההתאמה לסף, כך שלא יעלה יותר מ-0.25 מעל הבסיס.
# MIN_PCT_CHANGE:
# לדוג' אם השינוי במחיר קטן מ-0.00015 (0.015%), לא תתבצע עסקה גם אם התקבלו אותות רצופים.
# self.last_decision = final if pct_change >= Config.MIN_PCT_CHANGE else SignalType.NEUTRAL
# =====================================================
# MIN_PCT_CHANGE
# לדוג' אם MIN_PCT_CHANGE=0.00015, הבוט ידרוש שינוי של לפחות 0.00015 (0.015%) במחיר כדי לבצע עסקה.
# אם השינוי במחיר קטן מ־0.00015, הבוט לא ייתן
# החלטה גם אם יש אותות רצופים.
# =====================================================
# MIN_CONSEC_SIGNALS:
# לדוג' אם MIN_CONSEC_SIGNALS=2, הבוט ידרוש לפחות 2 אותות רצופים מאותו סוג כדי להוציא החלטה.
# אם יש פחות מ־2 אותות רצופים, הבוט לא ייתן החלטה.
# if self.consecutive >= Config.MIN_CONSEC_SIGNALS:
#     pct_change = abs(self.med_price - self.signal_price) / self.signal_price if self.signal_price > 0 else 0.0
#     self.last_decision = final if pct_change >= Config.MIN_PCT_CHANGE else SignalType.NEUTRAL         
# =====================================================






