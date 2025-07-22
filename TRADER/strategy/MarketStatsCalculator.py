import math
import statistics

# =====================================================
# מחשבון ניתוח שוק (תנודתיות, לחץ וכו')
# =====================================================
class MarketStatsCalculator:
    def __init__(self, coin):
        self.coin = coin

    def calculate_med_price(self):
        try:
            prices = []
            for ex, ob in self.coin.orderbooks.items():
                if ob is not None and ob.get("bids") and ob.get("asks"):
                    b, a = ob["bids"][0], ob["asks"][0]
                    prices.append((b[0] + a[0]) / 2)
                else:
                    print(f"MarketStatsCalculator: Exchange '{ex}' has no valid order book data for {self.coin.symbol}.")
            if not prices:
                print(f"MarketStatsCalculator: No valid order book data to calculate average price for {self.coin.symbol}.")
                return 0.0
            return statistics.median(prices)
        except Exception as e:
            print(f"MarketStatsCalculator: An unexpected error occurred in calculate_med_price for {self.coin.symbol}: {e}")
            return 0.0

    def _other_exchanges_med(self, exclude):
        prices = []
        for ex in ["binance", "bybit", "okx"]:
            if ex in exclude:
                continue
            ob = self.coin.orderbooks.get(ex)
            if ob and ob.get("bids") and ob.get("asks"):
                prices.append((ob["bids"][0][0] + ob["asks"][0][0]) / 2)
        if prices:
            return statistics.median(prices)
        return 0.0

    def binance_price(self):
        if "binance" not in self.coin.orderbooks:
            return self._other_exchanges_med(["binance"])
        ob = self.coin.orderbooks["binance"]
        if ob is None or not ob.get("bids") or not ob.get("asks"):
            return self._other_exchanges_med(["binance"])
        return (ob["bids"][0][0] + ob["asks"][0][0]) / 2

    def bybit_price(self):
        if "bybit" not in self.coin.orderbooks:
            return self._other_exchanges_med(["bybit"])
        ob = self.coin.orderbooks["bybit"]
        if ob is None or not ob.get("bids") or not ob.get("asks"):
            return self._other_exchanges_med(["bybit"])
        return (ob["bids"][0][0] + ob["asks"][0][0]) / 2

    def okx_price(self):
        if "okx" not in self.coin.orderbooks:
            return self._other_exchanges_med(["okx"])
        ob = self.coin.orderbooks["okx"]
        if ob is None or not ob.get("bids") or not ob.get("asks"):
            return self._other_exchanges_med(["okx"])
        return (ob["bids"][0][0] + ob["asks"][0][0]) / 2

    def calculate_volatility(self):
        avg_price = statistics.mean([
            self.binance_price(),
            self.bybit_price(),
            self.okx_price()
        ])
        return abs(avg_price - self.calculate_med_price() )
         

    def calculate_pressure_ratios(self):
        buy, sell = [], []
        for ob in self.coin.orderbooks.values():
            if not ob["bids"] or not ob["asks"]: continue
            bid_qty = sum(q for _, q in ob["bids"])
            ask_qty = sum(q for _, q in ob["asks"])
            if ask_qty > 0: buy.append(bid_qty / ask_qty)
            if bid_qty > 0: sell.append(ask_qty / bid_qty)
        return (sum(buy) / len(buy) if buy else 0.0, sum(sell) / len(sell) if sell else 0.0)


    def calculate_Volume(self):
        volumes = []
        for ob in self.coin.orderbooks.values():
            if not ob["bids"] or not ob["asks"]: continue
            bid_volume = sum(q for _, q in ob["bids"])
            ask_volume = sum(q for _, q in ob["asks"])
            volumes.append((bid_volume + ask_volume) / 2)
        return statistics.median(volumes) if volumes else 0.0
        