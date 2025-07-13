from flask import Flask, jsonify, request, render_template
import traceback,sys,signal,time,threading,time
from dashboard_data.SQL_DB_DashboardData import SQL_DB_DashboardData
from CONFIG import Config
from COIN.coin_model import Coin ,ALL_Coins
from flask_cors import CORS # Import CORS

app = Flask(__name__, template_folder="templates")
CORS(app) # Enable CORS for all routes

import logging
logging.getLogger('werkzeug').setLevel(logging.ERROR)

coins_lock = threading.Lock()



def trading_loop():
    try:
        last_prices = {}  # שמור את המחיר האחרון של כל מטבע בזיכרון
        while True:
            start_time = time.time()
            with coins_lock:
                for coin_obj in ALL_Coins.Coins :
                    coin_obj.process_coin()


            elapsed_time = time.time() - start_time
            sleep_time = max(0, Config.CYCLE_INTERVAL - elapsed_time)
            time.sleep(sleep_time)

    except Exception as e:
        print(f"Trading loop encountered an exception: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        sys.stdout.flush()

def handle_exit(signum, frame):
    print("Program is exiting. Cleaning up...")
    sys.exit(0)

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
            result = SQL_DB_DashboardData.load_all_data(Config.SYMBOLS, Config.HISTORY_LIMIT)
    except Exception as e:
        print(f"Error loading live data: {e}")
        traceback.print_exc()
        return jsonify({"error": "Failed to load live data"}), 500
    if not result:
        return jsonify({"error": "No data available"}), 404
    # Convert datetime objects to strings for JSON serialization
    return jsonify({"data": result, "cycle_interval": Config.CYCLE_INTERVAL})

@app.route("/api/transactions/<symbol>", methods=["GET"])
def get_transactions(symbol):
    symbol = symbol.upper()
    trades = SQL_DB_DashboardData.load_trades(symbol, Config.HISTORY_LIMIT)
    transactions = []
    for action, price, timestamp, reason, signal, net_profit in trades:
        transactions.append({
            "action": action,
            "price": price,
            "timestamp": timestamp,
            "reason": reason,
            "signal": signal,
            "net_profit": net_profit
        })
    return jsonify(transactions)

@app.route("/api/reset_trades", methods=["POST"])
def reset_all_trades():
    print("RESET TRADES API CALLED")
    with coins_lock:
        for coin in ALL_Coins.Coins:
            coin.trade_manager.reset_trades()
            coin.reset_coin()
    return {"status": "all trades reset successfully"}

@app.route("/api/n8n_hook", methods=["POST"])
def n8n_hook():
    data = request.get_json()
    if not data or "symbols" not in data:
        return {"error": "Invalid data"}, 400
    symbols = data["symbols"]
    if not isinstance(symbols, list):
        return {"error": "Symbols must be a list"}, 400

    return {"status": "configuration updated", "symbols": Config.SYMBOLS}

if __name__ == "__main__":
    import traceback

    print("Entering __main__ block.") # Log start of main
    try:
        print("Initializing coins...") # Log coin initialization start
        for symbol in Config.SYMBOLS:
            symbol = Coin(symbol)
        print(f"Successfully initialized coins: {Config.SYMBOLS}") # Log successful initialization
        SQL_DB_DashboardData.restore_all_data()  # Restore all data from SQLite
        print("Coins initialized successfully.") # Log successful initialization
    except Exception as e:
        print(f"Error initializing coins: {e}")
        print(f"Traceback: {traceback.format_exc()}")

    signal.signal(signal.SIGINT, handle_exit)  # Handle Ctrl+C
    signal.signal(signal.SIGTERM, handle_exit)  # Handle termination signals
    print("Starting trading loop thread...") # Log thread start
    try:
        trading_thread = threading.Thread(target=trading_loop, daemon=True)
        trading_thread.start()
        print("Trading loop thread started.") # Log thread started successfully
    except Exception as e:
        print(f"Error starting trading loop thread: {e}")
        print(f"Traceback: {traceback.format_exc()}")

    try:
        print("Starting Flask app...") # Log Flask app start
        app.run(host="0.0.0.0",port=Config.PORT, debug=Config.DEBUG if Config.DEBUG else False ,use_reloader=False )
    except Exception as e:
        print(f"Error running Flask app: {e}")
        print(f"Traceback: {traceback.format_exc()}")
