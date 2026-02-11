from textual.screen import Screen, ModalScreen
from textual.app import ComposeResult
from textual.widgets import Header, Footer, Static, DataTable, Button, Label, Input
from textual.containers import Container, Vertical, Horizontal, Grid
from textual.binding import Binding
from textual import on
import git
import os
from tui.modals import ConfirmationModal
from tui.input import InputModal

class GitScreen(Screen):
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back"),
        Binding("f5", "refresh", "Refresh"),
        Binding("i", "init", "Init Rep"),
        Binding("space", "toggle_stage", "Stage/Unstage"),
        Binding("c", "commit", "Commit"),
        Binding("p", "push", "Push"),
        Binding("b", "branch", "Branch"),
    ]

    CSS = """
    #git-status-header {
        height: 3;
        dock: top;
        content-align: center middle;
        background: $primary;
        color: $text;
    }
    
    #git-init-container {
        align: center middle;
        height: 100%;
    }
    
    DataTable {
        height: 1fr;
    }
    
    .staged { color: green; }
    .unstaged { color: red; }
    .untracked { color: yellow; }
    """

    def __init__(self, initial_path: str):
        super().__init__()
        self.path = initial_path
        self.repo = None
        self._load_repo()

    def _load_repo(self):
        try:
            self.repo = git.Repo(self.path, search_parent_directories=True)
        except git.InvalidGitRepositoryError:
            self.repo = None

    def compose(self) -> ComposeResult:
        yield Header()
        if self.repo is None:
             with Container(id="git-init-container"):
                yield Label(f"No git repository found at {self.path}")
                yield Button("Initialize Git Repository", variant="primary", id="init-repo")
        else:
            yield Static(id="git-status-header")
            yield DataTable(id="git-status-table")
        yield Footer()

    def on_mount(self):
        if self.repo:
            self.refresh_status()

    def refresh_status(self):
        if not self.repo:
            return
            
        header = self.query_one("#git-status-header", Static)
        try:
            branch = self.repo.active_branch.name
        except TypeError: # Detached head
            branch = "(detached)"
        
        remotes = ", ".join([r.name for r in self.repo.remotes])
        header.update(f"Repo: {os.path.basename(self.repo.working_dir)} | Branch: {branch} | Remotes: {remotes}")

        table = self.query_one("#git-status-table", DataTable)
        table.clear()
        table.cursor_type = "row"
        table.add_columns("S", "Path", "Status")

        # Get status
        # Staged
        for diff in self.repo.index.diff("HEAD"):
             table.add_row("S", diff.a_path, "Staged (Deleted)" if diff.change_type == "D" else "Staged (Modified)", key=f"staged:{diff.a_path}")
        
        # We need to look at index.diff("HEAD") for staged changes vs HEAD
        # And index.diff(None) for unstaged changes
        
        # Actually proper way:
        # Staged changes
        try:
            staged_files = self.repo.index.diff("HEAD")
            for diff in staged_files:
                table.add_row("✓", diff.a_path, "Staged", key=f"staged:{diff.a_path}")
        except Exception:
            pass # Initial commit maybe?
            
        # Unstaged changes
        unstaged_files = self.repo.index.diff(None)
        for diff in unstaged_files:
            table.add_row(" ", diff.a_path, "Modified", key=f"unstaged:{diff.a_path}")

        # Untracked
        for f in self.repo.untracked_files:
            table.add_row("?", f, "Untracked", key=f"untracked:{f}")

    @on(Button.Pressed, "#init-repo")
    def action_init(self):
        if self.repo:
            return
        
        try:
            self.repo = git.Repo.init(self.path)
            self.app.pop_screen() # pop to refresh structure maybe? or just re-render
            self.app.push_screen(GitScreen(self.path)) # simplistic reload
            self.notify("Initialized Git Repository")
        except Exception as e:
            self.notify(f"Error initializing: {e}", severity="error")

    def action_refresh(self):
        self._load_repo()
        if self.repo:
             # If we transitioned from no-repo to repo, we need to recompose, easiest is to restart screen
             # checking if query_one fails
             try:
                 self.refresh_status()
             except:
                 self.app.push_screen(GitScreen(self.path))
                 self.app.pop_screen() # Close old one

    def action_toggle_stage(self):
        if not self.repo: return
        
        table = self.query_one("#git-status-table", DataTable)
        if not table.row_count: return
        
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
        key_value = row_key.value # e.g. "staged:file.py"
        
        type_, path = key_value.split(":", 1)
        
        try:
            if type_ == "staged":
                self.repo.index.reset(paths=[path]) # Unstage
            else:
                self.repo.index.add([path]) # Stage
            self.refresh_status()
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    def action_commit(self):
        if not self.repo: return
        
        def do_commit(msg: str):
            if msg:
                try:
                    self.repo.index.commit(msg)
                    self.notify("Committed successfully")
                    self.refresh_status()
                except Exception as e:
                    self.notify(f"Commit failed: {e}", severity="error")
        
        self.app.push_screen(InputModal("Commit message:"), do_commit)

    def action_push(self):
        if not self.repo: return
        
        def confirmed(push: bool):
            if push:
                try:
                    # Defaulting to origin main/master or current
                    origin = self.repo.remote(name='origin')
                    info = origin.push()
                    # Check info for errors?
                    self.notify("Push command sent")
                except ValueError:
                    self.notify("No remote 'origin' found", severity="error")
                except Exception as e:
                    self.notify(f"Push error: {e}", severity="error")
                    
        self.app.push_screen(ConfirmationModal("Push to origin?"), confirmed)

    def action_branch(self):
        if not self.repo: return
        
        # Show functionality to create branch or checkout?
        # For simplicity: Input to create/checkout
        
        def handle_branch(name: str):
            if not name: return
            
            # Check if exists
            if name in self.repo.heads:
                self.repo.heads[name].checkout()
                self.notify(f"Switched to {name}")
            else:
                # Create and checkout
                try:
                    new_branch = self.repo.create_head(name)
                    new_branch.checkout()
                    self.notify(f"Created and switched to {name}")
                except Exception as e:
                     self.notify(f"Error: {e}", severity="error")
            self.refresh_status()
            
        self.app.push_screen(InputModal("Branch name (switch or create):"), handle_branch)
