from tinyflux import TinyFlux, Point, TagQuery
from typing import List
import os
from datetime import datetime

class PriceDB:
    def __init__(self, db_path: str = "prices.csv"):
        self.db = TinyFlux(db_path)

    def insert_price(self, item_id: int, price: int, volume: int):
        p = Point(
            time=datetime.now(),
            tags={"item_id": str(item_id)},
            fields={"price": price, "volume": volume}
        )
        self.db.insert(p)

    def get_history(self, item_id: int, hours: int = 24) -> List[dict]:
        # TinyFlux query logic could be complex for time ranges, but we'll simplisticly fetch all for the item 
        # and filter in memory if needed, or rely on TinyFlux's optimization if we key properly.
        # For a small app, fetching by tag is fine.
        
        # Note: TinyFlux query capabilities are limited compared to InfluxDB. 
        # We might need to handle time filtering manually or use its range queries if supported.
        
        # Simple retrieval:
        # We want to optimize this later, but for now let's just get points for the item.
        # To make it efficient, we might want separate DBs per item or careful indexing?
        # TinyFlux is a flat file append log. 
        pass 
        # Actually, let's just implement a simple fetch for now.
        
        Tag = TagQuery()
        query = self.db.search(Tag.item_id == str(item_id))
        # Filter by time manually if needed, assuming query returns sorted or we sort.
        # Ideally we limit the query.
        
        results = []
        cutoff = datetime.now().timestamp() - (hours * 3600)
        
        for point in query:
             if point.time.timestamp() > cutoff:
                 results.append({
                     "timestamp": int(point.time.timestamp()),
                     "price": point.fields["price"],
                     "volume": point.fields["volume"]
                 })
                 
        return results

db = PriceDB(os.path.join(os.path.dirname(__file__), "prices.db"))
