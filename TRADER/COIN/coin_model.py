from CONFIG import Config
from collections import deque
import time,os,sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo
from strategy.SignalDecisionEngine import SignalDecisionEngine
from strategy.TradeManager import TradeManager
from dashboard_data.SQL_DB_DashboardData import SQL_DB_DashboardData
import traceback
from strategy.MarketStatsCalculator import MarketStatsCalculator # Moved import to top

# Import SQL_DB_DashboardData only inside methods to avoid circular import

# =====================================================
# Coin אובייקט
# =====================================================
class Coin:
    def __init__(self, symbol):
        self.symbol = symbol

        # Use Config from CONFIG.py
        # Initialize SignalDecisionEngine and TradeManager with correct imports
        self.orderbooks = {ex: {"bids": [], "asks": []} for ex in ["binance", "bybit", "okx"]}
        self.calc = MarketStatsCalculator(self)
        self.signal_state = SignalDecisionEngine(self,self.calc)
        self.trade_manager = TradeManager(self)
        self.is_in_bought_Position = False
        self.buyed_price = 0.0
        self.med_price_history = deque(maxlen=Config.HISTORY_LIMIT)  # Initialize med_price_history
        self.binance_history = deque(maxlen=Config.HISTORY_LIMIT)  # Initialize binance_history
        self.bybit_history =deque(maxlen=Config.HISTORY_LIMIT)   # Initialize bybit_history
        self.okx_history = deque(maxlen=Config.HISTORY_LIMIT)   # Initialize okx_history     # Initialize okx_history
        self.current_profit = 0.0
        self.last_buy_time = ""  # Initialize last_buy_time

        self.total_buy_trades = 0
        self.total_sell_trades = 0
        self.total_profit = 0.0
        # New variables to store processed data as class members
        self.med_price = 0.0
        self.binance_price = 0.0
        self.bybit_price = 0.0
        self.okx_price = 0.0
        # New variables to store previous prices
        self.prev_med_price = 0.0
        self.prev_binance_price = 0.0
        self.prev_bybit_price = 0.0
        self.prev_okx_price = 0.0
        self.signal = "UNKNOWN"
        self.last_time_str = ""
        ALL_Coins.Coins.append(self)  # Add this coin to the static list
        


