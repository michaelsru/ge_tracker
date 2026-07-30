import requests
import time
from typing import Dict, List, Any
from .models import Recipe, Item
from .db import db

class Engine:
    API_BASE_URL = "https://prices.runescape.wiki/api/v1/osrs"
    USER_AGENT = "OSRS GE Tracker Web App - Personal Use"
    TAX_RATE = 0.01
    TAX_CAP = 5_000_000

    MAPPING_URL = "https://prices.runescape.wiki/api/v1/osrs/mapping"

    def __init__(self):
        self.prices: Dict[str, Any] = {}
        self.volumes: Dict[str, int] = {}
        self.recipes: List[dict] = []
        self.id_to_name: Dict[int, str] = {}
        self.fetch_mappings()
        self.load_recipes()

    def fetch_mappings(self):
        try:
            headers = {'User-Agent': self.USER_AGENT}
            response = requests.get(self.MAPPING_URL, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            for item in data:
                if 'id' in item and 'name' in item:
                    self.id_to_name[item['id']] = item['name']
        except Exception as e:
            print(f"Error fetching mappings: {e}")

    def load_recipes(self):
        import json
        import os
        try:
            with open(os.path.join(os.path.dirname(__file__), "recipes.json"), "r") as f:
                self.recipes = json.load(f)
        except Exception as e:
            print(f"Error loading recipes: {e}")
            self.recipes = []
        
    def fetch_prices(self):
        """Fetch latest prices + daily volumes and update local state."""
        try:
            headers = {'User-Agent': self.USER_AGENT}

            price_resp = requests.get(f"{self.API_BASE_URL}/latest", headers=headers, timeout=10)
            price_resp.raise_for_status()
            data = price_resp.json().get('data', {})
            self.prices = data

            vol_resp = requests.get(f"{self.API_BASE_URL}/volumes", headers=headers, timeout=10)
            vol_resp.raise_for_status()
            self.volumes = vol_resp.json().get('data', {})

            tracked_ids = set()
            for r in self.recipes:
                tracked_ids.update(r['inputs'])
                tracked_ids.update(r['outputs'])

            for iid in tracked_ids:
                sid = str(iid)
                if sid in data:
                    item_data = data[sid]
                    avg_price = (item_data.get('high', 0) + item_data.get('low', 0)) // 2
                    vol = self.volumes.get(sid, 0)
                    if avg_price > 0:
                        db.insert_price(iid, avg_price, vol)

            return True
        except Exception as e:
            print(f"Error fetching prices: {e}")
            return False

    def calculate_tax(self, price: int) -> int:
        return min(int(price * self.TAX_RATE), self.TAX_CAP)

    def get_processed_recipes(self) -> List[Recipe]:
        results = []
        for r in self.recipes:
            total_input_cost = 0
            total_output_val = 0
            output_qty = r.get('output_qty', 1)  # e.g. 12 for gem → bolt tips

            input_details = []
            output_details = []

            # Calculate Inputs
            input_volume = 0
            for iid in r['inputs']:
                sid = str(iid)
                price = 0
                if sid in self.prices:
                    p = self.prices[sid]
                    price = p.get('low', 0)
                    if not price: price = p.get('high', 0)
                input_volume += self.volumes.get(sid, 0)
                total_input_cost += price
                input_details.append({
                    "id": iid,
                    "name": self.id_to_name.get(iid, f"Item {iid}"),
                    "price": price or None,
                    "qty": 1,
                })

            # Calculate Outputs (qty-scaled)
            output_volume = 0
            for iid in r['outputs']:
                sid = str(iid)
                price = 0
                if sid in self.prices:
                    p = self.prices[sid]
                    price = p.get('high', 0)
                    if not price: price = p.get('low', 0)
                    revenue = (price - self.calculate_tax(price)) * output_qty
                    total_output_val += revenue
                output_volume += self.volumes.get(sid, 0)
                output_details.append({
                    "id": iid,
                    "name": self.id_to_name.get(iid, f"Item {iid}"),
                    "price": price or None,
                    "qty": output_qty,
                })

            profit = total_output_val - total_input_cost
            roi = (profit / total_input_cost * 100) if total_input_cost > 0 else 0

            # Scale XP by output_qty so frontend's xp * uph gives correct hourly XP
            raw_xp = r.get('xp')
            effective_xp = raw_xp * output_qty if raw_xp else None
            gp_xp = round(profit / effective_xp, 2) if effective_xp and effective_xp > 0 else None
            level = r.get('level')

            results.append(Recipe(
                id=r['id'],
                name=r['name'],
                inputs=input_details,
                outputs=output_details,
                tags=r.get('tags', []),
                profit_margin=int(profit),
                roi=round(roi, 2),
                is_profitable=profit > 0,
                xp=effective_xp,
                level=level,
                gp_xp=gp_xp,
                input_price=total_input_cost,
                output_price=int(total_output_val),
                input_volume=input_volume or None,
                output_volume=output_volume or None,
                hidden=r.get('hidden', False),
            ))

        return results

    def set_recipe_hidden(self, recipe_id: str, hidden: bool) -> bool:
        import json
        import os
        recipes_path = os.path.join(os.path.dirname(__file__), "recipes.json")
        try:
            with open(recipes_path, "r") as f:
                recipes_data = json.load(f)
            found = False
            for r in recipes_data:
                if r.get("id") == recipe_id:
                    r["hidden"] = hidden
                    found = True
                    break
            if not found:
                return False
            with open(recipes_path, "w") as f:
                json.dump(recipes_data, f, indent=4)
            self.load_recipes()
            return True
        except Exception as e:
            print(f"Error setting recipe hidden: {e}")
            return False

engine = Engine()
