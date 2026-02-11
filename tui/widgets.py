import os
from textual import events, on
from textual.coordinate import Coordinate
from textual.widgets import Static, DataTable, Button
from textual.containers import Vertical, Horizontal
from textual.message import Message
from utils.filesystem import list_directory
from typing import Optional

class CommanderTable(DataTable):
    @on(events.Click)
    def on_click(self, event: events.Click) -> None:
        if event.button == 1:
            try:
                # Attempt to get the row under the mouse
                coordinate = self.hover_coordinate
                if coordinate:
                    cell_key = self.coordinate_to_cell_key(coordinate)
                    self.post_message(DataTable.RowSelected(self, cell_key.row_key))
            except Exception:
                pass

    BINDINGS = [
        ("space", "toggle_select", "Select"),
    ]

    def action_toggle_select(self):
        try:
            row_key = self.coordinate_to_cell_key(self.cursor_coordinate).row_key
            self.post_message(self.FileSelectionEvent(row_key, ctrl=True, shift=False))
            self.action_cursor_down()
        except Exception:
            pass

    class FileSelectionEvent(Message):
        def __init__(self, row_key, ctrl: bool, shift: bool):
            self.row_key = row_key
            self.ctrl = ctrl
            self.shift = shift
            super().__init__()

class Toolbar(Horizontal):
    def on_mount(self):
        self.styles.height = 3
        self.styles.width = "100%"
        self.styles.background = "#222222"
        self.styles.border = None
        self.styles.padding = 0
        self.styles.margin = 0
        
        for button in self.query("Button"):
            button.styles.height = "100%"
            button.styles.width = "auto"
            button.styles.min_width = 16
            button.styles.border = None
            button.styles.margin = (0, 1, 0, 0)
            button.styles.padding = (0, 1)
            button.styles.background = "#444444"
            button.styles.color = "#ffffff"
            button.styles.content_align = ("center", "middle")

    def compose(self):
        yield Button("File", id="btn-file-menu")
        yield Button("Directory", id="btn-dir-menu")
        yield Button("Git", id="btn-git-menu")

