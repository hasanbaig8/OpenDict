#!/usr/bin/env python3
"""
OpenDict Setup Script
Handles Python environment setup and dependency installation
"""

import os
import subprocess
import sys
import venv
from pathlib import Path


def create_virtual_environment():
    """Create a virtual environment if it doesn't exist."""
    venv_path = Path("venv")
    if not venv_path.exists():
        print("Creating virtual environment...")
        venv.create(venv_path, with_pip=True)
        print("Virtual environment created successfully!")
    else:
        print("Virtual environment already exists.")


def install_dependencies():
    """Install Python dependencies in the virtual environment."""
    venv_python = Path("venv/bin/python")
    if not venv_python.exists():
        print("Virtual environment not found. Creating...")
        create_virtual_environment()

    print("Installing dependencies...")
    subprocess.run(
        [str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], check=True
    )

    subprocess.run(
        [str(venv_python), "-m", "pip", "install", "-r", "requirements.txt"], check=True
    )

    if os.path.exists("requirements-dev.txt"):
        subprocess.run(
            [str(venv_python), "-m", "pip", "install", "-r", "requirements-dev.txt"],
            check=True,
        )

    print("Dependencies installed successfully!")


def setup_pre_commit():
    """Set up pre-commit hooks."""
    venv_python = Path("venv/bin/python")
    if venv_python.exists():
        try:
            subprocess.run(
                [str(venv_python), "-m", "pre_commit", "install"], check=True
            )
            print("Pre-commit hooks installed successfully!")
        except subprocess.CalledProcessError:
            print("Warning: Could not install pre-commit hooks.")


def main():
    """Main setup function."""
    print("OpenDict Python Setup")
    print("=" * 50)

    # Check Python version
    if sys.version_info < (3, 8):
        print("Error: Python 3.8+ is required")
        sys.exit(1)

    try:
        create_virtual_environment()
        install_dependencies()
        setup_pre_commit()

        print("\n" + "=" * 50)
        print("Setup completed successfully!")
        print("To activate the virtual environment:")
        print("  source venv/bin/activate")
        print("To run the transcription server:")
        print("  python transcribe_server.py")

    except subprocess.CalledProcessError as e:
        print(f"Error during setup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
