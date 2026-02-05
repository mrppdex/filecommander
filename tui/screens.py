from textual.screen import Screen
from textual.containers import Container
from textual.widgets import Header, Footer
from tui.widgets import FilePane
import os
import subprocess
from tui.modals import ConfirmationModal
from utils.filesystem import is_ncdu_available, copy_item, move_item, delete_item
from tui.effects import MatrixScreen
from tui.preview import FilePreview
from tui.modals import ConfirmationModal
from tui.input import InputModal
from typing import Optional
from tui.git import GitScreen

class MainScreen(Screen):
    BINDINGS = [
        ("tab", "switch_pane", "Switch Pane"),
        ("s", "open_ncdu", "Open NCDU"),
        ("f5", "copy", "Copy"),
        ("f6", "move", "Move"),
        ("f3", "view", "View"),
        ("delete", "delete", "Delete"),
        ("ctrl+e", "matrix", "Matrix"),
        ("ctrl+f", "filter", "Filter"),
        ("ctrl+o", "sort", "Sort"),
        ("ctrl+g", "goto", "Go to"),
        ("ctrl+v", "open_git", "Git"),
    ]

    def action_view(self):
        active = self.get_active_pane()
        item = active.get_selected_file()
        if item and os.path.isfile(item):
            self.app.push_screen(FilePreview(item))
        elif item:
            self.notify("Selected item is not a file", severity="warning")
        else:
            self.notify("No item selected", severity="warning")

    def action_matrix(self):
        self.app.push_screen(MatrixScreen())
        
    def action_filter(self):
        def set_filter(pattern: Optional[str]):
            self.get_active_pane().set_filter(pattern)
            
        self.app.push_screen(InputModal("Filter by regex (empty to clear):", placeholder="e.g. ^test.*\\.py$"), set_filter)

    def action_sort(self):
        pane = self.get_active_pane()
        pane.cycle_sort()
        self.notify(f"Sorting by: {pane.sort_mode}")

    def action_goto(self):
        pane = self.get_active_pane()
        current = pane.current_path
        
        def change_path(path: Optional[str]):
            if not path:
                return
            
            target = os.path.expanduser(path)
            if os.path.isdir(target):
                self.get_active_pane().change_dir(target)
            else:
                self.notify(f"Invalid directory: {path}", severity="error")

        self.app.push_screen(InputModal("Go to path:", initial_value=current, placeholder="/path/to/dir"), change_path)


    def action_open_git(self):
        pane = self.get_active_pane()
        self.app.push_screen(GitScreen(pane.current_path))

    def compose(self):
        yield Header()
        with Container(id="panes"):
            yield FilePane(id="left-pane")
            yield FilePane(id="right-pane")
        yield Footer()

    def on_mount(self):
        self.query_one("#left-pane").query_one("DataTable").focus()

    def get_active_pane(self):
        start = self.query_one("#left-pane")
        if start.query_one("DataTable").has_focus:
            return start
        return self.query_one("#right-pane")

    def get_inactive_pane(self):
        start = self.query_one("#left-pane")
        if start.query_one("DataTable").has_focus:
            return self.query_one("#right-pane")
        return self.query_one("#left-pane")

    def action_switch_pane(self):
        left = self.query_one("#left-pane").query_one("DataTable")
        right = self.query_one("#right-pane").query_one("DataTable")
        
        if left.has_focus:
            right.focus()
        else:
            left.focus()
            
    def action_copy(self):
        active = self.get_active_pane()
        target = self.get_inactive_pane()
        item = active.get_selected_file()
        
        if not item:
            self.notify("No item selected", severity="warning")
            return

        def check_copy(do_copy: bool):
            if do_copy:
                copy_item(item, target.current_path)
                target.refresh_files()
                self.notify(f"Copied {os.path.basename(item)}")

        self.app.push_screen(ConfirmationModal(f"Copy {os.path.basename(item)}?"), check_copy)

    def action_move(self):
        active = self.get_active_pane()
        target = self.get_inactive_pane()
        item = active.get_selected_file()
        
        if not item:
            self.notify("No item selected", severity="warning")
            return

        def check_move(do_move: bool):
            if do_move:
                move_item(item, target.current_path)
                active.refresh_files()
                target.refresh_files()
                self.notify(f"Moved {os.path.basename(item)}")

        self.app.push_screen(ConfirmationModal(f"Move {os.path.basename(item)}?"), check_move)

    def action_delete(self):
        active = self.get_active_pane()
        item = active.get_selected_file()
        
        if not item:
            self.notify("No item selected", severity="warning")
            return

        def check_delete(do_delete: bool):
            if do_delete:
                delete_item(item)
                active.refresh_files()
                self.notify(f"Deleted {os.path.basename(item)}")

        self.app.push_screen(ConfirmationModal(f"Delete {os.path.basename(item)}?"), check_delete)

    def action_open_ncdu(self):
        if not is_ncdu_available():
            self.notify("ncdu is not installed", severity="error")
            return

        pane = self.get_active_pane()
        current_path = pane.current_path
        
        def run_ncdu():
            subprocess.run(["ncdu", current_path])

        with self.app.suspend():
            run_ncdu()
        
        pane.refresh_files()
