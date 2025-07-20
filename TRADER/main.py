from flask import Flask, jsonify, request, render_template
import traceback, sys, signal, time, multiprocessing, threading
from dashboard_data.SQL_DB_DashboardData import SQL_DB_DashboardData
from CONFIG import Config
from COIN.coin_model import Coin, ALL_Coins
from flask_cors import CORS
import logging, os
from dashboard_data.SQL_DB_DashboardData import initialize_dashboard_db
initialize_dashboard_db()

# --- הגדרות האפליקציה ---
app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)
CORS(app)

logging.getLogger('werkzeug').setLevel(logging.ERROR)
coins_lock = multiprocessing.Lock()

# --- לולאת הטריידינג ---
def trading_loop():
    try:
        while True:
            start_time = time.time()
            with coins_lock:
                if os.path.exists("reset.flag"):
                    for coin in ALL_Coins.Coins:
                        coin.trade_manager.reset_trades()
                        coin.reset_coin()
                    SQL_DB_DashboardData.reset_trades_sqlite()
                    os.remove("reset.flag")
                    time.sleep(1)  # Give time for the reset to complete
                    continue
                for coin_obj in ALL_Coins.Coins:
                    coin_obj.process_coin()
            elapsed_time = time.time() - start_time
            sleep_time = max(0, Config.CYCLE_INTERVAL - elapsed_time)
            time.sleep(sleep_time)
    except Exception as e:
        print(f"Trading loop encountered an exception: {e}\n{traceback.format_exc()}")
        sys.stdout.flush()

# --- Routes של Flask ---
@app.route("/")
def dashboard():
    return render_template("dashboard.html", reload_time_loop=Config.CYCLE_INTERVAL)

@app.route("/api/ping")
def ping():
    return {"status": "alive"}

@app.route("/api/live", methods=["GET"])
def live_data():
    try:
        with coins_lock:
            if os.path.exists("reset.flag"):
                result =None
            else:
                # Load live data from SQLite
                result = SQL_DB_DashboardData.load_all_data()

    except Exception as e:
        print(f"Error loading live data: {e}\n{traceback.format_exc()}")
        return jsonify({"error": "Failed to load live data"}), 500
    if not result or any(coin.symbol not in result for coin in ALL_Coins.Coins):
            for coin in ALL_Coins.Coins:
                result[coin.symbol] = {
                    "symbol": coin.symbol,
                    "binance_price": 0.0,
                    "momentum": 0.0,
                    "buy_pressure": 0.0,
                    "sell_pressure": 0.0,
                    "signal":  "error loading data",
                    "position": "[💰_IN_@]" if coin.is_in_bought_Position else "[⏳_OUT_@]",
                    "pnl_pct": coin.current_profit if coin.is_in_bought_Position else 0.0,
                    "total_buy_trades": coin.total_buy_trades,
                    "total_sell_trades": coin.total_sell_trades,
                    "total_profit": coin.total_profit,
                    "trades": coin.trade_manager.trade_log if coin.trade_manager else []}
                print(f"collect data: {coin.symbol} - error loading data")
    else:
        for coin in ALL_Coins.Coins:
            pragsess = f"{(len(coin.med_price_history)/Config.HISTORY_LIMIT)*100:.4f}%"
            result[coin.symbol]["signal"] = pragsess
            if coin.symbol=="BTCUSDT":
                 print(f"[1] {coin.last_time_str} {coin}, {coin.med_price}, binance_price: {coin.binance_price}, bybit_price: {coin.bybit_price}, okx_price: {coin.okx_price}, signal: {coin.signal}")

    return (jsonify({"data": result, "cycle_interval": Config.CYCLE_INTERVAL}), 200)

@app.route("/trader/api/live", methods=["GET"])
def trader_live_data():
    print("trader_live_data")
    return live_data()

@app.route("/api/transactions/<symbol>", methods=["GET"])
def get_transactions(symbol):
    symbol = symbol.upper()
    trades = SQL_DB_DashboardData.load_trades(symbol, Config.HISTORY_LIMIT)
    transactions = []
    for action, price, timestamp, reason, signal, net_profit in trades:
        transactions.append({
            "action": action, "price": price, "timestamp": timestamp,
            "reason": reason, "signal": signal, "net_profit": net_profit
        })
    return jsonify(transactions)

@app.route("/api/reset_trades", methods=["POST"])
def reset_all_trades():
    try:
        with open("reset.flag", "w") as f:
            f.write("1")
    except Exception as e:
        print(f"Error creating reset flag file: {e}\n{traceback.format_exc()}")
        return {"error": "Failed to create reset flag file"}, 500
    return {"status": "all trades reset successfully"}

@app.route("/api/n8n_hook", methods=["POST"])
def n8n_hook():
    data = request.get_json()
    if not data or "symbols" not in data or not isinstance(data["symbols"], list):
        return {"error": "Invalid data, symbols must be a list"}, 400
    # עדכון קונפיג (אם תרצה)
    # Config.SYMBOLS = data["symbols"]
    return {"status": "configuration updated", "symbols": Config.SYMBOLS}


# --- Initialization for all environments (development & production) ---
print("Initializing coins...")
try:
    for symbol in Config.SYMBOLS:
        Coin(symbol)
    for coin in ALL_Coins.Coins:
        print(f"Successfully initialized coin: {coin.symbol}")
        coin.restore_status_data()
except Exception as e:
    print(f"Error initializing coins: {e}\n{traceback.format_exc()}")

print("Starting trading loop thread...")
trading_thread = threading.Thread(target=trading_loop, daemon=True)
trading_thread.start()
print("Trading loop thread started successfully.")

# Note: If you use a production WSGI server like Gunicorn,
# you will point it to this 'app' object (e.g., gunicorn --bind 0.0.0.0:7070 'app:app')