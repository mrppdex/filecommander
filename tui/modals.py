from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Label, Button
from textual.containers import Grid, Vertical
from typing import Optional

class ConfirmationModal(ModalScreen[bool]):
    """A modal screen for confirmation."""

    CSS = """
    ConfirmationModal, DeleteOptionsModal {
        align: center middle;
    }

    #dialog {
        grid-size: 2;
        grid-gutter: 1 2;
        grid-rows: 1fr 3;
        padding: 0 1;
        width: 60;
        height: 11;
        border: thick $background 80%;
        background: $surface;
    }

    #question {
        column-span: 2;
        height: 1fr;
        width: 1fr;
        content-align: center middle;
    }

    Button {
        width: 100%;
    }
    """

    BINDINGS = [("escape", "dismiss", "Cancel")]

    def action_dismiss(self):
        self.dismiss(False)

    def __init__(self, message: str, name: Optional[str] = None, id: Optional[str] = None, classes: Optional[str] = None):
        super().__init__(name, id, classes)
        self.message = message

    def compose(self) -> ComposeResult:
        with Grid(id="dialog"):
            yield Label(self.message, id="question")
            yield Button("Yes", variant="primary", id="yes")
            yield Button("No", variant="error", id="no")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yes":
            self.dismiss(True)
        else:
            self.dismiss(False)


class DeleteOptionsModal(ModalScreen[str]):
    """A modal screen for delete options (Archive, Delete, Cancel)."""

    CSS = """
    DeleteOptionsModal #dialog {
        grid-size: 3;
        grid-gutter: 1 2;
        grid-rows: 1fr 3;
        width: 70;
    }
    DeleteOptionsModal #question {
        column-span: 3;
    }
    """

    BINDINGS = [("escape", "dismiss", "Cancel")]

    def action_dismiss(self):
        self.dismiss("cancel")

    def __init__(self, message: str, name: Optional[str] = None, id: Optional[str] = None, classes: Optional[str] = None):
        super().__init__(name, id, classes)
        self.message = message

    def compose(self) -> ComposeResult:
        with Grid(id="dialog"):
            yield Label(self.message, id="question")
            yield Button("Archive", variant="primary", id="archive")
            yield Button("Delete", variant="error", id="delete")
            yield Button("Cancel", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id)

class MenuModal(ModalScreen[str]):
    """A modal screen for displaying a menu of actions."""

    CSS = """
    MenuModal {
        align: center middle;
    }

    #menu-container {
        width: 40;
        height: auto;
        border: thick $background 80%;
        background: $surface;
        padding: 1;
    }

    MenuModal Button {
        width: 100%;
        margin-bottom: 1;
    }
    """

    BINDINGS = [("escape", "dismiss", "Cancel")]

    def action_dismiss(self):
        self.dismiss(None)

    def __init__(self, title: str, items: list[tuple[str, str]], name: Optional[str] = None, id: Optional[str] = None, classes: Optional[str] = None):
        super().__init__(name, id, classes)
        self.title_text = title
        self.items = items

    def compose(self) -> ComposeResult:
        with Vertical(id="menu-container"):
            yield Label(self.title_text)
            for label, action_id in self.items:
                yield Button(label, id=action_id)
            yield Button("Cancel", id="cancel", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss(None)
        else:
            self.dismiss(event.button.id)
