# build/build_windows.py
import PyInstaller.__main__
import shutil
import os

def build():
    for folder in ['build', 'dist']:
        if os.path.exists(folder):
            shutil.rmtree(folder)

    PyInstaller.__main__.run([
        'bb_detector/main.py',
        '--name=BBDetector',
        '--onefile',
        '--windowed',
        '--add-data=assets;assets',
        '--hidden-import=pynput.keyboard._win32',
        '--hidden-import=pynput.mouse._win32',
        '--exclude-module=matplotlib',
        '--exclude-module=scipy',
        '--exclude-module=pandas',
    ])

    print("Build complete: dist/BBDetector.exe")

if __name__ == '__main__':
    build()
