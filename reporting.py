# reporting.py
from __future__ import annotations
from typing import List, Tuple, Dict
import math
import statistics
import os


def compute_returns(equity_curve: List[Tuple]) -> Dict[str, object]:
    """
    equity_curve: list of (timestamp, equity_float).
    Returns a dict with total_return, periodic_returns, sharpe_per_period, max_drawdown.
    """
    if not equity_curve or len(equity_curve) < 2:
        return {
            "total_return": 0.0,
            "periodic_returns": [],
            "sharpe_per_period": float("nan"),
            "max_drawdown": 0.0,
        }

    equities = [e for _, e in equity_curve]
    rets: List[float] = []

    for i in range(1, len(equities)):
        prev, curr = equities[i - 1], equities[i]
        rets.append((curr / prev) - 1.0 if prev > 0 else 0.0)

    total_return = (equities[-1] / equities[0]) - 1.0 if equities[0] > 0 else 0.0

    if len(rets) >= 2:
        stdev = statistics.pstdev(rets) 
        sharpe = (statistics.mean(rets) / stdev) if stdev > 0 else float("nan")
    else:
        sharpe = float("nan")

    peak = equities[0]
    max_dd = 0.0
    for e in equities:
        peak = max(peak, e)
        drawdown = (e - peak) / peak if peak > 0 else 0.0
        max_dd = min(max_dd, drawdown)
    max_drawdown = abs(max_dd)

    return {
        "total_return": total_return,
        "periodic_returns": rets,
        "sharpe_per_period": sharpe,
        "max_drawdown": max_drawdown,
    }


def plot_equity_curve(equity_curve: List[Tuple], outfile: str) -> None:
    """
    Saves an equity curve PNG.
    """
    if not equity_curve:
        return
    import matplotlib.pyplot as plt

    xs = [t for t, _ in equity_curve]
    ys = [e for _, e in equity_curve]
    os.makedirs(os.path.dirname(outfile) or ".", exist_ok=True)

    plt.figure()
    plt.plot(xs, ys)
    plt.xlabel("Time")
    plt.ylabel("Equity")
    plt.title("Equity Curve")
    plt.tight_layout()
    plt.savefig(outfile)
    plt.close()


def write_markdown_report(
    metrics: Dict[str, object],
    equity_plot_relpath: str,
    outfile: str,
    context: Dict[str, object] | None = None,
) -> None:
    """
    Writes a Markdown report with a summary table, equity plot, and a short narrative.
    """
    os.makedirs(os.path.dirname(outfile) or ".", exist_ok=True)

    total_return = float(metrics.get("total_return", 0.0))
    sharpe_pp = metrics.get("sharpe_per_period", float("nan"))
    max_dd = float(metrics.get("max_drawdown", 0.0))

    fills = context.get("fills") if context else None
    rejects = context.get("rejects") if context else None
    errors = context.get("errors") if context else None

    def _fmt_sharpe(x):
        return f"{x:.4f}" if isinstance(x, float) and not math.isnan(x) else "NaN"

    lines: list[str] = []
    lines.append("# Backtest Performance Report\n")
    lines.append("## Summary Metrics\n")
    lines.append("| Metric | Value |\n")
    lines.append("|---|---:|\n")
    lines.append(f"| Total Return | {total_return:.4f} |\n")
    lines.append(f"| Sharpe (per-period) | {_fmt_sharpe(sharpe_pp)} |\n")
    lines.append(f"| Max Drawdown | {max_dd:.4f} |\n\n")

    lines.append("## Equity Curve\n")
    lines.append(f"![Equity Curve]({equity_plot_relpath})\n\n")

    lines.append("## Interpretation\n")
    lines.append(
        f"Over the backtest window, total return was {total_return:.2%}, "
        f"with a per-period Sharpe of {_fmt_sharpe(sharpe_pp)} and a maximum drawdown of "
        f"{max_dd:.2%}. "
    )
    if fills is not None and rejects is not None and errors is not None:
        lines.append(
            f"The engine recorded {fills} filled orders, {rejects} rejects, and {errors} logged errors. "
        )
    else:
        lines.append("\n")

    with open(outfile, "w") as f:
        f.write("".join(lines))

    with open(outfile, "w") as f:
        f.write("".join(lines))
