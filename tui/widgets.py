import os
from textual.widgets import Static, DataTable
from textual.containers import Vertical
from utils.filesystem import list_directory
from typing import Optional

class FilePane(Vertical):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_path = os.getcwd()
        self.sort_mode = "name" # name, size, date
        self.filter_pattern = None

    def get_selected_file(self):
        try:
            table = self.query_one(DataTable)
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
            if row_key.value == "..":
                return None
            return os.path.join(self.current_path, row_key.value)
        except Exception:
            return None

    def compose(self):
        yield Static(self.current_path, id="path-display")
        yield DataTable(id="file-table")

    def on_mount(self):
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.add_columns("Name", "Size", "Date")
        self.refresh_files()

    def refresh_files(self):
        table = self.query_one(DataTable)
        table.clear()
        files = list_directory(self.current_path, self.sort_by, self.filter_pattern)
        for f in files:
            # key is the full path or special ".."
            key = os.path.join(self.current_path, f["name"]) if f["name"] != ".." else os.path.dirname(self.current_path)
            table.add_row(f["name"], f["size"], f["date"], key=f["name"])
        
        # Update path display with status
        status = f"{self.current_path}"
        if self.filter_pattern:
             status += f" [Filter: {self.filter_pattern}]"
        status += f" [Sort: {self.sort_mode}]"
        self.query_one("#path-display", Static).update(status)

    @property
    def sort_by(self):
        return self.sort_mode
        
    def set_filter(self, pattern: Optional[str]):
        self.filter_pattern = pattern
        self.refresh_files()

    def cycle_sort(self):
        modes = ["name", "size", "date"]
        try:
            curr = modes.index(self.sort_mode)
            self.sort_mode = modes[(curr + 1) % len(modes)]
        except ValueError:
            self.sort_mode = "name"
        self.refresh_files()

    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        # row_key is what we passed as key to add_row (the name)
        selected_name = event.row_key.value
        if selected_name == "..":
            self.change_dir(os.path.dirname(self.current_path))
        else:
            path = os.path.join(self.current_path, selected_name)
            if os.path.isdir(path):
                self.change_dir(path)
            else:
                from utils.filesystem import open_file_with_default_app
                open_file_with_default_app(path)

    def change_dir(self, new_paths):
        try:
             # Normalize path
            target = os.path.normpath(new_paths)
            if os.path.isdir(target):
                self.current_path = target
                self.refresh_files()
                self.query_one(DataTable).focus()
        except OSError:
            pass
