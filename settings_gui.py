import tkinter as tk
from tkinter import ttk, messagebox
from item_manager import ItemManager

class DragDropListbox(tk.Listbox):
    """A Listbox that supports drag-and-drop reordering."""
    def __init__(self, master, **kw):
        if 'selectmode' not in kw:
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
    def __init__(self, root, queue=None):
        self.root = root
        self.queue = queue
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
        self.watchlist_listbox = DragDropListbox(left_frame, selectmode=tk.EXTENDED)
        self.watchlist_listbox.pack(fill=tk.BOTH, expand=True, padx=5)
        self.watchlist_listbox.on_reorder_callback = self.save_reorder
        self.watchlist_listbox.bind('<BackSpace>', self.remove_selected)
        
        btn_add_section = ttk.Button(left_frame, text="Add Section Divider", command=self.add_section_dialog)
        btn_add_section.pack(pady=(5, 0))
        
        btn_rename_section = ttk.Button(left_frame, text="Rename Section", command=self.rename_section_dialog)
        btn_rename_section.pack(pady=(5, 0))
        
        # Profit Config Buttons
        profit_frame = ttk.Frame(left_frame)
        profit_frame.pack(pady=(5, 0))
        
        ttk.Button(profit_frame, text="Set Inputs", command=self.set_selection_as_inputs).pack(side=tk.LEFT, padx=2)
        ttk.Button(profit_frame, text="Set Outputs", command=self.set_selection_as_outputs).pack(side=tk.LEFT, padx=2)
        
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
        self.results_listbox = tk.Listbox(right_frame, selectmode=tk.EXTENDED)
        self.results_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.results_listbox.bind('<Return>', self.add_selected)
        
        btn_add = ttk.Button(right_frame, text="Add Selected to Watchlist", command=self.add_selected)
        btn_add.pack(pady=5)
        
        # Initialize
        self.refresh_watchlist_ui()
        self.current_search_results = []

    def refresh_watchlist_ui(self):
        """Reloads the watchlist listbox from item_manager."""
        self.watchlist_listbox.delete(0, tk.END)
        # Iterate specifically over List[Dict]
        for i, entry in enumerate(self.item_manager.watchlist):
            if entry.get('type') == 'section':
                label = f"--- {entry.get('label', 'Section').upper()} ---"
                # Add indicator if profit is configured
                if entry.get('profit_stats'):
                    label += " [$]"
                self.watchlist_listbox.insert(tk.END, label)
                self.watchlist_listbox.itemconfig(i, {'fg': 'blue'})
            else:
                self.watchlist_listbox.insert(tk.END, entry.get('name', '???'))

    def save_reorder(self):
        """Called when listbox is reordered by user."""
        # Reconstruct the watchlist list based on new order
        # We need to map the visible text back to the original objects
        # This is tricky because names might be duplicated or similar to sections.
        # Strategy: We assume the user didn't rename items dynamically.
        # We can try to match by name, but if we have dupes, order matters.
        # But wait - we are dragging strings. We need to know which object was which.
        # To simplify: We can rebuild by matching against the CURRENT pool of items.
        
        # A safer way relies on the index if we tracked it, but standard Listbox doesn't link objects.
        # Let's map "Display String" -> "List of Candidate Objects"
        
        pool = list(self.item_manager.watchlist) # Shallow copy
        new_watchlist = []
        
        current_names = self.watchlist_listbox.get(0, tk.END)
        
        for display_name in current_names:
            # Find matching entry in pool
            found_idx = -1
            for i, entry in enumerate(pool):
                # Check for Section match
                if entry.get('type') == 'section':
                    base_label = f"--- {entry.get('label', '').upper()} ---"
                    # Match against base label OR label with profit indicator
                    if display_name == base_label or display_name == (base_label + " [$]"):
                        found_idx = i
                        break
                # Check for Item match
                elif entry.get('type') == 'item':
                    if display_name == entry.get('name'):
                        found_idx = i
                        break
            
            if found_idx != -1:
                new_watchlist.append(pool.pop(found_idx))
            else:
                print(f"Warning: Could not match UI item '{display_name}' to data object")

        if new_watchlist:
            self.item_manager.watchlist = new_watchlist
            self.item_manager.save_config()
            self.notify_update()

    def add_section_dialog(self):
        from tkinter import simpledialog
        label = simpledialog.askstring("New Section", "Enter section name:", parent=self.root)
        if label:
            self.item_manager.add_section(label)
            self.refresh_watchlist_ui()
            self.notify_update()

    def rename_section_dialog(self):
        """Rename the selected section."""
        selection = self.watchlist_listbox.curselection()
        if not selection:
            messagebox.showinfo("Select Section", "Please select a section to rename.")
            return

        idx = selection[0]
        if idx >= len(self.item_manager.watchlist): return

        entry = self.item_manager.watchlist[idx]
        if entry.get('type') != 'section':
            messagebox.showinfo("Not a Section", "Please select a section divider.")
            return
            
        old_label = entry.get('label')
        from tkinter import simpledialog
        new_label = simpledialog.askstring("Rename Section", "Enter new section name:", initialvalue=old_label, parent=self.root)
        
        if new_label and new_label != old_label:
            self.item_manager.rename_section(old_label, new_label)
            self.refresh_watchlist_ui()
            self.notify_update()

    def get_parent_section_for_items(self, indices):
        """Find the common section above the selected items."""
        # We need to map UI indices to watchlist indices (1:1)
        # We assume the user selected items. We walk UP from the first item to find a section.
        # But wait - if they selected items from multiple sections, which one?
        # Logic: Use the LAST selected item, walk up to find its section.
        # OR: Ensure all items belong to same section.
        # Let's simple: Use the first item's section.
        
        if not indices: return None, []
        
        first_idx = indices[0]
        # Walk backwards from first_idx
        section_label = None
        for i in range(first_idx, -1, -1):
            entry = self.item_manager.watchlist[i]
            if entry.get('type') == 'section':
                section_label = entry.get('label')
                break
        
        if not section_label:
            return None, []

        # Validate entries are items
        item_ids = []
        for i in indices:
            if i >= len(self.item_manager.watchlist): continue
            entry = self.item_manager.watchlist[i]
            if entry.get('type') == 'item':
                item_ids.append(entry.get('id'))
        
        return section_label, item_ids

    def set_selection_as_inputs(self):
        selection = self.watchlist_listbox.curselection()
        if not selection:
            messagebox.showinfo("Select Items", "Please select input items first.")
            return
            
        label, ids = self.get_parent_section_for_items(selection)
        if not label:
            messagebox.showerror("Error", "Could not find a parent section for these items.")
            return
            
        if not ids:
             messagebox.showerror("Error", "Selected entries must be items.")
             return
             
        self.item_manager.set_section_inputs(label, ids)
        self.refresh_watchlist_ui()
        self.notify_update()
        messagebox.showinfo("Success", f"Set {len(ids)} items as INPUTS for '{label}'.")

    def set_selection_as_outputs(self):
        selection = self.watchlist_listbox.curselection()
        if not selection:
            messagebox.showinfo("Select Items", "Please select output items first.")
            return
            
        label, ids = self.get_parent_section_for_items(selection)
        if not label:
            messagebox.showerror("Error", "Could not find a parent section for these items.")
            return
            
        if not ids:
             messagebox.showerror("Error", "Selected entries must be items.")
             return
             
        self.item_manager.set_section_outputs(label, ids)
        self.refresh_watchlist_ui()
        self.notify_update()
        messagebox.showinfo("Success", f"Set {len(ids)} items as OUTPUTS for '{label}'.")

    def notify_update(self):
        """Notify main process that config has changed."""
        if self.queue:
            try:
                self.queue.put("UPDATE")
            except Exception as e:
                print(f"Error sending update: {e}")

    def remove_selected(self, event=None):
        selection = self.watchlist_listbox.curselection()
        if not selection:
            return
            
        items_to_remove = []
        for index in selection:
            item_name = self.watchlist_listbox.get(index)
            items_to_remove.append(item_name)
            
        if items_to_remove:
            # Pass strict list of names/labels
            # We must be careful about distinguishing sections formatted string from raw name
            # Actually remove_items_from_watchlist expects raw names/labels.
            # We need to reverse-map the formatted string.
            
            real_names = []
            # We iterate the CURRENT watchlist to find matches again (similar to save_reorder)
            # Or just use the heuristic: if it starts with ---, extract label.
            
            for d_name in items_to_remove:
                if d_name.startswith("--- ") and d_name.endswith(" ---"):
                    # Section extraction
                    label = d_name[4:-4].lower() # We uppercased it
                    # Find matching section in watchlist matching this roughly
                    # This is brittle. Better to search watchlist for case-insensitive match on label.
                    for entry in self.item_manager.watchlist:
                        if entry.get('type') == 'section' and entry.get('label').upper() == label.upper():
                            real_names.append(entry.get('label'))
                            break
                else:
                    real_names.append(d_name)

            self.item_manager.remove_items_from_watchlist(real_names)
            self.refresh_watchlist_ui()
            self.notify_update()

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

    def add_selected(self, event=None):
        selection = self.results_listbox.curselection()
        if not selection:
            return
            
        items_to_add = []
        for index in selection:
            if index < len(self.current_search_results):
                items_to_add.append(self.current_search_results[index])
        
        if items_to_add:
            self.item_manager.add_items_to_watchlist(items_to_add)
            self.refresh_watchlist_ui()
            self.notify_update()
            
            # Optional: Clear selection or give feedback
            self.results_listbox.selection_clear(0, tk.END)

def start_settings(queue=None):
    root = tk.Tk()
    try:
        from AppKit import NSApplication
        NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
    except:
        pass
    app = SettingsGUI(root, queue)
    root.mainloop()