#####################################################################
# Process data for the coin, fetch from Config.EXCHANGES, analyze signals, and manage trades
#####################################################################
    # This method is called to process the coin's data, fetch from Config.EXCHANGES, analyze signals
    # and manage trades. It updates the coin's state based on the latest data.
    def reset_coin(self):
        for attr, value in self.__dict__.items():
            if isinstance(value, int):
                setattr(self, attr, 0)
            elif isinstance(value, float):
                setattr(self, attr, 0.0)
            elif isinstance(value, list):
                setattr(self, attr, [])
            elif isinstance(value, bool):
                setattr(self, attr, False)
            else:
                continue  # Skip unsupported types
                

    def process_coin(self):
        try:
            now = time.time()
            books = {}
            fanched = False
            for ex, connector in Config.EXCHANGES.items():
                try:
                    fetched = connector.fetch(self.symbol)
                    self.orderbooks[ex] = fetched
                    self.last_time_str = datetime.fromtimestamp(now, ZoneInfo("Asia/Jerusalem")).strftime("%H:%M:%S")
                    fanched = True
                except Exception as e:
                    print(f"Coin.process_coin: Error fetching data from {ex} for {self.symbol}: {e}")
                    books[ex] = None  # Continue even if one exchange fails
                    continue
            if not fanched:
                print(f"no data fetched for any exchange market for {self.symbol}")
                return
            


            med_price = self.calc.calculate_med_price()
            binance_price = self.calc.binance_price()
            bybit_price = self.calc.bybit_price()
            okx_price = self.calc.okx_price()
            if med_price is not None and med_price > 0:
                self.prev_med_price =self.med_price
                self.med_price = med_price
                self.med_price_history.append((now,self.med_price))
            else:
                print(f"Coin.process_coin: Invalid med_price for {self.symbol}: {med_price}")
                return
            if binance_price is not None and med_price > 0:
                self.prev_binance_price =self.binance_price
                self.binance_price = binance_price
                self.binance_history.append((now, self.binance_price))
            else:
                print(f"Coin.process_coin: Invalid binance_price for {self.symbol}: {binance_price}")
                return
            if bybit_price is not None and med_price > 0:
                self.prev_bybit_price =self.bybit_price
                self.bybit_price = bybit_price
                self.bybit_history.append((now, self.bybit_price))
            else:
                print(f"Coin.process_coin: Invalid bybit_price for {self.symbol}: {bybit_price}")
                return
            if okx_price is not None and med_price > 0:
                self.prev_okx_price =self.okx_price
                self.okx_price = okx_price
                self.okx_history.append((now, self.okx_price))
            else:
                print(f"Coin.process_coin: Invalid okx_price for {self.symbol}: {okx_price}")
                return

            if len(self.med_price_history) < Config.HISTORY_LIMIT:
                progress = f"{(len(self.med_price_history)/Config.HISTORY_LIMIT)*100:.4f}%"
                self.signal= progress
                print(f"Coin.process_coin: Progress for {self.symbol}: {progress} [{self.prev_med_price}  {self.med_price}]")
                return
            
            signal=self.signal_state.analyze(now)
            self.signal = signal.name if signal else "NO_SIGNAL"
            if  self.prev_med_price != self.med_price :
                self.trade_manager.check_selling_cond()
                self.trade_manager.check_buying_cond()
                SQL_DB_DashboardData.save_all_data(self)


        
        except Exception as e:
            # Log the error and set class members to error states
            print(f"Coin.process_coin: Error processing coin {self.symbol}: {e}")
            traceback.print_exc()  # Print the full traceback for debugging

            
            self.med_price = 0.0
            self.binance_price = 0.0
            self.bybit_price = 0.0
            self.okx_price = 0.0
            self.signal = "ERROR"
            self.last_time_str = datetime.now(ZoneInfo("Asia/Jerusalem")).strftime("%H:%M:%S")
            # No return statement here anymore

    def init_table_status_data(self):
        db_path = os.path.join("LOGS",f"{self.symbol}_status_data.db")
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        # Ensure table exists before INSERT or UPDATE
        c.execute("""
                CREATE TABLE IF NOT EXISTS status_data_main_table (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT,
                    buyed_price REAL DEFAULT 0.0,
                    is_in_bought_Position INTEGER DEFAULT 0,
                    total_profit REAL DEFAULT 0.0,
                    last_time_str TEXT DEFAULT ""
                )
            """)
        conn.commit()
        conn.close()
        time.sleep(0.1)  # Ensure table creation is committed

    def restore_status_data(self):
        self.init_table_status_data()
        db_path = os.path.join("LOGS",f"{self.symbol}_status_data.db")
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        # Ensure table exists before SELECT

        c.execute("""
            SELECT buyed_price, is_in_bought_Position, total_profit, last_time_str
            FROM status_data_main_table
            WHERE symbol = ?
        """, (self.symbol,))
        row = c.fetchone()
        conn.close()
        if row:
            self.buyed_price, is_in_bought_Position, self.total_profit, self.last_time_str = row
            self.is_in_bought_Position = bool(is_in_bought_Position)
            print(f"Restored status data for {self.symbol}: buyed_price={self.buyed_price}, is_in_bought_Position={self.is_in_bought_Position}, total_profit={self.total_profit}, last_time_str={self.last_time_str}")
            return True
        else:
            print(f"No status data found for {self.symbol} in {db_path}")
            return False

    def save_status_data(self):
        db_path = os.path.join("LOGS",f"{self.symbol}_status_data.db")
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        # Ensure table exists before INSERT or UPDATE
        self.init_table_status_data()
        
        c.execute("""
            UPDATE status_data_main_table
            SET buyed_price = ?, is_in_bought_Position = ?, total_profit = ?, last_time_str = ?
            WHERE symbol = ?
        """, (self.buyed_price, int(self.is_in_bought_Position), self.total_profit, self.last_time_str, self.symbol))
        if c.rowcount == 0:
            # No row updated, insert new row
            c.execute("""
                INSERT INTO status_data_main_table (symbol, buyed_price, is_in_bought_Position, total_profit, last_time_str)
                VALUES (?, ?, ?, ?, ?)
            """, (self.symbol, self.buyed_price, int(self.is_in_bought_Position), self.total_profit, self.last_time_str))
        conn.commit()
        conn.close()


##########################################################
#          Static Methods for Dashboard Data
##########################################################
   
    

class ALL_Coins:
    """
    Static class to manage all Coin instances.
    """
    Coins = []
    @staticmethod
    def print_all_coins():
        return f"\tALL_Coins:->  [{'| '.join(coin.symbol for coin in ALL_Coins.Coins)} ]"
  
