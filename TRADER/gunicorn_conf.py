
import threading

def post_fork(server, worker):
    from main import init_all_coins, trading_loop
    init_all_coins()
    threading.Thread(target=trading_loop, daemon=True).start()
