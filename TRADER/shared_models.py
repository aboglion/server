# =====================================================
# shared_models_refactored.py – גרסה משופרת ומודולרית
# =====================================================

import  time, json, sqlite3
from datetime import datetime


# =====================================================
# קונפיגורציה – דינמית ומוכנה ל־API/N8N
# =====================================================

# =====================================================
# איתותים
# =====================================================


# =====================================================
# מחשבון ניתוח שוק (תנודתיות, לחץ וכו')
# =====================================================

# =====================================================
# מחליט איתותים
# =====================================================

# =====================================================
# Coin אובייקט
# =====================================================

# =====================================================
# TradeManager – קנייה/מכירה
# =====================================================


# =====================================================
# SQLite DB
# =====================================================
class DBManager:
    def __init__(self, db_name=None):
        self.db_name = db_name or Config.DB_NAME
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute("""
            CREATE TABLE IF NOT EXISTS market_data (
                id INTEGER PRIMARY KEY,
                run_key TEXT, timestamp INTEGER, symbol TEXT,
                med_price REAL, volatility REAL, momentum REAL,
                buy_pressure_ratio REAL, sell_pressure_ratio REAL,
                signal_type TEXT, orderbooks_json TEXT,
                UNIQUE(run_key, timestamp, symbol)
            )""")
            conn.commit()

    def save_data_point(self, run_key, coin):
        if len(coin.med_price_history) < Config.VOLATILITY_WINDOW:
            return
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute("""
                INSERT OR IGNORE INTO market_data (
                    run_key, timestamp, symbol,
                    med_price, volatility, momentum,
                    buy_pressure_ratio, sell_pressure_ratio,
                    signal_type, orderbooks_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    run_key, int(time.time()), coin.symbol,
                    coin.signal_state.med_price,
                    coin.signal_state.volatility,
                    coin.signal_state.momentum,
                    coin.signal_state.buy_pressure,
                    coin.signal_state.sell_pressure,
                    coin.signal_state.last_decision.name,
                    json.dumps(coin.orderbooks)
                ))
            conn.commit()

    def generate_run_key(self):
        return datetime.now().strftime("%Y%m%d_%H%M%S")