class FilePane(Vertical):
    def on_mount(self):
        self.styles.width = "1fr"
        self.styles.height = "100%"
        self.styles.border = ("solid", "green")
        self.styles.padding = 1
        
        table = self.query_one(CommanderTable)
        table.cursor_type = "row"
        table.add_columns("Name", "Size", "Date")
        self.refresh_files()
    class FileClicked(Message):
        def __init__(self, path: str):
            self.path = path
            super().__init__()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_path = os.getcwd()
        self.sort_mode = "name" # name, size, date
        self.sort_ascending = True
        self.filter_pattern = None
        self.files_selected: set[str] = set()
        self.last_selected_key: Optional[str] = None

    def get_selected_files(self) -> list[str]:
        if self.files_selected:
            return list(self.files_selected)
        
        # If no explicit selection, return the current cursor item
        single = self.get_selected_file()
        if single:
            return [single]
        return []

    def get_selected_file(self):
        try:
            table = self.query_one(CommanderTable)
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
            if row_key.value == "..":
                return None
            return os.path.join(self.current_path, row_key.value)
        except Exception:
            return None

    def compose(self):
        yield Static(self.current_path, id="path-display")
        yield CommanderTable(id="file-table")

    # on_mount moved up


    def refresh_files(self):
        table = self.query_one(CommanderTable)
        
        # Save cursor position (key)
        cursor_row_key_value = None
        try:
            if table.row_count > 0:
                cursor_row_key_value = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value
        except Exception:
            pass

        table.clear()
        files = list_directory(self.current_path, self.sort_by, self.filter_pattern, self.sort_ascending)
        
        # Prune selections that are no longer valid (e.g. deleted/moved files)
        current_filenames = {os.path.join(self.current_path, f["name"]) for f in files if f["name"] != ".."}
        self.files_selected = {f for f in self.files_selected if f in current_filenames}

        for f in files:
            # key is the full path or special ".."
            key = os.path.join(self.current_path, f["name"]) if f["name"] != ".." else os.path.dirname(self.current_path)
            table.add_row(f["name"], f["size"], f["date"], key=key)
            
            if key in self.files_selected:
                index = table.get_row_index(key)
                if index is not None:
                    # Apply selection style
                    for col in range(len(table.columns)):
                        coord = Coordinate(index, col)
                        table.update_cell_at(coord, f"[reverse]{table.get_cell_at(coord)}[/reverse]")
        
        # Update path display with status
        status = f"{self.current_path}"
        if self.filter_pattern:
             status += f" [Filter: {self.filter_pattern}]"
        order = "Asc" if self.sort_ascending else "Desc"
        status += f" [Sort: {self.sort_mode} {order}]"
        self.query_one("#path-display", Static).update(status)
        
        # Restore cursor
        if cursor_row_key_value:
            try:
                # Find index of the key
                index = table.get_row_index(cursor_row_key_value)
                if index is not None:
                     table.cursor_coordinate = Coordinate(index, 0)
            except Exception:
                pass

    @property
    def sort_by(self):
        return self.sort_mode
        
    def set_filter(self, pattern: Optional[str]):
        self.filter_pattern = pattern
        self.refresh_files()

    def cycle_sort(self):
        # Cycle: Name Asc -> Name Desc -> Size Asc -> Size Desc -> Date Asc -> Date Desc
        if self.sort_ascending:
            self.sort_ascending = False
        else:
            self.sort_ascending = True
            modes = ["name", "size", "date"]
            try:
                curr = modes.index(self.sort_mode)
                self.sort_mode = modes[(curr + 1) % len(modes)]
            except ValueError:
                self.sort_mode = "name"
        self.refresh_files()

    @on(DataTable.RowSelected)
    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        # Clear selection on normal activation (click/enter) unless modified handled elsewhere
        # (Modifiers are handled in on_click and don't trigger this usually, 
        # but if they did, we might check. But here we assume this is "Single Select/Activate")
        self.files_selected.clear()
        self.refresh_files() # Refresh to remove styling from previously selected

        # row_key is what we passed as key to add_row (the name)
        selected_name = event.row_key.value
        if selected_name == "..":
            self.change_dir(os.path.dirname(self.current_path))
        else:
            path = os.path.join(self.current_path, selected_name)
            if os.path.isdir(path):
                self.change_dir(path)
            # Try removing trailing slash if present (list_directory adds it)
            elif selected_name.endswith("/") and os.path.isdir(os.path.join(self.current_path, selected_name.rstrip("/"))):
                self.change_dir(os.path.join(self.current_path, selected_name.rstrip("/")))
            else:
                self.post_message(self.FileClicked(path))

    @on(CommanderTable.FileSelectionEvent)
    def on_file_selection(self, event: CommanderTable.FileSelectionEvent):
        key = event.row_key.value
        if key == "..":
            return
            
        full_path = key # Key is already full path now
        
        if event.shift and self.last_selected_key:
            # Range selection
            self.select_range(self.last_selected_key, full_path)
        elif event.ctrl:
            # Toggle selection
            self.toggle_selection(full_path)
            self.last_selected_key = full_path
        
        # Refresh to show selection styles
        self.refresh_files()

    def toggle_selection(self, key: str):
        if key in self.files_selected:
            self.files_selected.remove(key)
        else:
            self.files_selected.add(key)

    def select_range(self, start_key: str, end_key: str):
        table = self.query_one(CommanderTable)
        try:
            start_idx = table.get_row_index(start_key)
            end_idx = table.get_row_index(end_key)
            
            if start_idx is None or end_idx is None:
                return
                
            low = min(start_idx, end_idx)
            high = max(start_idx, end_idx)
            
            # Select everything in between
            # We need to iterate over rows in the table
            # There isn't a direct way to get row key by index easily in older Textual versions,
            # but we can iterate. Or we can just rebuild the set.
            # Assuming we want to ADD to selection
            
            # We can get row keys by iterating table rows?
            # Actually table.rows returns mapping.
            
            # Let's iterate linearly for now, inefficient but works for small lists
            # Textual 0.50+ has `get_row_at`? No.
            # We can use `coordinate_to_cell_key`
            
            for i in range(low, high + 1):
                # We need the key at this index.
                # `get_row_at` might return data, not key.
                # Check textual docs or source... `get_row_at(index)` returns Row object which has `key`.
                # Assuming modern Textual
                # row = table.get_row_at(i) # This might not exist.
                # Alternative: iterate all rows and check index.
                pass 
                
            # Better way:
            # We want to select the range.
            # Since we iterate all files in refresh_files, we can't easily get them by index here without access to that list.
            # But the table has them.
            
            # Implementation detail:
            # We need a way to map index -> key
             # Let's just create a list of keys from the table
            keys = [row.key.value for row in table.ordered_rows]
            
            for i in range(low, high + 1):
                if i < len(keys):
                    self.files_selected.add(keys[i])

        except Exception:
            pass

    def change_dir(self, new_paths):
        try:
             # Normalize path
            target = os.path.normpath(new_paths)
            if os.path.isdir(target):
                self.current_path = target
                self.files_selected.clear()
                self.refresh_files()
                self.query_one(CommanderTable).focus()
        except OSError:
            pass
