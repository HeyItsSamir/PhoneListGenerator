#!/usr/bin/env python3
"""
Phone Number List Generator
Generates full 10M phone numbers per area code (0000000–9999999)
Merges all area codes from a state into one clean, dated file.
Perfect for red teaming, OSINT, or research (use responsibly).
"""

import sys
import subprocess
import os
import json
import signal
import argparse
import datetime
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from typing import List, Tuple, Optional

# ------------------------------------------------------------------
# Dependency check & auto-install
# ------------------------------------------------------------------
REQUIRED_LIBRARIES = ["py-area-codes"]

def check_dependencies() -> None:
    missing = []
    for lib in REQUIRED_LIBRARIES:
        try:
            __import__(lib.replace("-", "_"))
        except ImportError:
            missing.append(lib)

    if missing:
        print(f"Missing dependencies: {', '.join(missing)}")
        choice = input("Install them now? (y/n): ").strip().lower()
        if choice != "y":
            print("Exiting. Please install required packages.")
            sys.exit(1)
        for lib in missing:
            print(f"Installing {lib}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])

check_dependencies()

from py_area_codes import AreaCodes

# ------------------------------------------------------------------
# Global constants & setup
# ------------------------------------------------------------------
ac = AreaCodes()
OUTPUT_DIR = Path("PhoneListGenerator")
OUTPUT_DIR.mkdir(exist_ok=True)
PROGRESS_FILE = "progress.json"

global_start_from = 0
current_state_name: Optional[str] = None
current_output_file: Optional[Path] = None

# ------------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------------
def get_safe_state_name(state_input: str) -> str:
    """Convert CA, ca, california → California (or best guess)"""
    name = ac.get_state_name(state_input)
    if name:
        return "".join(c if c.isalnum() or c in " -" else "_" for c in name)
    return "".join(c if c.isalnum() else "_" for c in state_input.strip().title())

def get_output_filename(country_code: str, state_name: Optional[str]) -> Path:
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    country_label = "US" if country_code == "1" else f"Country{country_code}"
    state_label = get_safe_state_name(state_name) if state_name else "Custom"
    return OUTPUT_DIR / f"{country_label}_{state_label}_{date_str}.txt"

# ------------------------------------------------------------------
# User input functions
# ------------------------------------------------------------------
def get_country_code() -> str:
    while True:
        code = input("Enter the country code (e.g., 1 for USA): ").strip()
        if code.isdigit() and int(code) > 0:
            return code
        print("Invalid — please enter positive digits only.")

def get_area_codes() -> Tuple[List[str], Optional[str]]:
    choice = input("Use predefined area codes by state? (y/n): ").strip().lower()
    if choice == "y":
        state = input("Enter state name or abbreviation (e.g., Texas or TX): ").strip()
        codes = ac.get_area_codes(state)
        if codes:
            print(f"Found {len(codes)} area codes for {state}: {codes}")
            return codes, state
        print("State not found or has no area codes.")

    # Manual entry fallback
    print("Manual area code entry:")
    codes = []
    while True:
        n = input("How many area codes to add? ").strip()
        if n.isdigit() and int(n) > 0:
            n = int(n)
            break
        print("Please enter a positive number.")

    for i in range(n):
        while True:
            code = input(f"Area code {i+1}/{n}: ").strip()
            if code.isdigit() and 1 <= len(code) <= 5:
                codes.append(code)
                break
            print("Invalid — digits only (1–5 digits).")
    return codes, None

# ------------------------------------------------------------------
# Core generation logic
# ------------------------------------------------------------------
def generate_chunk(task: Tuple[str, str, int, int, Path]) -> None:
    area_code, country_code, start, end, outfile = task
    prefix = f"+{country_code}{area_code}"
    lines = [f"{prefix}{i:07d}\n" for i in range(start, end)]
    with open(outfile, "a", buffering=1024*1024) as f:
        f.writelines(lines)

def task_generator(country_code: str, area_codes: List[str], start_from: int, chunk_size: int, outfile: Path):
    prefix = f"+{country_code}"
    for area_code in area_codes:
        for start in range(start_from, 10_000_000, chunk_size):
            end = min(start + chunk_size, 10_000_000)
            yield (area_code, country_code, start, end, outfile)

# ------------------------------------------------------------------
# Progress & signal handling
# ------------------------------------------------------------------
def save_progress(position: int) -> None:
    data = {
        "start_from": position,
        "state": current_state_name,
        "output_file": str(current_output_file) if current_output_file else None
    }
    with open(PROGRESS_FILE, "w") as f:
        json.dump(data, f)

def load_progress() -> Optional[dict]:
    if PROGRESS_FILE in os.listdir("."):
        try:
            with open(PROGRESS_FILE) as f:
                return json.load(f)
        except:
            return None
    return None

def signal_handler(sig, frame):
    print("\nInterrupt received — saving progress...")
    save_progress(global_start_from)
    print(f"Progress saved. Resume later with the same settings.")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# ------------------------------------------------------------------
# Main function
# ------------------------------------------------------------------
def main():
    global global_start_from, current_state_name, current_output_file

    print("Phone Number List Generator\n")

    parser = argparse.ArgumentParser()
    parser.add_argument("--threads", type=int, default=os.cpu_count(),
                        help="Number of processes (default: CPU count)")
    args = parser.parse_args()

    country_code = get_country_code()
    area_codes, state_name = get_area_codes()
    current_state_name = state_name

    # Output file setup
    output_file = get_output_filename(country_code, state_name)
    current_output_file = output_file
    output_file.touch()  # create if not exists

    # Resume logic
    progress = load_progress()
    if progress and progress.get("output_file") == str(output_file):
        resume = input("Previous progress found for this exact file. Resume? (y/n): ").strip().lower()
        if resume == "y":
            global_start_from = progress.get("start_from", 0)
            print(f"Resuming from number offset: {global_start_from:,}")
        else:
            global_start_from = 0
            output_file.unlink(missing_ok=True)
            output_file.touch()
    else:
        global_start_from = 0
        if output_file.exists():
            output_file.unlink()
        output_file.touch()

    # Thread count
    print(f"\nUsing {args.threads} processes")
    print(f"Generating {len(area_codes)} area code(s) → {len(area_codes) * 10_000_000:,} numbers total")
    print(f"Output → {output_file}\n")

    chunk_size = 1_000_000
    tasks = task_generator(country_code, area_codes, global_start_from, chunk_size, output_file)

    with ProcessPoolExecutor(max_workers=args.threads) as executor:
        for i, _ in enumerate(executor.map(generate_chunk, tasks, chunksize=1), 1):
            if i % 10 == 0:  # feedback every 10M numbers
                print(f"\rProgress: {i * chunk_size:,} numbers written...", end="", flush=True)
            global_start_from += chunk_size

    # Final cleanup
    if os.path.getsize(output_file) == 0:
        output_file.unlink()
        print("No numbers generated.")
    else:
        print(f"\nGeneration complete!")
        print(f"File: {output_file}")
        print(f"Size: {os.path.getsize(output_file) / 1e9:.2f} GB")
        print(f"Contains: {len(area_codes)} area codes × 10M = {len(area_codes)*10_000_000:,} numbers")

    # Clean up progress file on success
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)

if __name__ == "__main__":
    main()
