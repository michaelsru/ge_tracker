#!/usr/bin/env python3
"""OSRS Grand Exchange Menu Bar Widget

A macOS menu bar application that displays real-time OSRS Grand Exchange prices.
"""

import rumps
import requests
from datetime import datetime
import threading
import time
import webbrowser
from typing import Dict, Optional, Any


class OSRSGEMenuBar(rumps.App):
    """Menu bar application for tracking OSRS GE prices."""
    
    # Update interval in seconds
    UPDATE_INTERVAL = 300  # 5 minutes
    
    # API configuration
    API_BASE_URL = "https://prices.runescape.wiki/api/v1/osrs"
    USER_AGENT = "OSRS GE Menu Bar Widget - Personal Use"
    
    def __init__(self):
        super(OSRSGEMenuBar, self).__init__(
            name="⚔️",
            title="⚔️",
            quit_button=None
        )
        
        # Popular OSRS items with their IDs
        self.items: Dict[str, int] = {
            "Old school bond": 13190,
            "Cooked karambwan": 3144,
            "Raw karambwan": 3142,
        }
        
        # State management
        self.price_data: Dict[str, Dict[str, Any]] = {}
        self.last_update_str: str = "Never"
        self.new_data_available: bool = False
        self._running = True
        
        # UI Component References
        # Structure: {item_id: {'main': MenuItem, 'avg': MenuItem, 'high': MenuItem, 'low': MenuItem}}
        self.item_refs: Dict[int, Dict[str, rumps.MenuItem]] = {}
        
        # Build the menu ONCE
        self.build_static_menu()
        
        # Start background fetcher (Daemon thread)
        self.fetch_thread = threading.Thread(target=self.background_fetch_loop, daemon=True)
        self.fetch_thread.start()
        
        # Start UI updater (rumps Timer) - checks for data every 1 second
        self.timer = rumps.Timer(self.ui_update_loop, 1)
        self.timer.start()

    def build_static_menu(self):
        """Build the initial menu structure with references."""
        self.menu.add(rumps.MenuItem("OSRS GE Prices", callback=None))
        self.menu.add(rumps.separator)
        
        # Status Item (Dynamic)
        self.status_item = rumps.MenuItem("Loading prices...", callback=None)
        self.menu.add(self.status_item)
        self.menu.add(rumps.separator)
        
        # Item Lists
        for item_name, item_id in self.items.items():
            # Create Main Item
            main_item = rumps.MenuItem(f"{item_name}: ...", callback=None)
            
            # Create Submenu Items
            avg_item = rumps.MenuItem("💰 Average: ...", callback=None)
            high_item = rumps.MenuItem("📈 High: ...", callback=None)
            low_item = rumps.MenuItem("📉 Low: ...", callback=None)
            
            # Action Item (we can recreate this or keep it static, static is fine)
            # We need a closure for the callback
            def make_callback(iid):
                return lambda sender: self.open_price_chart(sender, iid)
                
            chart_item = rumps.MenuItem("📊 View Price Chart", callback=make_callback(item_id))
            
            # storage for updating
            self.item_refs[item_id] = {
                'main': main_item,
                'avg': avg_item,
                'high': high_item, 
                'low': low_item
            }
            
            # Assemble Submenu
            main_item.add(avg_item)
            main_item.add(high_item)
            main_item.add(low_item)
            main_item.add(rumps.separator)
            main_item.add(chart_item)
            
            # Add to Main Menu
            self.menu.add(main_item)
            
        # Footer
        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem("Refresh Now", callback=self.refresh_callback))
        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem("Quit", callback=self.quit_application))
    
    def format_price(self, price: int) -> str:
        """Format price with K/M/B suffixes."""
        if price >= 1_000_000_000:
            return f"{price/1_000_000_000:.2f}B"
        elif price >= 1_000_000:
            return f"{price/1_000_000:.2f}M"
        elif price >= 1_000:
            return f"{price/1_000:.1f}K"
        return str(price)
    
    def fetch_prices(self) -> Optional[Dict[str, Dict[str, Any]]]:
        """Fetch prices from OSRS Wiki API."""
        try:
            url = f"{self.API_BASE_URL}/latest"
            headers = {'User-Agent': self.USER_AGENT}
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return data.get('data', {})
        except Exception as e:
            print(f"Error fetching prices: {e}")
            return None
            
    def background_fetch_loop(self):
        """Thread implementation: fetches data sleep loop."""
        print("Background fetcher started.")
        while self._running:
            data = self.fetch_prices()
            if data:
                # Store data but DO NOT touch UI
                self.price_data = data
                self.last_update_str = datetime.now().strftime("%H:%M:%S")
                # Signal UI to update
                self.new_data_available = True
            
            # Sleep logic
            for _ in range(self.UPDATE_INTERVAL):
                if not self._running: return
                time.sleep(1)

    def ui_update_loop(self, _):
        """Timer callback: effectively the 'Main Thread' safe zone."""
        if self.new_data_available:
            self.update_menu_view()
            self.new_data_available = False
            
    def update_menu_view(self) -> None:
        """Update the menu UI with cached data."""
        # Update Status
        self.status_item.title = f"🕐 Updated: {self.last_update_str}"
        
        # Update Items
        for item_name, item_id in self.items.items():
            item_id_str = str(item_id)
            refs = self.item_refs.get(item_id)
            
            if not refs: continue
            
            if item_id_str in self.price_data:
                item_data = self.price_data[item_id_str]
                high = item_data.get('high', 0)
                low = item_data.get('low', 0)
                
                if high and low:
                    avg = (high + low) // 2
                    
                    # Update Titles
                    refs['main'].title = f"{item_name}: {self.format_price(avg)} gp"
                    refs['avg'].title = f"💰 Average: {self.format_price(avg)} gp"
                    refs['high'].title = f"📈 High: {self.format_price(high)} gp"
                    refs['low'].title = f"📉 Low: {self.format_price(low)} gp"
            else:
                refs['main'].title = f"{item_name}: N/A"

    def open_price_chart(self, sender: rumps.MenuItem, item_id: int) -> None:
        """Open OSRS Wiki price page in browser."""
        url = f"https://prices.runescape.wiki/osrs/item/{item_id}"
        webbrowser.open(url)
    
    def refresh_callback(self, sender: rumps.MenuItem) -> None:
        """Trigger an immediate background fetch."""
        # We start a one-off thread to fetch immediately so we don't wait for the loop sleep
        def one_off_refresh():
            print("Manual refresh triggered")
            data = self.fetch_prices()
            if data:
                self.price_data = data
                self.last_update_str = datetime.now().strftime("%H:%M:%S")
                self.new_data_available = True
                
        threading.Thread(target=one_off_refresh, daemon=True).start()
    
    def quit_application(self, sender: rumps.MenuItem) -> None:
        """Clean shutdown."""
        self._running = False
        rumps.quit_application()


def main():
    """Main entry point for the application."""
    app = OSRSGEMenuBar()
    app.run()


if __name__ == "__main__":
    main()
