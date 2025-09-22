# tests.py
import unittest
import datetime as dt
from dataclasses import FrozenInstanceError
from models import MarketDataPoint, Order, OrderError, ExecutionError
from typing import List, Tuple, Dict
from strategies import Strategy, MovingAverageCrossover, MomentumStrategy
from data_loader import load_market_data
from engine import BacktestEngine
import os, tempfile
from reporting import compute_returns, plot_equity_curve, write_markdown_report


class TestOrderMutability(unittest.TestCase):
    def test_order_status_is_mutable(self):
        o = Order(symbol="AAPL", quantity=10, price=150.0)
        self.assertEqual(o.status, "NEW")
        o.status = "FILLED"  
        self.assertEqual(o.status, "FILLED")

    def test_marketdatapoint_is_immutable(self):
        mdp = MarketDataPoint(timestamp=dt.datetime(2025, 1, 1), symbol="AAPL", price=100.0)
        with self.assertRaises(FrozenInstanceError):
            mdp.price = 101.0  


class TestDataLoader(unittest.TestCase):
    def test_load_market_data_parses_and_sorts(self):
        import csv, tempfile, os
        t0 = dt.datetime(2025, 1, 1, 0, 0, 0)
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "m.csv")
            with open(p, "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["timestamp", "symbol", "price"])
                w.writerow([(t0+dt.timedelta(seconds=2)).isoformat(), "AAPL", "101"])
                w.writerow([t0.isoformat(), "AAPL", "100"])
                w.writerow([(t0+dt.timedelta(seconds=1)).isoformat(), "AAPL", "100.5"])
            ticks = load_market_data(p)
            self.assertEqual(len(ticks), 3)
            self.assertIsInstance(ticks[0], MarketDataPoint)
            self.assertEqual(ticks[0].timestamp, t0)
            from dataclasses import FrozenInstanceError
            with self.assertRaises(FrozenInstanceError):
                ticks[0].price = 123.0


class TestExceptions(unittest.TestCase):
    def test_order_error_for_invalid_quantity(self):
        o = Order(symbol="AAPL", quantity=0, price=150.0, side="BUY")
        with self.assertRaises(OrderError):
            o.validate()
        o2 = Order(symbol="AAPL", quantity=-5, price=150.0, side="SELL")
        with self.assertRaises(OrderError):
            o2.validate()

    def test_order_error_for_invalid_price(self):
        o = Order(symbol="AAPL", quantity=10, price=0.0, side="BUY")
        with self.assertRaises(OrderError):
            o.validate()

    def test_order_error_for_invalid_side(self):
        o = Order(symbol="AAPL", quantity=10, price=150.0, side="HOLD")
        with self.assertRaises(OrderError):
            o.validate()

    def test_execution_error_is_caught_and_flow_continues(self):
        # demo loop to see if it keeps processing when an execution fails
        logs = []
        orders = [
            Order(symbol="AAPL", quantity=10, price=100.0, side="BUY"),
            Order(symbol="AAPL", quantity=10, price=101.0, side="BUY"),
        ]
        for i, o in enumerate(orders):
            try:
                o.validate()
                # first order fails, second succeeds
                if i == 0:
                    raise ExecutionError("simulated failure")
                o.status = "FILLED"
            except OrderError as e:
                logs.append(f"OrderError: {e}")
            except ExecutionError as e:
                logs.append(f"ExecutionError: {e}")

        # should have 1 error logged, and second order filled
        self.assertTrue(any("ExecutionError" in m for m in logs))
        self.assertEqual(orders[0].status, "NEW")     
        self.assertEqual(orders[1].status, "FILLED") 


class TestEngine(unittest.TestCase):
    def test_engine_records_equity_and_catches_failures(self):
        now = dt.datetime(2025, 1, 1)
        ticks = [MarketDataPoint(now + dt.timedelta(seconds=i), "AAPL", 100.0 + i) for i in range(10)]

        strat = MomentumStrategy(symbol="AAPL", lookback=1, threshold=0.0, qty=1)

        # forcing failures
        engine = BacktestEngine(strategies=[strat], initial_cash=10_000.0, fail_prob=1.0)
        engine.process(ticks)

        self.assertEqual(len(engine.equity_curve), len(ticks))
        self.assertTrue(any("ExecutionError" in e for e in engine.errors))

if __name__ == "__main__":
    unittest.main()
