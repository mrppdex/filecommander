import sys
import os
sys.path.append(os.getcwd())

try:
    from tui.git import GitScreen
    print("GitScreen imported successfully")
except Exception as e:
    print(f"Import failed: {e}")
    sys.exit(1)

import git
print(f"GitPython version: {git.__version__}")
try:
    r = git.Repo(".", search_parent_directories=True)
    print(f"Current repo: {r.working_dir}")
except:
    print("No repo found (expected if testing outside)")
