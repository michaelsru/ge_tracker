#!/usr/bin/env python3
import rumps
import requests
from datetime import datetime
import threading
import time
import webbrowser

class OSRSGEMenuBar(rumps.App):
    def __init__(self):
        super(OSRSGEMenuBar, self).__init__(
            name="⚔️",
            title="⚔️",
            quit_button=None
        )
        
        # Popular OSRS items with their IDs
        self.items = {
            "Old school bond": 13190,
            "Twisted bow": 20997,
            "Scythe of vitur": 22325,
            "Dragon claws": 13652,
            "Abyssal whip": 4151,
            "Armadyl godsword": 11802,
            "Dragon warhammer": 13576,
            "Bandos chestplate": 11832,
            "Abyssal dagger": 13265,
            "Dragon pickaxe": 11920
        }
        
        self.price_data = {}
        self.last_update = "Never"
        
        # Build initial menu
        self.menu = [
            rumps.MenuItem("OSRS GE Prices", callback=None),
            rumps.separator,
            rumps.MenuItem("Loading prices...", callback=None),
            rumps.separator,
            rumps.MenuItem("Refresh Now", callback=self.refresh_callback),
            rumps.separator,
            rumps.MenuItem("Quit", callback=rumps.quit_application)
        ]
        
        # Start background price fetcher
        self.start_price_updater()
    
    def format_price(self, price):
        """Format price with K/M/B suffixes"""
        if price >= 1_000_000_000:
            return f"{price/1_000_000_000:.2f}B"
        elif price >= 1_000_000:
            return f"{price/1_000_000:.2f}M"
        elif price >= 1_000:
            return f"{price/1_000:.1f}K"
        return str(price)
    
    def fetch_prices(self):
        """Fetch prices from OSRS Wiki API"""
        try:
            url = "https://prices.runescape.wiki/api/v1/osrs/latest"
            headers = {'User-Agent': 'OSRS GE Menu Bar Widget - Personal Use'}
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('data', {})
        except Exception as e:
            print(f"Error fetching prices: {e}")
        return None
    
    def open_price_chart(self, sender, item_id):
        """Open OSRS Wiki price page in browser"""
        url = f"https://prices.runescape.wiki/osrs/item/{item_id}"
        webbrowser.open(url)
    
    def update_menu_items(self):
        """Update the menu with current prices"""
        # Clear all items
        self.menu.clear()
        
        # Rebuild menu
        self.menu.add(rumps.MenuItem("OSRS GE Prices", callback=None))
        self.menu.add(rumps.separator)
        
        if not self.price_data:
            self.menu.add(rumps.MenuItem("❌ Unable to fetch prices", callback=None))
        else:
            # Add updated timestamp
            self.menu.add(rumps.MenuItem(f"🕐 Updated: {self.last_update}", callback=None))
            self.menu.add(rumps.separator)
            
            # Add price items
            for item_name, item_id in self.items.items():
                item_id_str = str(item_id)
                if item_id_str in self.price_data:
                    item_data = self.price_data[item_id_str]
                    high = item_data.get('high', 0)
                    low = item_data.get('low', 0)
                    
                    if high and low:
                        avg = (high + low) // 2
                        price_text = f"{item_name}: {self.format_price(avg)} gp"
                        
                        # Create menu item
                        price_item = rumps.MenuItem(price_text)
                        
                        # Create submenu with details and chart option
                        submenu = [
                            rumps.MenuItem(f"💰 Average: {self.format_price(avg)} gp", callback=None),
                            rumps.MenuItem(f"📈 High: {self.format_price(high)} gp", callback=None),
                            rumps.MenuItem(f"📉 Low: {self.format_price(low)} gp", callback=None),
                            rumps.separator,
                            rumps.MenuItem(f"📊 View Price Chart", 
                                         callback=lambda sender, id=item_id: self.open_price_chart(sender, id))
                        ]
                        
                        # Add submenu items
                        for sub_item in submenu:
                            price_item.add(sub_item)
                        
                        self.menu.add(price_item)
        
        # Add footer items
        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem("Refresh Now", callback=self.refresh_callback))
        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem("Quit", callback=rumps.quit_application))
    
    def background_update(self):
        """Background thread to periodically fetch prices"""
        while True:
            data = self.fetch_prices()
            if data:
                self.price_data = data
                self.last_update = datetime.now().strftime("%H:%M:%S")
                self.update_menu_items()
            time.sleep(300)  # Update every 5 minutes
    
    def start_price_updater(self):
        """Start the background price updater thread"""
        # Initial fetch
        threading.Thread(target=self.initial_fetch, daemon=True).start()
        
        # Start periodic updates
        thread = threading.Thread(target=self.background_update, daemon=True)
        thread.start()
    
    def initial_fetch(self):
        """Fetch prices immediately on startup"""
        time.sleep(0.5)  # Small delay to let UI initialize
        data = self.fetch_prices()
        if data:
            self.price_data = data
            self.last_update = datetime.now().strftime("%H:%M:%S")
            self.update_menu_items()
    
    def refresh_callback(self, _):
        """Handle manual refresh"""
        def refresh():
            data = self.fetch_prices()
            if data:
                self.price_data = data
                self.last_update = datetime.now().strftime("%H:%M:%S")
                self.update_menu_items()
        
        threading.Thread(target=refresh, daemon=True).start()

if __name__ == "__main__":
    app = OSRSGEMenuBar()
    app.run()
