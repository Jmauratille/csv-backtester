# main.py
import argparse
import os
from collections import Counter
import random  

from data_loader import load_market_data
from strategies import MovingAverageCrossover, MomentumStrategy
from engine import BacktestEngine
from reporting import compute_returns, plot_equity_curve, write_markdown_report


def run_case(label, ticks, strategies, cash, fail_prob, outdir):
    """Runs a single backtest and writes a plot and report."""
    engine = BacktestEngine(strategies=strategies, initial_cash=cash, fail_prob=fail_prob)
    engine.process(ticks)

    # outputs
    os.makedirs(outdir, exist_ok=True)
    plot_path = os.path.join(outdir, f"{label}_equity_curve.png")
    plot_equity_curve(engine.equity_curve, plot_path)

    metrics = compute_returns(engine.equity_curve)
    status_counts = Counter(o.status for o in engine.order_history)
    context = {
        "fills":   status_counts.get("FILLED", 0),
        "rejects": status_counts.get("REJECTED", 0),
        "errors":  len(engine.errors),
    }
    report_path = os.path.join(outdir, f"{label}_performance.md")
    write_markdown_report(metrics, f"{label}_equity_curve.png", report_path, context=context)

    print(f"[{label}] Orders: {len(engine.order_history)} | Errors: {len(engine.errors)}")
    print(f"[{label}] Report: {report_path}")
    return metrics


def main():
    p = argparse.ArgumentParser(description="CSV-Based Algorithmic Trading Backtester")
    p.add_argument("--csv", type=str, default="market_data.csv", help="Path to CSV (timestamp,symbol,price)")
    p.add_argument("--symbol", type=str, default="AAPL", help="Symbol to backtest")
    p.add_argument("--outdir", type=str, default="artifacts", help="Output directory for report/plots")
    p.add_argument("--cash", type=float, default=100_000.0, help="Initial cash")
    p.add_argument("--fail-prob", type=float, default=0.01, help="Simulated execution failure probability")

    # strategy parameters
    p.add_argument("--fast", type=int, default=5, help="Fast MA window")
    p.add_argument("--slow", type=int, default=20, help="Slow MA window")
    p.add_argument("--mom-lb", type=int, default=10, help="Momentum lookback")
    p.add_argument("--mom-th", type=float, default=0.005, help="Momentum threshold")
    p.add_argument("--qty-ma", type=int, default=10, help="Qty per MA signal")
    p.add_argument("--qty-mom", type=int, default=5, help="Qty per Momentum signal")

    # produce separate runs for strategies
    p.add_argument("--separate", action="store_true",
                   help="If set, also run MA-only and MOM-only backtests alongside the combined run.")
    # seed for reproducability
    p.add_argument("--seed", type=int, default=None, help="Random seed for reproducible simulated failures")

    args = p.parse_args()
    if args.seed is not None:
        random.seed(args.seed)

    ticks = load_market_data(args.csv)

    # strategies
    ma = MovingAverageCrossover(symbol=args.symbol, fast=args.fast, slow=args.slow, qty=args.qty_ma)
    mom = MomentumStrategy(symbol=args.symbol, lookback=args.mom_lb, threshold=args.mom_th, qty=args.qty_mom)

    # combined portfolio
    run_case("combined", ticks, [ma, mom], args.cash, args.fail_prob, args.outdir)

    if args.separate:
        ma_only = MovingAverageCrossover(symbol=args.symbol, fast=args.fast, slow=args.slow, qty=args.qty_ma)
        mom_only = MomentumStrategy(symbol=args.symbol, lookback=args.mom_lb, threshold=args.mom_th, qty=args.qty_mom)

        run_case("ma_only",  ticks, [ma_only], args.cash, args.fail_prob, args.outdir)
        run_case("mom_only", ticks, [mom_only], args.cash, args.fail_prob, args.outdir)


if __name__ == "__main__":
    main()
