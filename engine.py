# engine.py
from typing import List, Dict, Tuple
import random
from models import MarketDataPoint, Order, OrderError, ExecutionError

Signal = Tuple[str, str, int, float]

class BacktestEngine:
    def __init__(self, strategies, initial_cash: float = 100_000.0, fail_prob: float = 0.01):
        self.strategies = strategies
        self.initial_cash = float(initial_cash)
        self.fail_prob = float(fail_prob)

        # portfolio state
        self.portfolio: Dict[str, Dict[str, float]] = {"CASH": {"amount": self.initial_cash}}
        self.positions: Dict[str, Dict[str, float]] = {}   
        self._last_prices: Dict[str, float] = {}           

        # logs and outputs
        self.order_history: List[Order] = []
        self.errors: List[str] = []
        self.equity_curve: List[Tuple] = []                

    # helpers
    def _ensure_symbol(self, symbol: str):
        if symbol not in self.positions:
            self.positions[symbol] = {"quantity": 0, "avg_price": 0.0}

    def _equity(self) -> float:
        cash = self.portfolio["CASH"]["amount"]
        eq = cash
        for sym, pos in self.positions.items():
            qty = pos.get("quantity", 0)
            price = self._last_prices.get(sym, 0.0)
            eq += qty * price
        return eq

    def _create_order(self, action: str, symbol: str, qty: int, price: float) -> Order:
        side = "BUY" if action.upper() == "BUY" else "SELL"
        order = Order(symbol=symbol, quantity=int(qty), price=float(price), side=side)
        order.validate() 
        return order

    def _execute_order(self, order: Order):
        # random simulated execution failure
        if random.random() < self.fail_prob:
            order.status = "ERROR"
            raise ExecutionError(f"Simulated execution failure for {order.side} {order.quantity} {order.symbol} @ {order.price}")

        self._ensure_symbol(order.symbol)
        pos = self.positions[order.symbol]
        cash = self.portfolio["CASH"]["amount"]
        qty = order.quantity
        px = order.price

        if order.side == "BUY":
            cost = qty * px
            if cash < cost:
                order.status = "REJECTED"
                raise ExecutionError(f"Insufficient cash to buy {qty} {order.symbol} at {px}")
            total_cost = pos["avg_price"] * pos["quantity"] + cost
            total_qty = pos["quantity"] + qty
            pos["avg_price"] = total_cost / total_qty if total_qty else 0.0
            pos["quantity"] = total_qty
            self.portfolio["CASH"]["amount"] = cash - cost
            order.status = "FILLED"
        else:  
            if pos["quantity"] < qty:
                order.status = "REJECTED"
                raise ExecutionError(f"Insufficient position to sell {qty} {order.symbol}")
            self.portfolio["CASH"]["amount"] = cash + qty * px
            pos["quantity"] -= qty
            if pos["quantity"] == 0:
                pos["avg_price"] = 0.0
            order.status = "FILLED"

    # main loop
    def process(self, ticks: List[MarketDataPoint]):
        # ensuring chronological
        ticks = sorted(ticks, key=lambda t: t.timestamp)

        for tick in ticks:
            self._last_prices[tick.symbol] = tick.price

            # strategy signals
            signals: List[Signal] = []
            for strat in self.strategies:
                try:
                    out = strat.generate_signals(tick)
                    if out:
                        signals.extend(out)
                except Exception as e:
                    self.errors.append(f"StrategyError: {e} at {tick.timestamp}")

            # signals to orders to executions
            for action, symbol, qty, price in signals:
                try:
                    order = self._create_order(action, symbol, qty, price)  
                    self.order_history.append(order)
                    self._execute_order(order)                               
                except OrderError as oe:
                    self.errors.append(f"OrderError: {oe}")
                except ExecutionError as xe:
                    self.errors.append(f"ExecutionError: {xe}")

            # equity snapshot
            self.equity_curve.append((tick.timestamp, self._equity()))
