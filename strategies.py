# strategies.py
from __future__ import annotations
from abc import ABC, abstractmethod
from collections import deque
from typing import List, Tuple
from models import MarketDataPoint

# (action, symbol, qty, price)
Signal = Tuple[str, str, int, float]

class Strategy(ABC):
    @abstractmethod
    def generate_signals(self, tick: MarketDataPoint) -> List[Signal]:
        """
        Given a single tick, return zero or more signals of the form:
        (action, symbol, qty, price), where action: {"BUY","SELL"}.
        """
        raise NotImplementedError


class MovingAverageCrossover(Strategy):
    """
    BUY when fast SMA crosses above slow SMA; SELL when fast crosses below slow.
    Private state: _prices, _fast, _slow, _qty, _prev_diff
    """
    def __init__(self, symbol: str, fast: int = 5, slow: int = 20, qty: int = 10) -> None:
        if not (isinstance(fast, int) and isinstance(slow, int) and fast > 0 and slow > 0 and slow > fast):
            raise ValueError("Invalid windows: require integers with 0 < fast < slow.")
        self.symbol = symbol
        self._fast = fast
        self._slow = slow
        self._qty = qty
        self._prices: deque[float] = deque(maxlen=slow)
        self._prev_diff: float | None = None

    def _sma(self, n: int) -> float:
        if len(self._prices) < n:
            return float("nan")
        return sum(list(self._prices)[-n:]) / n

    def generate_signals(self, tick: MarketDataPoint) -> List[Signal]:
        if tick.symbol != self.symbol:
            return []
        self._prices.append(tick.price)
        if len(self._prices) < self._slow:  
            return []

        fast_ma = self._sma(self._fast)
        slow_ma = self._sma(self._slow)
        if any(v != v for v in (fast_ma, slow_ma)):  
            return []

        diff = fast_ma - slow_ma
        signals: List[Signal] = []
        if self._prev_diff is not None:
            # Cross up 
            if self._prev_diff <= 0 and diff > 0:
                signals.append(("BUY", self.symbol, self._qty, tick.price))
            # Cross down
            elif self._prev_diff >= 0 and diff < 0:
                signals.append(("SELL", self.symbol, self._qty, tick.price))
        self._prev_diff = diff
        return signals


class MomentumStrategy(Strategy):
    """
    BUY if (price / price_lookback - 1) >= threshold; SELL if <= -threshold.
    Private state: _prices, _lb, _th, _qty
    """
    def __init__(self, symbol: str, lookback: int = 10, threshold: float = 0.005, qty: int = 5) -> None:
        if not (isinstance(lookback, int) and lookback > 0):
            raise ValueError("lookback must be a positive integer.")
        if not (isinstance(threshold, (int, float)) and threshold >= 0):
            raise ValueError("threshold must be a non-negative number.")
        self.symbol = symbol
        self._lb = lookback
        self._th = float(threshold)
        self._qty = qty
        self._prices: deque[float] = deque(maxlen=lookback + 1)

    def generate_signals(self, tick: MarketDataPoint) -> List[Signal]:
        if tick.symbol != self.symbol:
            return []
        self._prices.append(tick.price)
        if len(self._prices) <= self._lb:
            return []  

        past = list(self._prices)[0]
        if past <= 0:
            return []  
        ret = (tick.price / past) - 1.0

        if ret >= self._th:
            return [("BUY", self.symbol, self._qty, tick.price)]
        elif ret <= -self._th:
            return [("SELL", self.symbol, self._qty, tick.price)]
        return []
