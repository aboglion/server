# SignalDecisionEngine.py
from CONFIG import Config, SignalType
import time
import statistics
from collections import deque
from strategy.MarketStatsCalculator import MarketStatsCalculator

# =====================================================
# מנוע החלטות איתותים משופר
# =====================================================
class SignalDecisionEngine:
    """
    Analyzes market data for a specific coin to generate trading signals.
    """
    def __init__(self, coin, calc):
        self.coin = coin
        self.calc = calc
        self.recent_signals = deque(maxlen=Config.MOMENTUM_WINDOW)
        self.recent_buy_pressure = deque(maxlen=Config.PRESSURE_WINDOW)
        self.recent_sell_pressure = deque(maxlen=Config.PRESSURE_WINDOW)
        self.recent_volumes = deque(maxlen=Config.VOLUME_WINDOW)
        self.med_price = 0.0
        self.last_decision = SignalType.NEUTRAL
        self.volatility = 0.0
        self.signal_momentum = 0.0
        self.pressure_score = 0.0
        self.volume_momentum = 0.0
        self.buy_pressure = 0.0
        self.sell_pressure = 0.0
        self.momentum = 0.0

    def _update_market_data(self, now):
        self.med_price = self.calc.calculate_med_price()
        if self.med_price <= 0: return False
        self.coin.med_price_history.append((now, self.med_price))
        buy_p, sell_p = self.calc.calculate_pressure_ratios()
        volume = self.calc.calculate_Volume()
        self.recent_buy_pressure.append(buy_p)
        self.recent_sell_pressure.append(sell_p)
        self.recent_volumes.append(volume)
        if self.coin.is_in_bought_Position and self.coin.buyed_price > 0:
            gross_profit = (self.coin.binance_price - self.coin.buyed_price) / self.coin.buyed_price
            fee = Config.FEE * 2  # buy + sell
            self.coin.current_profit = gross_profit - fee
        else:
            self.coin.current_profit = 0.0
        return True

    def _calculate_indicators(self):
        volumes_list = list(self.recent_volumes)
        if (len(volumes_list) // 2) < 2: return False
        buy_signals = self.recent_signals.count(SignalType.BUY)
        sell_signals = self.recent_signals.count(SignalType.SELL)
        total_signals = len(self.recent_signals)
        self.signal_momentum = (buy_signals - sell_signals) / total_signals if total_signals > 0 else 0.0
        self.buy_pressure = statistics.median(self.recent_buy_pressure)
        self.sell_pressure = statistics.median(self.recent_sell_pressure)
        self.pressure_score = (self.buy_pressure - self.sell_pressure) / (self.buy_pressure + self.sell_pressure + 1e-9)
        split_point = len(volumes_list) // 2
        median_vol_recent = statistics.median(volumes_list[split_point:])
        median_vol_older = statistics.median(volumes_list[:split_point])
        self.volume_momentum = (median_vol_recent - median_vol_older) / (median_vol_recent + median_vol_older + 1e-9)
        self.volatility = self.calc.calculate_volatility()
        return True

    def _make_decision(self):
        # 💡 --- Volatility Filter (ADDED) ---
        # First, check if the market is suitable for trading.
        # If volatility is too high or too low, do not proceed.
        print(f"Volatility: {self.volatility:.2f}")
        if not (Config.MIN_VOLATILITY_FOR_SCALPING < self.volatility < Config.MAX_VOLATILITY_FOR_SCALPING):
            return SignalType.NEUTRAL  # Skip trade if market conditions are not ideal

        # --- Unified Momentum Calculation ---
        self.momentum = (
            (self.pressure_score * 0.5) +
            (self.signal_momentum * 0.3) +
            (self.volume_momentum * 0.2)
        ) * 10

        # --- Dynamic Threshold ---
        volatility_adjustment = min(self.volatility * 5, 0.2)
        decision_threshold = Config.BASE_DECISION_THRESHOLD + volatility_adjustment
        signal = SignalType.NEUTRAL
        if self.momentum > decision_threshold:
            signal = SignalType.BUY
        elif self.momentum < -decision_threshold:
            signal = SignalType.SELL

        # --- Risk/Reward Filter ---
        risk_reward_ratio,potential_profit,potential_loss = 0.0,0.0,0.0
        if signal != SignalType.NEUTRAL:
            potential_profit = self.med_price * Config.TAKE_PROFIT_PCT
            potential_loss = self.med_price * Config.STOP_LOSS_PCT
            net_potential_profit = potential_profit - (self.med_price * Config.FEE * 2)
            if potential_loss == 0:
                return SignalType.NEUTRAL
            risk_reward_ratio = net_potential_profit / potential_loss
            if risk_reward_ratio < Config.MIN_RISK_REWARD_RATIO:
                return SignalType.NEUTRAL
            
        print(f"{self.coin.symbol}->risk:{risk_reward_ratio:.4f},decision_threshold:{decision_threshold:.4f},signal")
        return signal

    def analyze(self, now=None):
        now = now or time.time()
        if not self._update_market_data(now):
            return SignalType.NEUTRAL
                # --- Debug prints for deque lengths ---
        max_len_collected = max(Config.HISTORY_LIMIT, Config.VOLATILITY_WINDOW, Config.PRESSURE_WINDOW, Config.VOLUME_WINDOW)
        min_pv = min(len(self.recent_signals), len(self.recent_buy_pressure), len(self.recent_sell_pressure), len(self.recent_volumes))
        if min_pv==0: min_pv = len(self.coin.med_price_history)  # Avoid division by zero
        if (len(self.coin.med_price_history) < max(Config.VOLATILITY_WINDOW,Config.HISTORY_LIMIT) or
            len(self.recent_buy_pressure) < Config.PRESSURE_WINDOW or
            len(self.recent_sell_pressure) < Config.PRESSURE_WINDOW or
            len(self.recent_volumes) < Config.VOLUME_WINDOW) :
                 COLLECTING_Progress=(f"COLLECTING {(min_pv/max_len_collected)*100}% | {self.coin.symbol}")
                 print(COLLECTING_Progress)
                 return COLLECTING_Progress

        # --- Market Data Checks ---
        if not self._calculate_indicators():
            return SignalType.NEUTRAL
        final_signal = self._make_decision()
        unfiltered_signal = SignalType.NEUTRAL
        if self.momentum > Config.BASE_DECISION_THRESHOLD:
            unfiltered_signal = SignalType.BUY
        elif self.momentum < -Config.BASE_DECISION_THRESHOLD:
            unfiltered_signal = SignalType.SELL
        self.recent_signals.append(unfiltered_signal)
        self.last_decision = final_signal
        return final_signal