from textual.screen import ModalScreen
from textual.widgets import Input, Label
from textual.containers import Grid, Vertical

class InputModal(ModalScreen[str]):
    CSS = """
    InputModal {
        align: center middle;
    }

    #dialog {
        width: 60;
        height: auto;
        border: thick $background 80%;
        background: $surface;
        padding: 1 2;
    }
    
    Label {
        margin-bottom: 1;
        width: 100%;
        text-align: center;
    }
    """

    def __init__(self, prompt: str, placeholder: str = "", initial_value: str = ""):
        super().__init__()
        self.prompt = prompt
        self.placeholder = placeholder
        self.initial_value = initial_value

    def compose(self):
        with Vertical(id="dialog"):
            yield Label(self.prompt)
            yield Input(placeholder=self.placeholder, value=self.initial_value)

    def on_input_submitted(self, event: Input.Submitted):
        self.dismiss(event.value)
