from textual.screen import Screen
from textual.containers import Container
from textual.widgets import Header, Footer, Button
from tui.widgets import FilePane, Toolbar, CommanderTable
import os
import subprocess
from tui.modals import ConfirmationModal, DeleteOptionsModal, MenuModal
from utils.filesystem import copy_item, move_item, delete_item, archive_item
from tui.effects import MatrixScreen
from tui.preview import FilePreview
from tui.modals import ConfirmationModal
from tui.input import InputModal
from typing import Optional
from tui.git import GitScreen

class MainScreen(Screen):
    def on_file_pane_file_clicked(self, event: FilePane.FileClicked):
        self.app.push_screen(FilePreview(event.path))

    BINDINGS = [
        ("tab", "switch_pane", "Switch Pane"),
        ("f5", "copy", "Copy"),
        ("f6", "move", "Move"),
        ("f3", "view", "View"),
        ("ctrl+f", "filter", "Filter"),
        ("ctrl+o", "sort", "Sort"),
        ("ctrl+g", "goto", "Go to"),
        
        # Hidden bindings (accessible via menus/keys but not in footer)
        # Hidden bindings (accessible via menus/keys but not in footer)
        ("delete", "delete", None),
        ("ctrl+e", "matrix", None),
        ("ctrl+v", "open_git", None),
        ("f7", "new_folder", None),
        ("ctrl+n", "new_file", None),
    ]

    def on_button_pressed(self, event: Button.Pressed):
        item_id = event.button.id
        if item_id == "btn-file-menu":
            self.open_file_menu()
        elif item_id == "btn-dir-menu":
            self.open_dir_menu()
        elif item_id == "btn-git-menu":
            self.open_git_menu()
            
    def open_file_menu(self):
        items = [
            ("New File (^N)", "new_file"),
            ("View (F3)", "view"),
            ("Sort (^O)", "sort"),
            ("Filter (^F)", "filter"),
            ("Matrix (^E)", "matrix"),
            ("Delete (Del)", "delete"),
            ("Quit (q)", "quit")
        ]
        def handle_menu(action: Optional[str]):
            if action == "new_file": self.action_new_file()
            elif action == "view": self.action_view()
            elif action == "sort": self.action_sort()
            elif action == "filter": self.action_filter()
            elif action == "matrix": self.action_matrix()
            elif action == "delete": self.action_delete()
            elif action == "quit": self.app.exit()
            
        self.app.push_screen(MenuModal("File Operations", items), handle_menu)

    def open_dir_menu(self):
        items = [
            ("New Folder (F7)", "new_folder"),
            ("Go to (^G)", "goto"),
            ("Copy (F5)", "copy"),
            ("Move (F6)", "move")
        ]
        def handle_menu(action: Optional[str]):
            if action == "new_folder": self.action_new_folder()
            elif action == "goto": self.action_goto()
            elif action == "copy": self.action_copy()
            elif action == "move": self.action_move()

        self.app.push_screen(MenuModal("Directory Operations", items), handle_menu)

    def open_git_menu(self):
        items = [
            ("Git Interface (^V)", "open_git")
        ]
        def handle_menu(action: Optional[str]):
            if action == "open_git": self.action_open_git()
            
        self.app.push_screen(MenuModal("Git Operations", items), handle_menu)

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
        yield Toolbar()
        with Container(id="panes"):
            yield FilePane(id="left-pane")
            yield FilePane(id="right-pane")
        yield Footer()

    def on_mount(self):
        self.last_active_pane = "left-pane"
        self.query_one("#left-pane").query_one(CommanderTable).focus()
        
    def on_descendant_focus(self, event):
        if self.query_one("#left-pane").has_focus_within:
            self.last_active_pane = "left-pane"
        elif self.query_one("#right-pane").has_focus_within:
            self.last_active_pane = "right-pane"

    def get_active_pane(self):
        if hasattr(self, "last_active_pane") and self.last_active_pane == "right-pane":
            return self.query_one("#right-pane")
        return self.query_one("#left-pane")

    def get_inactive_pane(self):
        if hasattr(self, "last_active_pane") and self.last_active_pane == "right-pane":
            return self.query_one("#left-pane")
        return self.query_one("#right-pane")

    def action_switch_pane(self):
        left = self.query_one("#left-pane").query_one(CommanderTable)
        right = self.query_one("#right-pane").query_one(CommanderTable)
        
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

        def check_delete(result: Optional[str]):
            if result == "delete":
                delete_item(item)
                active.refresh_files()
                self.notify(f"Deleted {os.path.basename(item)}")
            elif result == "archive":
                archive_item(item)
                active.refresh_files()
                self.notify(f"Archived {os.path.basename(item)}")

        self.app.push_screen(DeleteOptionsModal(f"Delete or Archive {os.path.basename(item)}?"), check_delete)

    def action_new_folder(self):
        def create_folder(name: Optional[str]):
            if not name:
                return
            path = os.path.join(self.get_active_pane().current_path, name)
            try:
                os.makedirs(path, exist_ok=False)
                self.get_active_pane().refresh_files()
                self.notify(f"Created folder {name}")
            except OSError as e:
                self.notify(f"Error creating folder: {e}", severity="error")

        self.app.push_screen(InputModal("New Folder Name:", placeholder="folder_name"), create_folder)

    def action_new_file(self):
        def create_file(name: Optional[str]):
            if not name:
                return
            path = os.path.join(self.get_active_pane().current_path, name)
            try:
                with open(path, 'x') as f:
                    pass
                self.get_active_pane().refresh_files()
                self.notify(f"Created file {name}")
            except OSError as e:
                self.notify(f"Error creating file: {e}", severity="error")

        self.app.push_screen(InputModal("New File Name:", placeholder="file.txt"), create_file)


