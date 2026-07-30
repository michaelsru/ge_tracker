from pydantic import BaseModel
from typing import List, Optional, Dict

class Item(BaseModel):
    id: int
    name: str
    high: int
    low: int
    highTime: int
    lowTime: int
    highVolume: Optional[int] = 0
    lowVolume: Optional[int] = 0
    dailyVolume: Optional[int] = 0

class ItemDetail(BaseModel):
    id: int
    name: str

class Recipe(BaseModel):
    id: str
    name: str
    inputs: List[ItemDetail]
    outputs: List[ItemDetail]
    tags: List[str]
    profit_margin: int
    roi: float
    is_profitable: bool
    # Skilling fields (optional — only set when recipe has xp)
    xp: Optional[float] = None
    level: Optional[int] = None
    gp_xp: Optional[float] = None
    input_price: Optional[int] = None
    output_price: Optional[int] = None
    input_volume: Optional[int] = None   # daily grimy buy volume
    output_volume: Optional[int] = None  # daily clean sell volume

class PricePoint(BaseModel):
    timestamp: int
    item_id: int
    price: int
    volume: int
