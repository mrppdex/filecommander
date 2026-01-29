# File Commander

A terminal-based file manager built with Python and Textual, inspired by Norton Commander.

## Features

- **Dual-pane interface**: Classic file management layout.
- **File operations**: Copy, move, delete, and rename files.
- **File preview**: Syntax highlighting for code, robust previews for images (using specialized tools if available), and hex views for binary files.
- **Disk usage analysis**: Integration with `ncdu` (if available).
- **Themes**: Dark/Light mode toggle.

## Prerequisites

- Python 3.8 or higher
- Terminal with true color support (recommended)

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/mrppdex/filecommander.git
   cd filecommander
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   - On legacy Windows cmd:
     ```bash
     venv\Scripts\activate
     ```
   - On Windows PowerShell:
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

To start the application, ensure your virtual environment is activated and run:

```bash
python main.py
```

## Keyboard Shortcuts

- **Tab**: Switch between panes
- **F5**: Copy selected file/directory
- **F6**: Move selected file/directory
- **F8**: Delete selected file/directory
- **F10**: Quit
- **Ctrl+d**: Toggle Dark/Light mode
