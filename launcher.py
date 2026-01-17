# launcher.py
"""Entry point for PyInstaller build."""
import sys
import os

# Ensure the package directory is in path
if getattr(sys, 'frozen', False):
    # Running as compiled
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, base_path)

# Now import and run
from bb_detector.main import main

if __name__ == '__main__':
    main()
