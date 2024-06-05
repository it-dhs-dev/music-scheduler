import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def main():
    packages = [
        "tkinter",
        "spotipy",
        "ttkthemes"
    ]

    for package in packages:
        try:
            __import__(package)
            print(f"{package} is already installed.")
        except ImportError:
            print(f"Installing {package}...")
            install(package)
            print(f"{package} installed successfully.")

if __name__ == "__main__":
    main()
