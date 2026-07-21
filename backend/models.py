from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MarketData(BaseModel):
    id: Optional[int] = None
    symbol: str
    price: float
    volume: float
    timestamp: datetime


class StrategySignal(BaseModel):
    id: Optional[int] = None
    symbol: str
    signal: str
    timestamp: datetime
