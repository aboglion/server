import requests
from datetime import datetime

class BinanceConnector:
    def fetch(self, symbol):
        url = "https://api.binance.com/api/v3/depth"
        params = {"symbol": symbol, "limit": 5}
        try:
            r = requests.get(url, params=params, timeout=5)
            r.raise_for_status()
            data = r.json()
            return {"bids": [[float(p), float(q)] for p, q in data["bids"]],
                    "asks": [[float(p), float(q)] for p, q in data["asks"]]}
        except requests.exceptions.RequestException as e:
            print(f"BinanceConnector: Request failed: {e}")
            return {"bids": [], "asks": []} # Return empty on failure

class BybitConnector:
    def fetch(self, symbol):
        url = "https://api.bybit.com/v5/market/orderbook"
        params = {"category": "spot", "symbol": symbol, "limit": 5}
        try:
            r = requests.get(url, params=params, timeout=5)
            r.raise_for_status()
            data = r.json()
            return {"bids": [[float(p), float(q)] for p, q in data["result"]["b"]],
                    "asks": [[float(p), float(q)] for p, q in data["result"]["a"]]}
        except requests.exceptions.RequestException as e:
            print(f"BybitConnector: Request failed: {e}")
            return {"bids": [], "asks": []} # Return empty on failure

class OKXConnector:
    def fetch(self, symbol):
        instId = symbol.replace("USDT", "-USDT")
        try:
            r = requests.get("https://www.okx.com/api/v5/market/books", params={"instId": instId, "sz": 5}, timeout=5)
            r.raise_for_status()
            data = r.json()
            return {"bids": [[float(p), float(q)] for p, q, *_ in data["data"][0]["bids"]],
                    "asks": [[float(p), float(q)] for p, q, *_ in data["data"][0]["asks"]]}
        except requests.exceptions.RequestException as e:
            print(f"OKXConnector: Request failed: {e}")
            return {"bids": [], "asks": []} # Return empty on failure
