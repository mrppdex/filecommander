import os
import json
from textual.screen import ModalScreen
from textual.widgets import Label, Button, Static
from textual.containers import Grid, VerticalScroll
from rich.syntax import Syntax
from rich.text import Text

class FilePreview(ModalScreen):
    CSS = """
    FilePreview {
        align: center middle;
    }

    #dialog {
        width: 90%;
        height: 80%;
        border: thick $background 80%;
        background: $surface;
        layout: vertical;
    }

    #title {
        dock: top;
        width: 100%;
        background: $primary;
        color: $text;
        padding: 0 1;
    }

    #content {
        width: 100%;
        height: auto;
    }

    #footer {
        dock: bottom;
        width: 100%;
        height: 3;
        align: right middle;
        padding: 0 1;
    }
    
    Button {
        width: 16;
    }
    """
    
    BINDINGS = [("escape", "close", "Close")]

    def __init__(self, path: str):
        super().__init__()
        self.path = path

    def compose(self):
        with VerticalScroll(id="dialog"):
            yield Label(f"Preview: {os.path.basename(self.path)}", id="title")
            yield Static(id="content", expand=True)
            yield Button("Close", id="close", variant="primary")

    def on_mount(self):
        self.load_content()

    def load_content(self):
        content_widget = self.query_one("#content", Static)
        
        try:
            # Check for binary first
            if self.is_binary(self.path):
                content_widget.update(self.get_hex_dump(self.path))
            else:
                with open(self.path, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                # Try JSON
                if self.path.endswith(".json"):
                    try:
                        parsed = json.loads(content)
                        content = json.dumps(parsed, indent=2)
                        content_widget.update(Syntax(content, "json", theme="monokai"))
                        return
                    except json.JSONDecodeError:
                        pass # Fallback to normal text
                
                # Syntax highlighting
                lexer = Syntax.guess_lexer(self.path, code=content)
                if lexer:
                     content_widget.update(Syntax(content, lexer, theme="monokai"))
                else:
                     content_widget.update(content)

        except Exception as e:
            content_widget.update(f"Error reading file: {e}")

    def is_binary(self, path):
        try:
            with open(path, "rb") as f:
                chunk = f.read(1024)
                if b"\0" in chunk:
                    return True
                # Use text decoding check as secondary
                try:
                    chunk.decode("utf-8")
                except UnicodeDecodeError:
                    return True
        except:
             return False
        return False

    def get_hex_dump(self, path):
        lines = []
        try:
            with open(path, "rb") as f:
                offset = 0
                while True:
                    chunk = f.read(16)
                    if not chunk:
                        break
                    
                    hex_vals = " ".join(f"{b:02x}" for b in chunk)
                    ascii_vals = "".join((chr(b) if 32 <= b < 127 else ".") for b in chunk)
                    
                    # Pad hex if short chunk
                    if len(chunk) < 16:
                        hex_vals += "   " * (16 - len(chunk))
                    
                    lines.append(f"{offset:08x}  {hex_vals}  |{ascii_vals}|")
                    offset += 16
                    
                    if offset > 16 * 1024: # Limit preview size
                        lines.append("... (truncated) ...")
                        break
        except Exception as e:
            return f"Error reading binary: {e}"
            
        return Text("\n".join(lines), style="bold white on black")

    def on_button_pressed(self, event):
        if event.button.id == "close":
            self.dismiss()
            
    def action_close(self):
        self.dismiss()
