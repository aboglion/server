import sqlite3
from datetime import datetime
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
            pnl_pct REAL,
            total_buy_trades INTEGER,
            total_sell_trades INTEGER,
            total_profit REAL,
            is_in_bought_Position BOOLEAN DEFAULT FALSE,
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
        initialize_dashboard_db()
        conn = sqlite3.connect(Config.DB_NAME)
        c = conn.cursor()

            # שמור סטטיסטיקות
        c.execute("""
                INSERT OR REPLACE INTO stats (
                    symbol, med_price, binance_price, bybit_price, okx_price, signal, last_time_str, current_profit,
                    momentum, buy_pressure, sell_pressure, position, pnl_pct, total_buy_trades, total_sell_trades, total_profit,is_in_bought_Position, buyed_price,last_buy_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?, ?, ?)
            """, (
                coin_obj.symbol,
                coin_obj.med_price,
                coin_obj.binance_price,
                coin_obj.bybit_price,
                coin_obj.okx_price,
                coin_obj.signal,
                coin_obj.last_time_str,
                coin_obj.current_profit,
                getattr(coin_obj.signal_state, 'momentum', 0.0),
                getattr(coin_obj.signal_state, 'buy_pressure', 0.0) ,
                getattr(coin_obj.signal_state, 'sell_pressure', 0.0),
                getattr(coin_obj.signal_state, 'position', ""),
                coin_obj.current_profit,
                coin_obj.total_buy_trades,
                coin_obj.total_sell_trades,
                coin_obj.total_profit,

                coin_obj.is_in_bought_Position,
                coin_obj.buyed_price,
                getattr(coin_obj, 'last_buy_time', "")
            ))
            # שמור price_history
        for ts, price in coin_obj.med_price_history:
            c.execute("""
                INSERT OR IGNORE INTO price_history (symbol, timestamp, price)
                VALUES (?, ?, ?)
            """, (coin_obj.symbol, ts, price))
        # שמור binance_history
        for ts, price in coin_obj.binance_history:
            c.execute("""
                INSERT OR IGNORE INTO binance_history (symbol, timestamp, price)
                VALUES (?, ?, ?)
            """, (coin_obj.symbol, ts, price))
        # שמור bybit_history
        for ts, price in coin_obj.bybit_history:
            c.execute("""
                INSERT OR IGNORE INTO bybit_history (symbol, timestamp, price)
                VALUES (?, ?, ?)
            """, (coin_obj.symbol, ts, price))
        # שמור okx_history
        for ts, price in coin_obj.okx_history:
            c.execute("""
                INSERT OR IGNORE INTO okx_history (symbol, timestamp, price)
                VALUES (?, ?, ?)
            """, (coin_obj.symbol, ts, price))
        conn.commit()
    
 

    # שאר הפונקציות נשארות ללא שינוי
    @staticmethod
    def load_all_data(symbols, history_limit=200):
        initialize_dashboard_db()
        conn = sqlite3.connect(Config.DB_NAME)
        c = conn.cursor()
        result = {}
        for symbol in symbols:
            c.execute("SELECT * FROM stats WHERE symbol=?", (symbol,))
            stats = c.fetchone()
            c.execute("SELECT timestamp, price FROM price_history WHERE symbol=? ORDER BY timestamp DESC LIMIT ?", (symbol, history_limit))
            price_history = c.fetchall()[::-1]
            c.execute("SELECT timestamp, price FROM binance_history WHERE symbol=? ORDER BY timestamp DESC LIMIT ?", (symbol, history_limit))
            binance_history = c.fetchall()[::-1]
            c.execute("SELECT timestamp, price FROM bybit_history WHERE symbol=? ORDER BY timestamp DESC LIMIT ?", (symbol, history_limit))
            bybit_history = c.fetchall()[::-1]
            c.execute("SELECT timestamp, price FROM okx_history WHERE symbol=? ORDER BY timestamp DESC LIMIT ?", (symbol, history_limit))
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
                "pnl_pct": stats[12] if stats else 0,
                "total_buy_trades": stats[13] if stats else 0,
                "total_sell_trades": stats[14] if stats else 0,
                "total_profit": stats[15] if stats else 0,
                "price_history": price_history,
                "binance_history": binance_history,
                "bybit_history": bybit_history,
                "okx_history": okx_history,
                "is_in_bought_Position": stats[16] if stats else False,
                "buyed_price": stats[17] if stats else 0.0,
                "last_buy_time": stats[18] if stats else "",
            }
        conn.close()
        return result

    @staticmethod
    def restore_all_data():
        """
        טוען את כל הנתונים עבור רשימת מטבעות.
        """
        initialize_dashboard_db()
        conn = sqlite3.connect(Config.DB_NAME)
        c = conn.cursor()

        from COIN.coin_model import ALL_Coins
        for coin_obj in ALL_Coins.Coins:
            if coin_obj.symbol not in Config.SYMBOLS:
                continue
            c.execute("SELECT * FROM stats WHERE symbol=?", (coin_obj.symbol,))
            data= SQL_DB_DashboardData.load_all_data(Config.SYMBOLS, Config.HISTORY_LIMIT)
            if data:
                coin_obj.med_price = data[coin_obj.symbol]["med_price"]
                coin_obj.binance_price = data[coin_obj.symbol]["binance_price"]
                coin_obj.bybit_price = data[coin_obj.symbol]["bybit_price"]
                coin_obj.okx_price = data[coin_obj.symbol]["okx_price"]
                coin_obj.signal = data[coin_obj.symbol]["signal"]
                coin_obj.last_time_str = data[coin_obj.symbol]["last_time_str"]
                coin_obj.current_profit = data[coin_obj.symbol]["current_profit"]
                coin_obj.total_buy_trades = data[coin_obj.symbol]["total_buy_trades"]
                coin_obj.total_sell_trades = data[coin_obj.symbol]["total_sell_trades"]
                coin_obj.total_profit = data[coin_obj.symbol]["total_profit"]
                coin_obj.med_price_history = data[coin_obj.symbol]["price_history"]
                coin_obj.binance_history = data[coin_obj.symbol]["binance_history"]
                coin_obj.bybit_history = data[coin_obj.symbol]["bybit_history"]
                coin_obj.okx_history = data[coin_obj.symbol]["okx_history"]
                coin_obj.is_in_bought_Position = data[coin_obj.symbol]["is_in_bought_Position"]   
                coin_obj.buyed_price = data[coin_obj.symbol]["buyed_price"]
                coin_obj.last_buy_time = data[coin_obj.symbol]["last_buy_time"]

    @staticmethod
    def record_trade(coin,action,reason=None):
        initialize_dashboard_db()
        conn = sqlite3.connect(Config.DB_NAME)
        c = conn.cursor()
        c.execute(
            "INSERT INTO trades (symbol, action, price, timestamp, reason, signal) VALUES (?, ?, ?, ?, ?, ?)",
            (coin.symbol, action, coin.binance_price, coin.last_time_str, reason, coin.signal)
        )
        conn.commit()
        # Log progress after recording a trade
        print(f"Trade recorded: {action} {coin.symbol} at {coin.binance_price} on {coin.last_time_str}")
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
    def print_exchange_error(exchange_name: str, error_message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {exchange_name.upper()} ERROR: {error_message}")

    @staticmethod
    def reset_trades_sqlite():
        """
        Reset all trades and graph data in the SQLite database.
        Only deletes from tables that exist.
        """
        initialize_dashboard_db()
        conn = sqlite3.connect(Config.DB_NAME)
        c = conn.cursor()
        tables = [row[0] for row in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        for table in ["trades", "price_history", "binance_history", "bybit_history", "okx_history", "stats"]:
            if table in tables:
                c.execute(f"DELETE FROM {table}")
        conn.commit()
        conn.close()
    