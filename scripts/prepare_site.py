import shutil
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    source = root / "frontend/dist"
    if not (source / "index.html").is_file() or not (source / "demo.json").is_file():
        raise ValueError("Build the frontend and synthetic dataset first")
    destination = root / "MarketInsight/web"
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)
    print("Prepared the built workspace for the installable package")


if __name__ == "__main__":
    main()
