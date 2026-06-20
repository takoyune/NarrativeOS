import os
import sys
import argparse
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def run_server():
    """Start the NarrativeOS web server."""
    print("Starting NarrativeOS server on http://localhost:8765")
    try:
        subprocess.run([sys.executable, "server.py"], cwd=BASE_DIR)
    except KeyboardInterrupt:
        print("\nServer stopped.")

def build_epub(novel_folder: str):
    """Build an EPUB for a specific novel folder."""
    if not novel_folder:
        print("Error: Please provide a novel folder path.")
        return
    print(f"Building EPUB for: {novel_folder}")
    subprocess.run([sys.executable, "build_novel.py", novel_folder], cwd=BASE_DIR)

def check_types():
    """Run mypy to check Python type hints."""
    print("Running type checks with mypy...")
    try:
        subprocess.run([sys.executable, "-m", "mypy", "server.py", "build_novel.py", "epub_builder.py"], cwd=BASE_DIR)
    except FileNotFoundError:
        print("mypy not found. Install it via 'pip install mypy'")

def format_code():
    """Format code with black."""
    print("Formatting code with black...")
    try:
        subprocess.run([sys.executable, "-m", "black", "server.py", "build_novel.py", "epub_builder.py", "tasks.py"], cwd=BASE_DIR)
    except FileNotFoundError:
        print("black not found. Install it via 'pip install black'")

def main():
    parser = argparse.ArgumentParser(description="NarrativeOS Task Runner")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Start server
    subparsers.add_parser("serve", help="Start the NarrativeOS web server")

    # Build EPUB
    build_parser = subparsers.add_parser("build", help="Build an EPUB for a novel")
    build_parser.add_argument("folder", help="Path to the novel folder")

    # QA / Checks
    subparsers.add_parser("check", help="Run type hints check (mypy)")
    subparsers.add_parser("fmt", help="Format code (black)")

    args = parser.parse_args()

    if args.command == "serve":
        run_server()
    elif args.command == "build":
        build_epub(args.folder)
    elif args.command == "check":
        check_types()
    elif args.command == "fmt":
        format_code()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
