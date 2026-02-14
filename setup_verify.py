
import sys
import os
import io
import time
import socket
import importlib.util
from pathlib import Path

def print_status(message, status):
    symbol = "✅" if status else "❌"
    print(f"{symbol} {message}")

def check_python():
    v = sys.version_info
    status = v.major == 3 and v.minor >= 10
    print_status(f"Python 3.10+ ({v.major}.{v.minor}.{v.micro})", status)

def check_file(path):
    exists = Path(path).exists()
    print_status(f"File exists: {path}", exists)
    return exists

def check_port(host, port, name):
    try:
        with socket.create_connection((host, port), timeout=1):
            print_status(f"{name} running on {host}:{port}", True)
            return True
    except (ConnectionRefusedError, socket.timeout, OSError):
        print_status(f"{name} NOT found on {host}:{port}", False)
        return False

def check_import(module_name):
    spec = importlib.util.find_spec(module_name)
    status = spec is not None
    print_status(f"Module installed: {module_name}", status)

def main():
    print("--- System Verification ---")
    check_python()
    
    print("\n--- Files ---")
    check_file("backend/.env")
    check_file("backend/requirements.txt")
    check_file("streamlit_app/requirements.txt")
    
    print("\n--- Services (Ensure they are running if checking connections) ---")
    # Postgres
    check_port("localhost", 5432, "PostgreSQL")
    # Ollama
    check_port("localhost", 11434, "Ollama")
    
    print("\n--- Python Dependencies (Basic Check) ---")
    # We can't easily check installed packages without knowing which venv we are in,
    # but we can try imports if we are running in the right environment.
    try:
        import django
        print_status("Django installed", True)
    except ImportError:
        print_status("Django installed", False)
        
    try:
        import fastapi
        print_status("FastAPI installed", True)
    except ImportError:
        print_status("FastAPI installed", False)
        
    try:
        import streamlit
        print_status("Streamlit installed", True)
    except ImportError:
        print_status("Streamlit installed", False)

    print("\n--- Verification Complete ---")
    print("Note: This script checks basic environment. For full verification, run unit tests.")

if __name__ == "__main__":
    main()
