from textual.app import App
from tui.screens import MainScreen

class FileCommanderApp(App):
    CSS_PATH = "styles.css"
    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def on_mount(self) -> None:
        self.push_screen(MainScreen())
