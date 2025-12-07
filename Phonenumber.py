#!/usr/bin/env python3
"""
Clean Phone Number List Generator (NO + sign)
Generates 0000000–9999999 for selected area codes
All numbers from one state → single dated file in PhoneListGenerator/
Perfect for OSINT, research, burn lists, etc.

Example output line: 15551234567  (pure digits, no +)
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
import json
from pathlib import Path

# Load area codes dictionary from JSON file
DATA_FILE = Path(__file__).parent / "area_codes.json"
with open(DATA_FILE) as f:
    STATE_AREA_CODES = json.load(f)



# ------------------------------------------------------------------
# Constants & setup
# ------------------------------------------------------------------
ac = AreaCodes()
OUTPUT_DIR = Path("PhoneListGenerator")
OUTPUT_DIR.mkdir(exist_ok=True)
PROGRESS_FILE = "progress.json"

global_start_from = 0
current_state_name: Optional[str] = None
current_output_file: Optional[Path] = None

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def get_safe_state_name(state_input: str) -> str:
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
# Input
# ------------------------------------------------------------------
def get_country_code() -> str:
    while True:
        code = input("Enter country code (e.g. 1 for USA): ").strip()
        if code.isdigit() and int(code) > 0:
            return code
        print("Positive digits only.")

def get_area_codes() -> Tuple[List[str], Optional[str]]:
    choice = input("Use predefined area codes by state? (y/n): ").strip().lower()
    if choice == "y":
        state = input("Enter state (e.g. Florida or FL): ").strip()
        state_key = state.upper()
        if state_key in STATE_AREA_CODES:
            codes = STATE_AREA_CODES[state_key]
            print(f"Found {len(codes)} area codes for {state}: {codes}")
            return codes, state_key
        print("State not found.")
        return [], None

    # Manual mode
    codes = []
    while True:
        n = input("How many area codes to add? ").strip()
        if n.isdigit() and int(n) > 0:
            n = int(n)
            break
        print("Enter a positive number.")

    for i in range(n):
        while True:
            code = input(f"Area code {i+1}/{n}: ").strip()
            if code.isdigit() and 1 <= len(code) <= 5:
                codes.append(code)
                break
            print("Digits only (1–5).")
    return codes, None

    # Manual mode
    codes = []
    while True:
        n = input("How many area codes to add? ").strip()
        if n.isdigit() and int(n) > 0:
            n = int(n)
            break
        print("Enter a positive number.")

    for i in range(n):
        while True:
            code = input(f"Area code {i+1}/{n}: ").strip()
            if code.isdigit() and 1 <= len(code) <= 5:
                codes.append(code)
                break
            print("Digits only (1–5).")
    return codes, None

# ------------------------------------------------------------------
# Core generation (NO + SIGN!)
# ------------------------------------------------------------------
def generate_chunk(task: Tuple[str, str, int, int, Path]) -> None:
    area_code, country_code, start, end, outfile = task
    # ← NO "+" HERE ANYMORE
    prefix = f"{country_code}{area_code}"
    lines = [f"{prefix}{i:07d}\n" for i in range(start, end)]
    with open(outfile, "a", buffering=1024*1024) as f:
        f.writelines(lines)

def task_generator(country_code: str, area_codes: List[str], start_from: int, chunk_size: int, outfile: Path):
    for area_code in area_codes:
        for start in range(start_from, 10_000_000, chunk_size):
            end = min(start + chunk_size, 10_000_000)
            yield (area_code, country_code, start, end, outfile)

# ------------------------------------------------------------------
# Progress & interrupt handling
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
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE) as f:
                return json.load(f)
        except:
            return None
    return None

def signal_handler(sig, frame):
    print("\nInterrupt received — saving progress...")
    save_progress(global_start_from)
    print("Progress saved to progress.json")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
def main():
    global global_start_from, current_state_name, current_output_file

    print("Clean Phone Number List Generator (no + sign)\n")

    parser = argparse.ArgumentParser()
    parser.add_argument("--threads", type=int, default=os.cpu_count(),
                        help="Number of processes (default: all cores)")
    args = parser.parse_args()

    country_code = get_country_code()
    area_codes, state_name = get_area_codes()
    current_state_name = state_name

    # Output file
    output_file = get_output_filename(country_code, state_name)
    current_output_file = output_file
    output_file.touch()

    # Resume?
    progress = load_progress()
    if progress and progress.get("output_file") == str(output_file):
        resume = input(f"Resume previous run for {output_file.name}? (y/n): ").strip().lower()
        if resume == "y":
            global_start_from = progress.get("start_from", 0)
            print(f"Resuming from offset {global_start_from:,}")
        else:
            global_start_from = 0
            output_file.unlink(missing_ok=True)
            output_file.touch()
    else:
        global_start_from = 0
        output_file.unlink(missing_ok=True)
        output_file.touch()

    total_numbers = len(area_codes) * 10_000_000
    print(f"\nGenerating {len(area_codes)} area code(s) → {total_numbers:,} numbers total")
    print(f"Output → {output_file}\n")

    chunk_size = 1_000_000
    tasks = task_generator(country_code, area_codes, global_start_from, chunk_size, output_file)

    with ProcessPoolExecutor(max_workers=args.threads) as executor:
        completed = 0
        for _ in executor.map(generate_chunk, tasks, chunksize=1):
            completed += chunk_size
            global_start_from += chunk_size
            if completed % (chunk_size * 10) == 0:
                print(f"\rWritten: {completed:,} / {total_numbers:,} numbers...", end="", flush=True)

    # Final report
    if output_file.stat().st_size == 0:
        output_file.unlink()
        print("\nNo numbers generated.")
    else:
        size_gb = output_file.stat().st_size / 1e9
        print(f"\nDONE!")
        print(f"File → {output_file}")
        print(f"Size → {size_gb:.2f} GB")
        print(f"Total numbers → {total_numbers:,}")

    # Clean up progress file on success
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)

if __name__ == "__main__":
    main()
