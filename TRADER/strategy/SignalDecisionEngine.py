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
    This revised engine uses a scoring system and robust risk management
    to make more reliable, conservative trading decisions.
    """
    def __init__(self, coin, calc):
        self.coin = coin
        self.calc = calc

        # --- Data Deques for Indicators ---
        self.recent_signals = deque(maxlen=Config.MOMENTUM_WINDOW)
        self.recent_buy_pressure = deque(maxlen=Config.PRESSURE_WINDOW)
        self.recent_sell_pressure = deque(maxlen=Config.PRESSURE_WINDOW)
        self.recent_volumes = deque(maxlen=Config.VOLUME_WINDOW)

        # --- State Variables ---
        self.med_price = 0.0
        self.last_decision = SignalType.NEUTRAL

        # --- Instance attributes for indicators ---
        self.volatility = 0.0
        self.signal_momentum = 0.0
        self.pressure_score = 0.0
        self.volume_momentum = 0.0
        self.buy_pressure = 0.0
        self.sell_pressure = 0.0
        self.momentum = 0.0

    def _update_market_data(self, now):
        self.med_price = self.calc.calculate_med_price()
        if self.med_price <= 0:
            return False

        self.coin.med_price_history.append((now, self.med_price))

        buy_p, sell_p = self.calc.calculate_pressure_ratios()
        volume = self.calc.calculate_Volume()

        self.recent_buy_pressure.append(buy_p)
        self.recent_sell_pressure.append(sell_p)
        self.recent_volumes.append(volume)

        if self.coin.is_in_bought_Position and self.coin.buyed_price > 0:
            self.coin.current_profit = (self.coin.binance_price - self.coin.buyed_price) / self.coin.buyed_price
        else:
            self.coin.current_profit = 0.0

        return True

    def _calculate_indicators(self):
        volumes_list = list(self.recent_volumes)
        if (len(volumes_list) // 2) < 2:
            return False  # Not enough data for volume momentum

        # --- Signal Momentum ---
        buy_signals = self.recent_signals.count(SignalType.BUY)
        sell_signals = self.recent_signals.count(SignalType.SELL)
        total_signals = len(self.recent_signals)
        self.signal_momentum = (buy_signals - sell_signals) / total_signals if total_signals > 0 else 0.0

        # --- Pressure Analysis ---
        self.buy_pressure = statistics.median(self.recent_buy_pressure)
        self.sell_pressure = statistics.median(self.recent_sell_pressure)
        self.pressure_score = (self.buy_pressure - self.sell_pressure) / (self.buy_pressure + self.sell_pressure + 1e-9)

        # --- Volume Momentum ---
        split_point = len(volumes_list) // 2
        median_vol_recent = statistics.median(volumes_list[split_point:])
        median_vol_older = statistics.median(volumes_list[:split_point])
        self.volume_momentum = (median_vol_recent - median_vol_older) / (median_vol_recent + median_vol_older + 1e-9)

        # --- Volatility ---
        self.volatility = self.calc.calculate_volatility()

        return True

    def _make_decision(self):
        # --- Unified Momentum Calculation ---
        self.momentum = (
            (self.pressure_score * 0.5) +
            (self.signal_momentum * 0.3) +
            (self.volume_momentum * 0.2)
        )*10

        # --- Dynamic Threshold ---
        volatility_adjustment = min(self.volatility * 5, 0.2)
        decision_threshold = Config.BASE_DECISION_THRESHOLD + volatility_adjustment

        signal = SignalType.NEUTRAL
        if self.momentum > decision_threshold:
            signal = SignalType.BUY
        elif self.momentum < -decision_threshold:
            signal = SignalType.SELL

        # --- Risk/Reward Filter ---
        if signal != SignalType.NEUTRAL:
            potential_profit = self.med_price * Config.TAKE_PROFIT_PCT
            potential_loss = self.med_price * Config.STOP_LOSS_PCT
            net_potential_profit = potential_profit - (self.med_price * Config.FEE * 2)

            if potential_loss == 0:
                return SignalType.NEUTRAL

            risk_reward_ratio = net_potential_profit / potential_loss
            if risk_reward_ratio < Config.MIN_RISK_REWARD_RATIO:
                return SignalType.NEUTRAL

        return signal

    def analyze(self, now=None):
        now = now or time.time()

        if not self._update_market_data(now):
            return SignalType.NEUTRAL

        if (len(self.coin.med_price_history) < Config.VOLATILITY_WINDOW or
            len(self.recent_buy_pressure) < Config.PRESSURE_WINDOW or
            len(self.recent_volumes) < Config.VOLUME_WINDOW):
            return SignalType.NEUTRAL

        if not self._calculate_indicators():
            return SignalType.NEUTRAL

        final_signal = self._make_decision()

        # --- Update recent_signals with raw market sentiment ---
        unfiltered_signal = SignalType.NEUTRAL
        if self.momentum > Config.BASE_DECISION_THRESHOLD:
            unfiltered_signal = SignalType.BUY
        elif self.momentum < -Config.BASE_DECISION_THRESHOLD:
            unfiltered_signal = SignalType.SELL

        self.recent_signals.append(unfiltered_signal)
        self.last_decision = final_signal
        return final_signal
