# models.py
from dataclasses import dataclass, field
import datetime 

@dataclass(frozen=True)
class MarketDataPoint:
    timestamp: datetime.datetime
    symbol: str
    price: float
    
class OrderError(Exception):
    """Raised for invalid orders (e.g., non-positive qty/price, bad side)."""
    pass

class ExecutionError(Exception):
    """Raised when execution fails (simulated or real)."""
    pass
    
@dataclass
class Order:
    """
    Mutable order: all fields can be updated at runtime.
    """
    symbol: str
    quantity: int
    price: float
    side: str = field(default="BUY")
    status: str = field(default="NEW")
    
    def validate(self) -> None:
        if self.quantity is None or self.quantity <= 0:
            raise OrderError("Quantity must be positive.")
        if self.price is None or self.price <= 0:
            raise OrderError("Price must be positive.")
        if self.side not in {"BUY", "SELL"}:
            raise OrderError("Side must be 'BUY' or 'SELL'.")
