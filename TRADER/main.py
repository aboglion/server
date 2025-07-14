from flask import Flask, jsonify, request, render_template
from werkzeug.middleware.dispatcher import DispatcherMiddleware
import traceback, sys, signal, time, threading
from dashboard_data.SQL_DB_DashboardData import SQL_DB_DashboardData
from CONFIG import Config
from COIN.coin_model import Coin, ALL_Coins
from flask_cors import CORS

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

coins_lock = threading.Lock()

def trading_loop():
    try:
        last_prices = {}
        while True:
            start_time = time.time()
            with coins_lock:
                for coin_obj in ALL_Coins.Coins:
                    coin_obj.process_coin()
            time.sleep(max(0, Config.CYCLE_INTERVAL - (time.time() - start_time)))
    except Exception as e:
        print(f"Trading loop error: {e}\n{traceback.format_exc()}")

def handle_exit(signum, frame):
    print("Exiting...")
    sys.exit(0)

@app.route("/")
def dashboard():
    return render_template("dashboard.html", reload_time_loop=Config.CYCLE_INTERVAL)

@app.route("/api/ping")
def ping():
    return {"status": "alive"}

@app.route("/api/live")
def live_data():
    try:
        with coins_lock:
            result = SQL_DB_DashboardData.load_all_data(Config.SYMBOLS, Config.HISTORY_LIMIT)
    except Exception as e:
        print(f"Live data error: {e}")
        return jsonify({"error": "Failed to load live data"}), 500
    return jsonify({"data": result, "cycle_interval": Config.CYCLE_INTERVAL}) if result else ({"error": "No data"}, 404)

@app.route("/api/transactions/<symbol>")
def get_transactions(symbol):
    trades = SQL_DB_DashboardData.load_trades(symbol.upper(), Config.HISTORY_LIMIT)
    return jsonify([{
        "action": a, "price": p, "timestamp": t,
        "reason": r, "signal": s, "net_profit": np
    } for a, p, t, r, s, np in trades])

@app.route("/api/reset_trades", methods=["POST"])
def reset_all_trades():
    with coins_lock:
        for coin in ALL_Coins.Coins:
            coin.trade_manager.reset_trades()
            coin.reset_coin()
    return {"status": "all trades reset successfully"}

@app.route("/api/n8n_hook", methods=["POST"])
def n8n_hook():
    data = request.get_json()
    if not data or "symbols" not in data or not isinstance(data["symbols"], list):
        return {"error": "Invalid data"}, 400
    return {"status": "configuration updated", "symbols": Config.SYMBOLS}

# עטיפת האפליקציה כך שתפעל תחת /trader
application = DispatcherMiddleware(None, {
    '/trader': app
})

if __name__ == "__main__":
    import traceback
    print("Initializing...")
    try:
        for symbol in Config.SYMBOLS:
            symbol = Coin(symbol)
        SQL_DB_DashboardData.restore_all_data()
    except Exception as e:
        print(f"Init error: {e}\n{traceback.format_exc()}")
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
    threading.Thread(target=trading_loop, daemon=True).start()
    from werkzeug.serving import run_simple
    run_simple('0.0.0.0', Config.PORT, application, use_reloader=False, use_debugger=Config.DEBUG)
