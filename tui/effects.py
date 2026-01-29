import random
from textual.screen import Screen
from textual.widgets import Static
from textual.app import ComposeResult
from textual.reactive import reactive
from rich.text import Text

class MatrixRain(Static):
    DEFAULT_CSS = """
    MatrixRain {
        width: 100%;
        height: 100%;
    }
    """
    
    def on_mount(self):
        self.drops = [random.randint(-20, 0) for _ in range(self.size.width)]
        self.set_interval(0.1, self.tick)

    def tick(self):
        width, height = self.size
        
        # Ensure drops match width (handle resize)
        if len(self.drops) != width:
            self.drops = [random.randint(-20, 0) for _ in range(width)]

        lines = []
        for y in range(height):
            line = []
            for x in range(width):
                 # Simple drop logic: if drop is at this y, render char
                 # drop position represents the "head" of the stream
                 head = self.drops[x]
                 if head >= y and head < y + 10: # trail length
                     char = random.choice("0123456789ABCDEF")
                     # simple color ramp? Textual rich text supports it but keeping it simple first
                     line.append(char)
                 else:
                     line.append(" ")
            lines.append("".join(line))
        
        # Move drops down
        for i in range(width):
            self.drops[i] += 1
            if self.drops[i] > height + random.randint(0, 20):
                 self.drops[i] = random.randint(-20, 0)

        text = Text("\n".join(lines), style="bold green on black")
        self.update(text)

class MatrixScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Back")]

    def compose(self) -> ComposeResult:
        yield MatrixRain()
