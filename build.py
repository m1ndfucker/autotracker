# build.py
import platform
import subprocess
import sys

def main():
    system = platform.system()
    print(f"Building for {system}...")

    if system == 'Windows':
        subprocess.run([sys.executable, 'build/build_windows.py'])
    elif system == 'Darwin':
        subprocess.run([sys.executable, 'build/build_macos.py', 'py2app'])
    else:
        print(f"Unsupported: {system}")
        sys.exit(1)

if __name__ == '__main__':
    main()
