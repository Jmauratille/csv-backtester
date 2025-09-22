# CSV-Based Algorithmic Trading Backtester

Reads market data CSV of AAPL ticks generated via a Gaussian random walk, then uses the data for two strategies: a Moving Average Crossover and a Momentum strategy. The engine turns the signals into orders, simulates fills, updates a cash position portfolio, and reports an equity curve, total return, per-period Sharpe, and max drawdown.

## Generate Data

```bash
python data_generator.py
```

## Run Combined and Separate Per-Strategy Backtests

```bash
python main.py --csv market_data.csv --symbol AAPL --outdir artifacts --cash 100000 --fail-prob 0.01 --separate --seed 42
```

## Outputs

- `artifacts/combined_performance.md`
- `artifacts/combined_equity_curve.png`
- `artifacts/ma_only_performance.md`
- `artifacts/ma_only_equity_curve.png`
- `artifacts/mom_only_performance.md`
- `artifacts/mom_only_equity_curve.png`

Each report will include:

- Total return 
- Sharpe per-period
- Max drawdown
- Equity curve plot
- A short narrative with counts of fills, rejects, and errors

## Tests

```bash
python -m unittest discover -s tests -p "tests.py" -v
```

Covers:

- CSV parsing into frozen dataclass 
- Mutable Behavior of Order
- Exception raising and handling
- Engine resilience and equity recording


## Filemap

- `models.py`: MarketDataPoint, Order, OrderError, ExecutionError
- `data_loader.py`: CSV to List[MarketDataPoint] 
- `strategies.py`: Strategy ABC, MovingAverageCrossover, MomentumStrategy
- `engine.py`: Backtest loop, positions, equity curve
- `reporting.py`: Metrics, equity plot, Markdown report
- `main.py`: CLI entry point
- `data_generator.py`: Sample CSV generator
- `performance.ipynb`: Notebook walkthrough 
- `tests/`: Unit tests

## Strategy Parameters (CLI)

- Moving Average Crossover:
    `--fast` (default: 5)
    `--slow` (default: 20)
    `--qty-ma` (default: 10)

- Momentum:
    `--mom-lb` (default: 10)
    `--mom-th` (default: 0.005)
    `--qty-mom` (default: 5)
