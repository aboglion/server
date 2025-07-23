import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo
from CONFIG import Config
import os

def initialize_dashboard_db():
    db_path = Config.DB_NAME
    db_created = not os.path.exists(db_path)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # טבלת היסטוריית מחירים
    c.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            timestamp REAL,
            price REAL,
            UNIQUE(symbol, timestamp)
        )
    """)
    # טבלאות לכל בורסה
    for exchange in ["binance", "bybit", "okx"]:
        c.execute(f"""
            CREATE TABLE IF NOT EXISTS {exchange}_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                timestamp REAL,
                price REAL,
                UNIQUE(symbol, timestamp)
            )
        """)
    # טבלת עסקאות
    c.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            action TEXT,
            price REAL,
            timestamp TEXT,
            reason TEXT,
            signal TEXT,
            net_profit REAL
        )
    """)
    # טבלת סטטיסטיקות מורחבת
    c.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            symbol TEXT PRIMARY KEY,
            med_price REAL,
            binance_price REAL,
            bybit_price REAL,
            okx_price REAL,
            signal TEXT,
            last_time_str TEXT,
            current_profit REAL,
            momentum REAL,
            buy_pressure REAL,
            sell_pressure REAL,
            position TEXT,
            total_buy_trades INTEGER,
            total_sell_trades INTEGER,
            total_profit REAL,
            buyed_price REAL DEFAULT 0.0,
            last_buy_time TEXT DEFAULT ""
        )
    """)
    conn.commit()
    conn.close()
    if db_created:
        os.chmod(db_path, 0o664)

class SQL_DB_DashboardData:

    @staticmethod
    def save_all_data(coin_obj):
        """
        שמירה מסונכרנת: כל מטבע נשמר עם timestamp לפי last_time_str שלו.
        שמירה אחת בלבד כל 20 שניות לכל מטבע.
        """
        if not os.path.exists(Config.DB_NAME):
            print(f"Database {Config.DB_NAME} does not exist. Initializing...")
            initialize_dashboard_db()
            os.chmod(Config.DB_NAME, 0o664)

        conn = sqlite3.connect(Config.DB_NAME)
        c = conn.cursor()

        # שמור סטטיסטיקות
        c.execute("""
            INSERT OR REPLACE INTO stats (
                symbol, med_price, binance_price, bybit_price, okx_price,
                signal, last_time_str, current_profit, momentum,
                buy_pressure, sell_pressure, position,
                total_buy_trades, total_sell_trades, total_profit,
                buyed_price, last_buy_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            coin_obj.symbol,
            coin_obj.med_price,
            coin_obj.binance_price,
            coin_obj.bybit_price,
            coin_obj.okx_price,
            str(coin_obj.signal) if coin_obj.signal is not None else "None_SIGNAL",
            coin_obj.last_time_str,
            coin_obj.current_profit,
            float(coin_obj.signal_state.momentum) if coin_obj.signal_state.momentum is not None else 0.0,
            float(coin_obj.signal_state.buy_pressure) if coin_obj.signal_state.buy_pressure is not None else 0.0,
            float(coin_obj.signal_state.sell_pressure) if coin_obj.signal_state.sell_pressure is not None else 0.0,
            "[💰.IN]" if coin_obj.is_in_bought_Position else "[⏳.OUT]",
            coin_obj.total_buy_trades,
            coin_obj.total_sell_trades,
            coin_obj.total_profit,
            coin_obj.buyed_price,
            coin_obj.last_buy_time
        ))

        # price history
        for ts, price in coin_obj.med_price_history:
            c.execute("""
                INSERT OR IGNORE INTO price_history (symbol, timestamp, price)
                VALUES (?, ?, ?)
            """, (coin_obj.symbol, ts, price))

        # binance
        for ts, price in coin_obj.binance_history:
            c.execute("""
                INSERT OR IGNORE INTO binance_history (symbol, timestamp, price)
                VALUES (?, ?, ?)
            """, (coin_obj.symbol, ts, price))

        # bybit
        for ts, price in coin_obj.bybit_history:
            c.execute("""
                INSERT OR IGNORE INTO bybit_history (symbol, timestamp, price)
                VALUES (?, ?, ?)
            """, (coin_obj.symbol, ts, price))

        # okx
        for ts, price in coin_obj.okx_history:
            c.execute("""
                INSERT OR IGNORE INTO okx_history (symbol, timestamp, price)
                VALUES (?, ?, ?)
            """, (coin_obj.symbol, ts, price))

        conn.commit()
        conn.close()

    
 

    @staticmethod
    def load_all_data(symbols=Config.SYMBOLS, history_limit=Config.HISTORY_LIMIT):
        initialize_dashboard_db()
        conn = sqlite3.connect(Config.DB_NAME)
        c = conn.cursor()
        result = {}

        for symbol in symbols:
            c.execute("SELECT * FROM stats WHERE symbol=?", (symbol,))
            stats = c.fetchone()

            c.execute("""
                SELECT timestamp, price FROM price_history
                WHERE symbol=? ORDER BY timestamp DESC LIMIT ?
            """, (symbol, history_limit))
            price_history = c.fetchall()[::-1]

            c.execute("""
                SELECT timestamp, price FROM binance_history
                WHERE symbol=? ORDER BY timestamp DESC LIMIT ?
            """, (symbol, history_limit))
            binance_history = c.fetchall()[::-1]

            c.execute("""
                SELECT timestamp, price FROM bybit_history
                WHERE symbol=? ORDER BY timestamp DESC LIMIT ?
            """, (symbol, history_limit))
            bybit_history = c.fetchall()[::-1]

            c.execute("""
                SELECT timestamp, price FROM okx_history
                WHERE symbol=? ORDER BY timestamp DESC LIMIT ?
            """, (symbol, history_limit))
            okx_history = c.fetchall()[::-1]

            result[symbol] = {
                "symbol": symbol,
                "med_price": stats[1] if stats else None,
                "binance_price": stats[2] if stats else None,
                "bybit_price": stats[3] if stats else None,
                "okx_price": stats[4] if stats else None,
                "signal": stats[5] if stats else None,
                "last_time_str": stats[6] if stats else None,
                "current_profit": stats[7] if stats else None,
                "momentum": stats[8] if stats else None,
                "buy_pressure": stats[9] if stats else None,
                "sell_pressure": stats[10] if stats else None,
                "position": stats[11] if stats else None,
                "total_buy_trades": stats[12] if stats else 0,
                "total_sell_trades": stats[13] if stats else 0,
                "total_profit": stats[14] if stats else 0.0,
                "buyed_price": stats[15] if stats else 0.0,
                "last_buy_time": stats[16] if stats else "",

                "price_history": price_history,
                "binance_history": binance_history,
                "bybit_history": bybit_history,
                "okx_history": okx_history,
            }

        conn.close()
        return result


   
                
    @staticmethod
    def record_trade(coin,action,reason=None):
        initialize_dashboard_db()
        conn = sqlite3.connect(Config.DB_NAME)
        c = conn.cursor()

        c.execute(
            "INSERT INTO trades (symbol, action, price, timestamp, reason, signal, net_profit) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (coin.symbol, action, coin.binance_price, coin.last_time_str, reason, coin.signal, coin.current_profit if action.lower() == "sell" else None)
        )
        conn.commit()

        conn.close()

    


    @staticmethod
    def load_trades(symbol, limit=200):
        initialize_dashboard_db()
        conn = sqlite3.connect(Config.DB_NAME)
        c = conn.cursor()
        c.execute("SELECT action, price, timestamp, reason, signal, net_profit FROM trades WHERE symbol=? ORDER BY id DESC LIMIT ?", (symbol, limit))
        rows = c.fetchall()
        conn.close()
        return rows[::-1]

   


    @staticmethod
    def reset_trades_sqlite():
        """
        Reset all trades and graph data in the SQLite database.
        Deletes all rows from relevant tables and removes the database file.
        """
        db_path = Config.DB_NAME
        # Close any open connections before deleting
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            tables = [row[0] for row in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            for table in ["trades", "price_history", "binance_history", "bybit_history", "okx_history", "stats"]:
                if table in tables:
                    c.execute(f"DELETE FROM {table}")
            conn.commit()
            conn.close()
        except Exception:
            pass
        # Remove the database file
        if os.path.exists(db_path):
            os.remove(db_path)
    