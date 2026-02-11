import os
from textual import events, on
from textual.widgets import Static, DataTable, Button
from textual.containers import Vertical, Horizontal
from textual.message import Message
from utils.filesystem import list_directory
from typing import Optional

class CommanderTable(DataTable):
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
        table.clear()
        files = list_directory(self.current_path, self.sort_by, self.filter_pattern, self.sort_ascending)
        for f in files:
            # key is the full path or special ".."
            key = os.path.join(self.current_path, f["name"]) if f["name"] != ".." else os.path.dirname(self.current_path)
            table.add_row(f["name"], f["size"], f["date"], key=f["name"])
        
        # Update path display with status
        status = f"{self.current_path}"
        if self.filter_pattern:
             status += f" [Filter: {self.filter_pattern}]"
        order = "Asc" if self.sort_ascending else "Desc"
        status += f" [Sort: {self.sort_mode} {order}]"
        self.query_one("#path-display", Static).update(status)

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

    def change_dir(self, new_paths):
        try:
             # Normalize path
            target = os.path.normpath(new_paths)
            if os.path.isdir(target):
                self.current_path = target
                self.refresh_files()
                self.query_one(CommanderTable).focus()
        except OSError:
            pass
