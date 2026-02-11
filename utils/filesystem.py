import os
import datetime
import humanize
from typing import Optional

import re

def list_directory(path: str, sort_by: str = "name", filter_pattern: Optional[str] = None, ascending: bool = True) -> list[dict]:
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
    
    if not ascending:
        # We want directories still on top? strict reverse reverses everything.
        # If we want dirs on top, we need to handle that.
        # Existing logic returns (not is_dir, val). False < True. So dirs (False) come before files (True).
        # If we reverse, files come before dirs.
        # We probably want to keep dirs on top, but reverse the secondary sort.
        # But `list.sort` is stable.
        # Let's re-sort or use a key that respects ascending flag for value but not for dir status.
        
        def sort_key_desc(x):
            is_dir = x["is_dir"]
            # To keep dirs on top (0), files bottom (1).
            # But reverse value. 
            # We can't easily negate strings.
            # So we rely on Python's stable sort and do it in two passes or clever key.
            # Easiest: separate dirs and files, sort each, then combine.
            pass
            
    # Refined Sort Logic
    dirs = [e for e in entries if e["is_dir"]]
    files = [e for e in entries if not e["is_dir"]]
    
    def get_val(x):
        if sort_by == "size": return x.get("raw_size", 0)
        if sort_by == "date": return x.get("raw_date", 0)
        return x["name"].lower()
        
    dirs.sort(key=get_val, reverse=not ascending)
    files.sort(key=get_val, reverse=not ascending)
    
    entries = dirs + files

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

def archive_item(path: str):
    import shutil
    
    dir_name = os.path.dirname(path)
    base_name = os.path.basename(path)
    archive_dir = os.path.join(dir_name, "archived")
    
    try:
        os.makedirs(archive_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        new_name = f"{timestamp}_{base_name}"
        dest = os.path.join(archive_dir, new_name)
        
        shutil.move(path, dest)
    except OSError:
        pass
