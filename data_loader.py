# data_loader.py
from typing import List
import csv
import datetime as dt
from models import MarketDataPoint

def load_market_data(csv_path: str) -> List[MarketDataPoint]:
    data: List[MarketDataPoint] = []
    with open(csv_path, "r", newline="") as f:
        reader = csv.DictReader(f)

        required = {"timestamp", "symbol", "price"}
        if reader.fieldnames is None or not required.issubset({c.strip() for c in reader.fieldnames}):
            raise ValueError("CSV must contain columns: timestamp, symbol, price")

        for row in reader:
            ts = dt.datetime.fromisoformat(row["timestamp"])
            sym = row["symbol"]
            px = float(row["price"])
            data.append(MarketDataPoint(timestamp=ts, symbol=sym, price=px))

    data.sort(key=lambda mdp: mdp.timestamp)
    return data
