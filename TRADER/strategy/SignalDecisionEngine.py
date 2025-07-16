from collections import deque
from strategy.MarketStatsCalculator import MarketStatsCalculator # Moved import to top
import time
from CONFIG import Config, SignalType  # Import SignalType from CONFIG.py

# =====================================================
# מחליט איתותים
# =====================================================
class SignalDecisionEngine:
    def __init__(self, coin):
        self.coin = coin
        self.recent_signals = deque([SignalType.NEUTRAL] * Config.MOMENTUM_WINDOW, maxlen=Config.MOMENTUM_WINDOW)
        self.current_signal = SignalType.NEUTRAL
        self.signal_price = 0.0
        self.consecutive = 0
        self.med_price = 0.0
        self.volatility = 0.0
        self.momentum = 0.0
        self.buy_pressure = 0.0
        self.sell_pressure = 0.0
        self.binance_price = 0.0  # Main reference price
        self.bybit_price = 0.0  # Secondary reference price
        self.okx_price = 0.0  # OKX reference price
        self.last_signals = deque(maxlen=Config.Last_signals_len)  # Store last 5 signals

    def analyze(self, now=None):
        from CONFIG import Config, SignalType # Import SignalType locally
        now = now or time.time()
        # Check for stale data from exchanges


        calc = MarketStatsCalculator(self.coin)
        self.med_price = calc.calculate_med_price()
        self.binance_price = calc.binance_price()
        self.bybit_price = calc.bybit_price()
        self.okx_price = calc.okx_price()

        # Append current prices to history deques regardless of med_price value
        self.coin.med_price_history.append((now, self.med_price))
        self.coin.binance_history.append((now, self.binance_price))
        self.coin.bybit_history.append((now, self.bybit_price))
        self.coin.okx_history.append((now, self.okx_price))

        # Limit history length to Config.HISTORY_LIMIT
        history_limit = Config.HISTORY_LIMIT if Config.HISTORY_LIMIT > 0 else 60
        if len(self.coin.med_price_history) > history_limit:
            self.coin.med_price_history.pop(0)
        if len(self.coin.binance_history) > history_limit:
            self.coin.binance_history.pop(0)
        if len(self.coin.bybit_history) > history_limit:
            self.coin.bybit_history.pop(0)
        if len(self.coin.okx_history) > history_limit:
            self.coin.okx_history.pop(0)    




        # If med_price is still zero or negative after appending, return NEUTRAL
        if self.med_price <= 0:
            print(f"Average price is zero or negative ({self.med_price}). Not appending to history.")
            return SignalType.NEUTRAL

        if self.coin.is_in_bought_Position and self.coin.buyed_price > 0:
            self.coin.current_profit = (self.med_price - self.coin.buyed_price) / self.coin.buyed_price
        else:
            self.coin.current_profit = 0.0

        history_len = len(self.coin.med_price_history)
        # print(f"[{self.coin.symbol}] History Length: {history_len}, Required: {Config.VOLATILITY_WINDOW}")
        if history_len < Config.VOLATILITY_WINDOW:
            return SignalType.NEUTRAL


        self.volatility = calc.calculate_volatility()
        self.buy_pressure, self.sell_pressure = calc.calculate_pressure_ratios()
        # print(f"[{self.coin.symbol}] Volatility: {self.volatility:.4f}, Buy Pressure: {self.buy_pressure:.4f}, Sell Pressure: {self.sell_pressure:.4f}")

        threshold = Config.BASE_THRESHOLD + min(self.volatility * 100, Config.MAX_VOL_ADJ) * (1 + self.momentum)

        raw = SignalType.NEUTRAL
        if self.buy_pressure > threshold: raw = SignalType.BUY
        elif self.sell_pressure > threshold: raw = SignalType.SELL

        self.recent_signals.append(raw)
        self.momentum = (self.recent_signals.count(SignalType.BUY) - self.recent_signals.count(SignalType.SELL)) / len(self.recent_signals)
        # print(f"[{self.coin.symbol}] Momentum: {self.momentum:.4f}")

        signal_ = SignalType.BUY if self.momentum > 0.5 else SignalType.SELL if self.momentum < -0.5 else SignalType.NEUTRAL


        
        if ((self.coin.is_in_bought_Position and signal_ == SignalType.BUY) or
            (not self.coin.is_in_bought_Position and signal_ == SignalType.SELL) or
             signal_ == SignalType.NEUTRAL):
                self.recent_signals.append(signal_)
        else:
            self.recent_signals.clear()

        if len(self.recent_signals) == Config.Last_signals_len:
            postive_signals_count = len([s for s in self.recent_signals if s == SignalType.BUY])
            negative_signals_count = len([s for s in self.recent_signals if s == SignalType.SELL])
        else :
            postive_signals_count = 0
            negative_signals_count = 0

        if postive_signals_count > Config.MIN_CONSEC_SIGNALS_postive:
            return SignalType.BUY
        elif negative_signals_count > Config.MIN_CONSEC_SIGNALS_negative:
            return SignalType.SELL
        else:
            return SignalType.NEUTRAL

