from collections import deque
from strategy.MarketStatsCalculator import MarketStatsCalculator # Moved import to top
import time, statistics
from CONFIG import Config, SignalType  # Import SignalType from CONFIG.py

# =====================================================
# מחליט איתותים
# =====================================================
class SignalDecisionEngine:
    def __init__(self, coin):
        self.coin = coin
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
        self.recent_signals = deque(maxlen=Config.recent_signals_len)  
        self.recent_buy_pressure = deque(maxlen=Config.recent_pressure_len)
        self.recent_sell_pressure = deque(maxlen=Config.recent_pressure_len)
        self.recent_Volumes = deque(maxlen=Config.recent_Volumes_len)
        self.last_decision = SignalType.NEUTRAL  # Last decision made by the engine

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
            self.last_decision = SignalType.NEUTRAL
            return SignalType.NEUTRAL

        if self.coin.is_in_bought_Position and self.coin.buyed_price > 0:
            self.coin.current_profit = (self.coin.binance_price - self.coin.buyed_price) / self.coin.buyed_price - (Config.FEE * 2)
        else:
            self.coin.current_profit = 0.0

        history_len = len(self.coin.med_price_history)
        if history_len < Config.VOLATILITY_WINDOW:
            self.last_decision = SignalType.NEUTRAL
            return self.last_decision
        self.volatility = calc.calculate_volatility()

        self.buy_pressure, self.sell_pressure = calc.calculate_pressure_ratios()
        last_Volume= calc.calculate_Volume()
        self.recent_buy_pressure.append(self.buy_pressure)
        self.recent_sell_pressure.append(self.sell_pressure)    
        self.recent_Volumes.append(last_Volume)

        if  len(self.recent_buy_pressure) < Config.recent_pressure_len or \
            len(self.recent_sell_pressure) < Config.recent_pressure_len or \
            len(self.recent_Volumes) < Config.recent_Volumes_len:
                self.last_decision = SignalType.NEUTRAL
                return self.last_decision
        # Calculate the median of buy and sell pressures
        self.buy_pressure = statistics.median(self.recent_buy_pressure)
        self.sell_pressure = statistics.median(self.recent_sell_pressure)
        Volume_median_PART1= statistics.median(self.recent_Volumes[:int(Config.recent_Volumes_len/2)+1] )
        Volume_median_PART2= statistics.median(self.recent_Volumes[int(Config.recent_Volumes_len/2):] )

        volume_factor = (Volume_median_PART2 - Volume_median_PART1)/ Volume_median_PART2 if Volume_median_PART2 > 0 else 0.0
        vol_factor = min(self.volatility, 0.05)  # מגביל תנודתיות קיצונית
        momentum_adj = max(0.0, 0.5 + self.momentum)  # לא יורד מתחת ל־0.5
        threshold = Config.BASE_THRESHOLD + (vol_factor * 10) * momentum_adj + (volume_factor * 10)
        print("coin:",self.coin.symbol,vol_factor * 10, momentum_adj, volume_factor * 10,"\n","#"*20)
        # print(f"thereshold: {threshold}, self.buy_pressure: {self.buy_pressure}, self.sell_pressure: {self.sell_pressure}")
        signal_ = SignalType.NEUTRAL
        if self.buy_pressure > threshold and self.buy_pressure > self.sell_pressure:
            signal_ = SignalType.BUY
        elif self.sell_pressure > threshold and self.sell_pressure > self.buy_pressure:
            signal_ = SignalType.SELL


        # Check for consecutive signals shuld be sell/nuetral or buy/nuetral not sell/buy/neutral
        if (signal_ == SignalType.BUY and SignalType.SELL in self.recent_signals) or \
            (signal_ == SignalType.SELL and SignalType.BUY in self.recent_signals):
                self.recent_signals.clear()
        self.recent_signals.append(signal_)

        postive_signals = self.recent_signals.count(SignalType.BUY)
        negative_signals = self.recent_signals.count(SignalType.SELL)
        # print(f" {self.coin.symbol} - Postive: {postive_signals}, Negative: {negative_signals},\n Recent Signals: {list(self.recent_signals)}\n {(postive_signals - negative_signals) / len(self.recent_signals) if len(self.recent_signals) > 0 else 0.0}\n","="*20)
        if len(self.recent_signals) > min(Config.MIN_CONSEC_SIGNALS_postive, Config.MIN_CONSEC_SIGNALS_negative):
            self.momentum = (postive_signals - negative_signals) / len(self.recent_signals)
        else:
            self.momentum = 0.0
        self.last_decision = SignalType.NEUTRAL
        if len(self.recent_signals) == Config.recent_signals_len:
            if postive_signals > Config.MIN_CONSEC_SIGNALS_postive:
                self.last_decision = SignalType.BUY
            elif self.recent_signals.count(SignalType.SELL) > Config.MIN_CONSEC_SIGNALS_negative:
                self.last_decision = SignalType.SELL
            
       
        return self.last_decision

