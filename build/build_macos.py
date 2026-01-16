# build/build_macos.py
from setuptools import setup
import shutil
import os

def build():
    for folder in ['build', 'dist']:
        if os.path.exists(folder):
            shutil.rmtree(folder)

    APP = ['bb_detector/main.py']
    DATA_FILES = [('assets/templates', ['assets/templates/you_died_en.png', 'assets/templates/you_died_ru.png'])]
    OPTIONS = {
        'argv_emulation': False,
        'bundle_identifier': 'kg.home.watch.bbdetector',
        'plist': {
            'CFBundleName': 'BB Death Detector',
            'CFBundleVersion': '1.0.0',
            'LSUIElement': True,
            'NSScreenCaptureUsageDescription': 'Screen capture for death detection',
        },
        'packages': ['dearpygui', 'cv2', 'mss', 'pynput', 'pystray', 'websockets'],
    }

    setup(
        name='BB Death Detector',
        app=APP,
        data_files=DATA_FILES,
        options={'py2app': OPTIONS},
        setup_requires=['py2app'],
    )

if __name__ == '__main__':
    build()
