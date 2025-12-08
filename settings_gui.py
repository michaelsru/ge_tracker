import tkinter as tk
from tkinter import ttk, messagebox
from item_manager import ItemManager

class DragDropListbox(tk.Listbox):
    """A Listbox that supports drag-and-drop reordering."""
    def __init__(self, master, **kw):
        kw['selectmode'] = tk.SINGLE
        tk.Listbox.__init__(self, master, kw)
        self.bind('<Button-1>', self.click)
        self.bind('<B1-Motion>', self.drag)
        self.bind('<ButtonRelease-1>', self.release)
        self.curIndex = None
        self.on_reorder_callback = None

    def click(self, event):
        self.curIndex = self.nearest(event.y)

    def drag(self, event):
        i = self.nearest(event.y)
        if i < 0 or i >= self.size(): return
            
        if i != self.curIndex:
            text = self.get(self.curIndex)
            self.delete(self.curIndex)
            self.insert(i, text)
            self.activate(i)
            self.curIndex = i

    def release(self, event):
        if self.on_reorder_callback:
            self.on_reorder_callback()

class SettingsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GE Tracker Settings")
        self.root.geometry("600x400")
        
        self.item_manager = ItemManager()
        
        # --- Styles ---
        style = ttk.Style()
        style.configure("Bold.TLabel", font=('Helvetica', 12, 'bold'))
        
        # --- Main Layout ---
        paned = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left Frame
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)
        
        ttk.Label(left_frame, text="Current Watchlist", style="Bold.TLabel").pack(pady=5)
        ttk.Label(left_frame, text="(Drag items to reorder)").pack(pady=0)
        
        # Use Custom DragDrop Listbox
        self.watchlist_listbox = DragDropListbox(left_frame)
        self.watchlist_listbox.pack(fill=tk.BOTH, expand=True, padx=5)
        self.watchlist_listbox.on_reorder_callback = self.save_reorder
        
        btn_remove = ttk.Button(left_frame, text="Remove Selected", command=self.remove_selected)
        btn_remove.pack(pady=5)
        
        # Right Frame
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=1)
        
        ttk.Label(right_frame, text="Add New Item", style="Bold.TLabel").pack(pady=5)
        
        # Search Container
        search_container = ttk.Frame(right_frame)
        search_container.pack(fill=tk.X, padx=5)
        
        self.search_var = tk.StringVar()
        entry_search = ttk.Entry(search_container, textvariable=self.search_var)
        entry_search.pack(side=tk.LEFT, fill=tk.X, expand=True)
        entry_search.bind('<Return>', self.perform_search)
        
        btn_search = ttk.Button(search_container, text="Search", command=self.perform_search)
        btn_search.pack(side=tk.LEFT, padx=(5, 0))
        
        # Results List
        ttk.Label(right_frame, text="Search Results:").pack(anchor='w', padx=5, pady=(10, 0))
        self.results_listbox = tk.Listbox(right_frame)
        self.results_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        btn_add = ttk.Button(right_frame, text="Add Selected to Watchlist", command=self.add_selected)
        btn_add.pack(pady=5)
        
        # Initialize
        self.refresh_watchlist_ui()
        self.current_search_results = []

    def refresh_watchlist_ui(self):
        """Reloads the watchlist listbox from item_manager."""
        self.watchlist_listbox.delete(0, tk.END)
        # REMOVED SORT: Iterate directly to respect order
        for name in self.item_manager.watchlist.keys():
            self.watchlist_listbox.insert(tk.END, name)

    def save_reorder(self):
        """Called when listbox is reordered by user."""
        # Reconstruct the watchlist dictionary based on new order
        new_order_names = self.watchlist_listbox.get(0, tk.END)
        new_watchlist = {}
        
        for name in new_order_names:
            # Get ID from old watchlist (it must exist)
            if name in self.item_manager.watchlist:
                new_watchlist[name] = self.item_manager.watchlist[name]
        
        self.item_manager.watchlist = new_watchlist
        self.item_manager.save_config()

    def remove_selected(self):
        selection = self.watchlist_listbox.curselection()
        if not selection:
            return
            
        item_name = self.watchlist_listbox.get(selection[0])
        self.item_manager.remove_from_watchlist(item_name)
        self.refresh_watchlist_ui()

    def perform_search(self, event=None):
        query = self.search_var.get()
        if not query: return
        
        name, iid, suggestions = self.item_manager.search_item(query)
        
        self.results_listbox.delete(0, tk.END)
        self.current_search_results = []
        
        found_any = False
        
        if name and iid:
            display = f"{name} (Best Match)"
            self.results_listbox.insert(tk.END, display)
            self.current_search_results.append((name, iid))
            found_any = True
            
        if suggestions:
            for s_name in suggestions:
                s_id = self.item_manager.name_to_id.get(s_name.lower())
                if s_id:
                    self.results_listbox.insert(tk.END, s_name)
                    self.current_search_results.append((s_name, s_id))
                    found_any = True
        
        if not found_any:
            self.results_listbox.insert(tk.END, "No results found.")

    def add_selected(self):
        selection = self.results_listbox.curselection()
        if not selection:
            return
            
        index = selection[0]
        if index < len(self.current_search_results):
            name, iid = self.current_search_results[index]
            self.item_manager.add_to_watchlist(name, iid)
            self.refresh_watchlist_ui()
            messagebox.showinfo("Success", f"Added {name} to watchlist.")
        else:
            pass

def start_settings():
    root = tk.Tk()
    try:
        from AppKit import NSApplication
        NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
    except:
        pass
    app = SettingsGUI(root)
    root.mainloop()