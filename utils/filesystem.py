import os
import datetime
import humanize

import re

def list_directory(path: str, sort_by: str = "name", filter_pattern: str | None = None) -> list[dict]:
    """
    List contents of a directory and return metadata.
    sort_by: "name", "size", "date"
    filter_pattern: Regex pattern to filter filenames (directories are always shown)
    """
    entries = []
    try:
        with os.scandir(path) as it:
            for entry in it:
                try:
                    stat = entry.stat()
                    # Filter check
                    if filter_pattern and not entry.is_dir():
                        if not re.search(filter_pattern, entry.name, re.IGNORECASE):
                            continue
                            
                    entries.append({
                        "name": entry.name + ("/" if entry.is_dir() else ""),
                        "size": humanize.naturalsize(stat.st_size) if not entry.is_dir() else "<DIR>",
                        "date": datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                        "raw_size": stat.st_size,
                        "raw_date": stat.st_mtime,
                        "is_dir": entry.is_dir()
                    })
                except OSError:
                    continue 
    except OSError:
        pass
    
    # Sort: Directories first, then by key
    def sort_key(x):
        is_dir = x["is_dir"]
        # Primary sort: Directory status (dirs on top)
        # Secondary sort: Selected criteria
        if sort_by == "size":
            val = x.get("raw_size", 0)
        elif sort_by == "date":
            val = x.get("raw_date", 0)
        else: # name
            val = x["name"].lower()
            
        return (not is_dir, val)

    entries.sort(key=sort_key)
    
    if os.path.dirname(path) != path:
        entries.insert(0, {
            "name": "..",
            "size": "<DIR>",
            "date": "",
            "raw_size": 0,
            "raw_date": 0,
            "is_dir": True
        })
    
    
    return entries

def is_ncdu_available() -> bool:
    import shutil
    return shutil.which("ncdu") is not None

def open_file_with_default_app(path: str):
    import subprocess
    import platform
    
    system = platform.system()
    try:
        if system == 'Darwin':       # macOS
            subprocess.run(('open', path))
        elif system == 'Windows':    # Windows
            os.startfile(path)
        else:                        # linux variants
            subprocess.run(('xdg-open', path))
    except Exception:
        pass

def copy_item(src: str, dst_dir: str):
    import shutil
    try:
        if os.path.isfile(src):
            shutil.copy2(src, dst_dir)
        elif os.path.isdir(src):
            basename = os.path.basename(os.path.normpath(src))
            shutil.copytree(src, os.path.join(dst_dir, basename))
    except OSError:
        pass

def move_item(src: str, dst_dir: str):
    import shutil
    try:
        shutil.move(src, dst_dir)
    except OSError:
        pass

def delete_item(path: str):
    import shutil
    try:
        if os.path.isfile(path) or os.path.islink(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
    except OSError:
        pass
