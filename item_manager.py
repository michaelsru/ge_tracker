import json
import os
import requests
import difflib
from typing import Dict, List, Optional, Tuple

class ItemManager:
    """Manages OSRS item mappings, user watchlist, and persistence."""
    
    MAPPING_URL = "https://prices.runescape.wiki/api/v1/osrs/mapping"
    CONFIG_FILE = os.path.expanduser("~/.ge_tracker_config.json")
    USER_AGENT = "OSRS GE Menu Bar Widget - Personal Use"
    
    def __init__(self):
        # Maps Name -> ID (loaded from API)
        self.name_to_id: Dict[str, int] = {}
        # Maps ID -> Name (loaded from API)
        self.id_to_name: Dict[int, str] = {}
        
        # User's watchlist: List of dicts
        # Schema: {'type': 'item', 'name': '...', 'id': 123} OR {'type': 'section', 'label': '...'}
        self.watchlist: List[Dict] = []
        
        self.load_config()
        self.refresh_mappings()

    def refresh_mappings(self) -> None:
        """Fetch latest item mappings from OSRS Wiki API."""
        try:
            print("Fetching item mappings...")
            headers = {'User-Agent': self.USER_AGENT}
            response = requests.get(self.MAPPING_URL, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            # Data is a list of dicts: {'id': 123, 'name': 'Item', ...}
            
            self.name_to_id.clear()
            self.id_to_name.clear()
            
            for item in data:
                # Some items might not be tradeable, but let's map everything
                item_name = item.get('name')
                item_id = item.get('id')
                
                if item_name and item_id:
                    self.name_to_id[item_name.lower()] = item_id
                    self.id_to_name[item_id] = item_name
            
            print(f"Loaded {len(self.name_to_id)} items.")
            
        except Exception as e:
            print(f"Error fetching mappings: {e}")
            # If fetch fails, we rely on whatever we might have, or empty.

    def search_item(self, query: str) -> Tuple[Optional[str], Optional[int], List[str]]:
        """Search for an item by name using tokenized 'contains' logic.
        
        Returns:
            (BestMatchName, BestMatchID, List[Alternatives])
        """
        query_lower = query.lower().strip()
        
        # 1. Exact Match
        if query_lower in self.name_to_id:
            real_name = self.id_to_name[self.name_to_id[query_lower]]
            return real_name, self.name_to_id[query_lower], []
            
        # 2. Tokenized Contains Search
        # Much faster than difflib for large datasets (20k+ items)
        tokens = query_lower.split()
        if not tokens: return None, None, []
        
        # Find all keys that contain ALL tokens
        # Optimization: Filter by first token, then check others
        matches = []
        for name in self.name_to_id:
            if all(token in name for token in tokens):
                matches.append(name)
                
        if not matches:
            return None, None, []
            
        # 3. Rank Results
        # Heuristic: shorter names are usually the 'base' item
        # e.g. "Rune scimitar" vs "Rune scimitar (orn)"
        matches.sort(key=len)
        
        # Take best
        best_match_key = matches[0]
        real_name = self.id_to_name[self.name_to_id[best_match_key]]
        best_id = self.name_to_id[best_match_key]
        
        # Get suggestions (up to 5 more)
        suggestions = []
        for key in matches[1:6]:
            suggestions.append(self.id_to_name[self.name_to_id[key]])
            
        return real_name, best_id, suggestions

    def add_to_watchlist(self, name: str, item_id: int) -> None:
        """Add an item to the user's watchlist."""
        # Check if already exists to avoid dupes (optional, but good UX)
        for entry in self.watchlist:
            if entry.get('type') == 'item' and entry.get('id') == item_id:
                return
        
        self.watchlist.append({
            'type': 'item',
            'name': name,
            'id': item_id
        })
        self.save_config()

    def add_items_to_watchlist(self, items: List[Tuple[str, int]]) -> None:
        """Add multiple items to the watchlist at once."""
        existing_ids = {entry['id'] for entry in self.watchlist if entry.get('type') == 'item'}
        
        for name, item_id in items:
            if item_id not in existing_ids:
                self.watchlist.append({
                    'type': 'item',
                    'name': name,
                    'id': item_id
                })
                existing_ids.add(item_id)
        self.save_config()
        
    def add_section(self, label: str) -> None:
        """Add a new section divider."""
        self.watchlist.append({
            'type': 'section',
            'label': label
        })
        self.save_config()

    def remove_from_watchlist(self, name: str) -> None:
        """Remove an item (or section) from the watchlist by name/label."""
        self.watchlist = [
            entry for entry in self.watchlist 
            if not (entry.get('name') == name or entry.get('label') == name)
        ]
        self.save_config()

    def remove_items_from_watchlist(self, names: List[str]) -> None:
        """Remove multiple items/sections from the watchlist."""
        names_set = set(names)
        self.watchlist = [
            entry for entry in self.watchlist 
            if not (entry.get('name') in names_set or entry.get('label') in names_set)
        ]
        self.save_config()

    def save_config(self) -> None:
        """Save the current watchlist to disk atomically."""
        try:
            # Write to a temp file first
            temp_file = self.CONFIG_FILE + ".tmp"
            with open(temp_file, 'w') as f:
                json.dump(self.watchlist, f, indent=4)
            # Atomic rename
            os.replace(temp_file, self.CONFIG_FILE)
        except Exception as e:
            print(f"Error saving config: {e}")

    def load_config(self) -> None:
        """Load the watchlist from disk, handling migration."""
        if not os.path.exists(self.CONFIG_FILE):
            # separate default
            self.watchlist = [
                {'type': 'item', 'name': "Old school bond", 'id': 13190},
                {'type': 'item', 'name': "Cooked karambwan", 'id': 3144},
                {'type': 'item', 'name': "Raw karambwan", 'id': 3142},
            ]
            return

        try:
            with open(self.CONFIG_FILE, 'r') as f:
                data = json.load(f)
                
            # Migration Logic: Dict -> List
            if isinstance(data, dict):
                print("Migrating config from Dict to List...")
                new_list = []
                for name, iid in data.items():
                    new_list.append({
                        'type': 'item',
                        'name': name,
                        'id': iid
                    })
                self.watchlist = new_list
                # Save immediately to persist migration
                self.save_config()
            else:
                self.watchlist = data
                
        except Exception as e:
            print(f"Error loading config: {e}")
            self.watchlist = []
