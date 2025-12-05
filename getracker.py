#!/usr/bin/env python3
"""OSRS Grand Exchange Menu Bar Widget

A macOS menu bar application that displays real-time OSRS Grand Exchange prices.
"""

import rumps
import requests
import os
from datetime import datetime
import threading
import time
import webbrowser
from typing import Dict, Optional, Any
from item_manager import ItemManager


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
        
        # Initialize Item Manager (Handles persistence & mapping)
        self.item_manager = ItemManager()
        
        # State management
        self.price_data: Dict[str, Dict[str, Any]] = {}
        self.last_update_str: str = "Never"
        self.new_data_available: bool = False
        self._running = True
        
        # UI Component References
        # Structure: {item_id: {'main': MenuItem, 'avg': MenuItem, 'high': MenuItem, 'low': MenuItem}}
        self.item_refs: Dict[int, Dict[str, rumps.MenuItem]] = {}
        
        # Build the menu
        self.rebuild_menu()
        
        # Start background fetcher (Daemon thread)
        self.fetch_thread = threading.Thread(target=self.background_fetch_loop, daemon=True)
        self.fetch_thread.start()
        
        # Start UI updater (rumps Timer) - checks for data every 1 second
        self.timer = rumps.Timer(self.ui_update_loop, 1)
        self.timer.start()

    def rebuild_menu(self):
        """Completely (re)build the menu structure."""
        self.menu.clear()
        self.item_refs.clear()
        
        self.menu.add(rumps.MenuItem("OSRS GE Prices", callback=None))
        self.menu.add(rumps.separator)
        
        # Status Item (Dynamic)
        self.status_item = rumps.MenuItem(f"🕐 Updated: {self.last_update_str}", callback=None)
        self.menu.add(self.status_item)
        self.menu.add(rumps.separator)
        
        # Item Lists from Watchlist
        # We iterate over the ItemManager's watchlist
        for item_name, item_id in self.item_manager.watchlist.items():
            # Create Main Item
            # We initialize with "..." or cached data if available
            price_text = f"{item_name}: ..."
            
            # Check if we already have data for generic 'rebuild' (e.g. after adding item)
            avg_text = "💰 Average: ..."
            high_text = "📈 High: ..."
            low_text = "📉 Low: ..."
            
            # (Optional) Pre-fill if we have data
            item_id_str = str(item_id)
            if item_id_str in self.price_data:
                data = self.price_data[item_id_str]
                high, low = data.get('high', 0), data.get('low', 0)
                if high and low:
                    avg = (high + low) // 2
                    price_text = f"{item_name}: {self.format_price(avg)} gp"
                    avg_text = f"💰 Average: {self.format_price(avg)} gp"
                    high_text = f"📈 High: {self.format_price(high)} gp"
                    low_text = f"📉 Low: {self.format_price(low)} gp"

            main_item = rumps.MenuItem(price_text, callback=None)
            
            # Create Submenu Items
            avg_item = rumps.MenuItem(avg_text, callback=None)
            high_item = rumps.MenuItem(high_text, callback=None)
            low_item = rumps.MenuItem(low_text, callback=None)
            
            # Chart Action
            def make_chart_callback(iid):
                return lambda sender: self.open_price_chart(sender, iid)
            chart_item = rumps.MenuItem("📊 View Price Chart", callback=make_chart_callback(item_id))
            
            # Remove Action
            def make_remove_callback(n):
                return lambda sender: self.remove_item_callback(sender, n)
            remove_item = rumps.MenuItem("❌ Remove Item", callback=make_remove_callback(item_name))
            
            # Storage for fast updating
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
            main_item.add(remove_item)
            
            # Add to Main Menu
            self.menu.add(main_item)
            
        # Footer
        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem("⚙️ Settings...", callback=self.open_settings))
        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem("Refresh Now", callback=self.refresh_callback))
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
            
            # Only fetch simple validation or all items? 
            # The /latest endpoint returns ALL items. That's fine.
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
                self.price_data = data
                self.last_update_str = datetime.now().strftime("%H:%M:%S")
                self.new_data_available = True
            
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
        self.status_item.title = f"🕐 Updated: {self.last_update_str}"
        
        # Iterate over what we are CURRENTLY tracking
        for item_name, item_id in self.item_manager.watchlist.items():
            refs = self.item_refs.get(item_id)
            if not refs: continue # Should invoke rebuild if this happens often
            
            item_id_str = str(item_id)
            if item_id_str in self.price_data:
                item_data = self.price_data[item_id_str]
                high = item_data.get('high', 0)
                low = item_data.get('low', 0)
                
                if high and low:
                    avg = (high + low) // 2
                    refs['main'].title = f"{item_name}: {self.format_price(avg)} gp"
                    refs['avg'].title = f"💰 Average: {self.format_price(avg)} gp"
                    refs['high'].title = f"📈 High: {self.format_price(high)} gp"
                    refs['low'].title = f"📉 Low: {self.format_price(low)} gp"
            else:
                refs['main'].title = f"{item_name}: N/A"

    def open_settings(self, sender) -> None:
        """Launch the separate Settings GUI process."""
        import subprocess
        import sys
        
        # Check if already open
        if hasattr(self, 'settings_process') and self.settings_process.poll() is None:
            # Already running, bring to front? (Hard cross-process, just ignore or re-launch)
            return

        try:
            # Launch in separate process using same python interpreter
            # When frozen, sys.executable is the app bundle executable.
            # We pass --settings to tell it to run the settings GUI instead of the main app.
            self.settings_process = subprocess.Popen([sys.executable, "--settings"])
            
            # Start a timer to watch for it closing
            self.settings_watcher = rumps.Timer(self.check_settings_closed, 1)
            self.settings_watcher.start()
        except Exception as e:
            rumps.alert("Error", f"Could not open settings: {e}")

    def check_settings_closed(self, sender):
        """Timer callback to check if settings process finished."""
        if hasattr(self, 'settings_process'):
            if self.settings_process.poll() is not None:
                # Process finished
                self.settings_watcher.stop()
                del self.settings_process
                
                # Reload config and rebuild menu
                print("Settings closed, reloading config...")
                self.item_manager.load_config()
                self.rebuild_menu()

    def remove_item_callback(self, sender, item_name: str) -> None:
        """Remove item from watchlist."""
        self.item_manager.remove_from_watchlist(item_name)
        self.rebuild_menu()

    def open_price_chart(self, sender: rumps.MenuItem, item_id: int) -> None:
        """Open OSRS Wiki price page in browser."""
        url = f"https://prices.runescape.wiki/osrs/item/{item_id}"
        webbrowser.open(url)
    
    def refresh_callback(self, sender: rumps.MenuItem) -> None:
        """Trigger an immediate background fetch."""
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
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--settings':
        import settings_gui
        settings_gui.main()
    else:
        app = OSRSGEMenuBar()
        app.run()


if __name__ == "__main__":
    main()
