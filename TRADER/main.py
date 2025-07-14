from flask import Flask, jsonify, request, render_template
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
import traceback, sys, signal, time, threading
from dashboard_data.SQL_DB_DashboardData import SQL_DB_DashboardData
from CONFIG import Config
from COIN.coin_model import Coin, ALL_Coins
from flask_cors import CORS

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)
coins_lock = threading.Lock()

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
        print(f"Error: {e}")
        return jsonify({"error": "load error"}), 500
    return jsonify({"data": result, "cycle_interval": Config.CYCLE_INTERVAL}) if result else ({"error": "No data"}, 404)

@app.route("/api/reset_trades", methods=["POST"])
def reset_all_trades():
    with coins_lock:
        for coin in ALL_Coins.Coins:
            coin.trade_manager.reset_trades()
            coin.reset_coin()
    return {"status": "all trades reset successfully"}

application = DispatcherMiddleware(None, {
    '/trader': app
})

def trading_loop():
    try:
        while True:
            start = time.time()
            with coins_lock:
                for coin_obj in ALL_Coins.Coins:
                    coin_obj.process_coin()
            time.sleep(max(0, Config.CYCLE_INTERVAL - (time.time() - start)))
    except Exception as e:
        print(f"Trading loop error: {e}\n{traceback.format_exc()}")

if __name__ == "__main__":
    try:
        for symbol in Config.SYMBOLS:
            Coin(symbol)
        SQL_DB_DashboardData.restore_all_data()
        threading.Thread(target=trading_loop, daemon=True).start()
        run_simple("0.0.0.0", Config.PORT, application, use_reloader=False)
    except Exception as e:
        print(f"Startup error: {e}\n{traceback.format_exc()}")
