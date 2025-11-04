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
	    "Cooked karambwan": 3144
        }
        
        self.price_data: Dict[str, Dict[str, Any]] = {}
        self.last_update: str = "Never"
        self._update_lock = threading.Lock()
        self._running = True
        
        # Build initial menu
        self.menu = [
            rumps.MenuItem("OSRS GE Prices", callback=None),
            rumps.separator,
            rumps.MenuItem("Loading prices...", callback=None),
            rumps.separator,
            rumps.MenuItem("Refresh Now", callback=self.refresh_callback),
            rumps.separator,
            rumps.MenuItem("Quit", callback=self.quit_application)
        ]
        
        # Start background price fetcher
        self.start_price_updater()
    
    def format_price(self, price: int) -> str:
        """Format price with K/M/B suffixes.
        
        Args:
            price: Price value to format
            
        Returns:
            Formatted price string
        """
        if price >= 1_000_000_000:
            return f"{price/1_000_000_000:.2f}B"
        elif price >= 1_000_000:
            return f"{price/1_000_000:.2f}M"
        elif price >= 1_000:
            return f"{price/1_000:.1f}K"
        return str(price)
    
    def fetch_prices(self) -> Optional[Dict[str, Dict[str, Any]]]:
        """Fetch prices from OSRS Wiki API.
        
        Returns:
            Dictionary of price data or None on error
        """
        try:
            url = f"{self.API_BASE_URL}/latest"
            headers = {'User-Agent': self.USER_AGENT}
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return data.get('data', {})
        except requests.exceptions.RequestException as e:
            print(f"Error fetching prices: {e}")
            return None
        except (ValueError, KeyError) as e:
            print(f"Error parsing price data: {e}")
            return None
    
    def open_price_chart(self, sender: rumps.MenuItem, item_id: int) -> None:
        """Open OSRS Wiki price page in browser.
        
        Args:
            sender: Menu item that triggered the callback
            item_id: OSRS item ID
        """
        url = f"https://prices.runescape.wiki/osrs/item/{item_id}"
        webbrowser.open(url)
    
    def update_menu_items(self) -> None:
        """Update the menu with current prices."""
        with self._update_lock:
            # Clear all items
            self.menu.clear()
            
            # Rebuild menu header
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
                            # Use closure to capture item_id properly
                            def make_callback(item_id_val):
                                return lambda sender: self.open_price_chart(sender, item_id_val)
                            
                            submenu = [
                                rumps.MenuItem(f"💰 Average: {self.format_price(avg)} gp", callback=None),
                                rumps.MenuItem(f"📈 High: {self.format_price(high)} gp", callback=None),
                                rumps.MenuItem(f"📉 Low: {self.format_price(low)} gp", callback=None),
                                rumps.separator,
                                rumps.MenuItem("📊 View Price Chart", callback=make_callback(item_id))
                            ]
                            
                            # Add submenu items
                            for sub_item in submenu:
                                price_item.add(sub_item)
                            
                            self.menu.add(price_item)
            
            # Add footer items
            self.menu.add(rumps.separator)
            self.menu.add(rumps.MenuItem("Refresh Now", callback=self.refresh_callback))
            self.menu.add(rumps.separator)
            self.menu.add(rumps.MenuItem("Quit", callback=self.quit_application))
    
    def background_update(self) -> None:
        """Background thread to periodically fetch prices."""
        while self._running:
            data = self.fetch_prices()
            if data:
                with self._update_lock:
                    self.price_data = data
                    self.last_update = datetime.now().strftime("%H:%M:%S")
                self.update_menu_items()
            
            # Sleep in small increments to allow quick shutdown
            for _ in range(self.UPDATE_INTERVAL):
                if not self._running:
                    break
                time.sleep(1)
    
    def start_price_updater(self) -> None:
        """Start the background price updater thread."""
        # Initial fetch in separate thread
        threading.Thread(target=self.initial_fetch, daemon=True).start()
        
        # Start periodic updates
        update_thread = threading.Thread(target=self.background_update, daemon=True)
        update_thread.start()
    
    def initial_fetch(self) -> None:
        """Fetch prices immediately on startup."""
        time.sleep(0.5)  # Small delay to let UI initialize
        data = self.fetch_prices()
        if data:
            with self._update_lock:
                self.price_data = data
                self.last_update = datetime.now().strftime("%H:%M:%S")
            self.update_menu_items()
    
    def refresh_callback(self, sender: rumps.MenuItem) -> None:
        """Handle manual refresh.
        
        Args:
            sender: Menu item that triggered the callback
        """
        def refresh():
            data = self.fetch_prices()
            if data:
                with self._update_lock:
                    self.price_data = data
                    self.last_update = datetime.now().strftime("%H:%M:%S")
                self.update_menu_items()
        
        threading.Thread(target=refresh, daemon=True).start()
    
    def quit_application(self, sender: rumps.MenuItem) -> None:
        """Clean shutdown of the application.
        
        Args:
            sender: Menu item that triggered the callback
        """
        self._running = False
        rumps.quit_application()


def main():
    """Main entry point for the application."""
    app = OSRSGEMenuBar()
    app.run()


if __name__ == "__main__":
    main()
