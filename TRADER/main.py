from flask import Flask, jsonify, request, render_template
import traceback, sys, signal, time, multiprocessing, threading
from dashboard_data.SQL_DB_DashboardData import SQL_DB_DashboardData
from CONFIG import Config
from COIN.coin_model import Coin, ALL_Coins
from flask_cors import CORS
import logging
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

reset=False
@app.route("/api/live", methods=["GET"])
def live_data():
    global reset
    try:
        with coins_lock:
            result = SQL_DB_DashboardData.load_all_data(Config.SYMBOLS, Config.HISTORY_LIMIT)
            if reset:
                print("No data found, initializing with empty structure.")
                result = None
    except Exception as e:
        print(f"Error loading live data: {e}\n{traceback.format_exc()}")
        return jsonify({"error": "Failed to load live data"}), 500
    if not result:
        print("No data found, initializing with empty structure.")
        print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<,")
        result = {}
        for symbol in Config.SYMBOLS:
            result[symbol] = {
                "symbol": symbol,
                "binance_price": 0.0,
                "momentum": 0.0,
                "buy_pressure": 0.0,
                "sell_pressure": 0.0,
                "signal": "No Signal",
                "position": "No Position",
                "pnl_pct": 0.0,
                "total_buy_trades": 0,
                "total_sell_trades": 0,
                "total_profit": 0.0,
                "trades": []
            }
    else:
        for symbol in Config.SYMBOLS:
            if result[symbol].get("momentum")== 0.0 and result[symbol].get("buy_pressure") == 0.0 and result[symbol].get("sell_pressure") == 0.0:
                result[symbol].update({
                    "symbol": symbol,
                    "momentum": 0.0,
                    "buy_pressure": 0.0,
                    "sell_pressure": 0.0,
                    "signal": "אוסף נתונים",
                    "position": f"{(len(result[symbol].get('price_history', []))/Config.HISTORY_LIMIT)*100:.2f}% ",
                    "pnl_pct": 0.0,
                    "total_buy_trades": 0,
                    "total_sell_trades": 0,
                    "total_profit": 0.0,
                    "trades": []
            })
    return jsonify({"data": result, "cycle_interval": Config.CYCLE_INTERVAL})

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
    global reset
    reset = True
    try:
        with coins_lock:
            for coin in ALL_Coins.Coins:
                coin.trade_manager.reset_trades()
                coin.reset_coin()
                SQL_DB_DashboardData.reset_trades_sqlite()
                reset = False
    except Exception as e:
        reset = False
        print(f"Error resetting trades: {e}\n{traceback.format_exc()}")
        return {"error": "Failed to reset trades"}, 500
    return {"status": "all trades reset successfully"}

@app.route("/api/n8n_hook", methods=["POST"])
def n8n_hook():
    data = request.get_json()
    if not data or "symbols" not in data or not isinstance(data["symbols"], list):
        return {"error": "Invalid data, symbols must be a list"}, 400
    # עדכון קונפיג (אם תרצה)
    # Config.SYMBOLS = data["symbols"]
    return {"status": "configuration updated", "symbols": Config.SYMBOLS}

# --- אתחול המערכת (פעם אחת בלבד) ---
print("Initializing coins...")
try:
    for symbol in Config.SYMBOLS:
        Coin(symbol)
    SQL_DB_DashboardData.restore_all_data()
    print(f"Successfully initialized coins: {Config.SYMBOLS}")
except Exception as e:
    print(f"Error initializing coins: {e}\n{traceback.format_exc()}")

print("Starting trading loop thread...")
trading_thread = threading.Thread(target=trading_loop, daemon=True)
trading_thread.start()
print("Trading loop thread started successfully.")

# Note: If you use a production WSGI server like Gunicorn,
# you will point it to this 'app' object (e.g., gunicorn --bind 0.0.0.0:7070 'app:app')