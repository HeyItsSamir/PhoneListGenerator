#!/usr/bin/env python3
"""
Clean Phone Number List Generator (NO + sign)
Generates 0000000–9999999 for selected area codes
All numbers from one state → single dated file in PhoneListGenerator/
Perfect for OSINT, research, burn lists, etc.

Example output line: 15551234567  (pure digits, no +)
"""

import sys, os, json, signal, argparse, datetime, difflib
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from typing import List, Tuple, Optional

# ------------------------------------------------------------------
# Load area codes dictionary from JSON file
# ------------------------------------------------------------------
DATA_FILE = Path(__file__).parent / "area_codes.json"
with open(DATA_FILE) as f:
    STATE_AREA_CODES = json.load(f)

# Full state/territory names → abbreviations
STATE_NAME_TO_ABBR = {
    "ALABAMA": "AL", "ALASKA": "AK", "ARIZONA": "AZ", "ARKANSAS": "AR",
    "CALIFORNIA": "CA", "COLORADO": "CO", "CONNECTICUT": "CT", "DELAWARE": "DE",
    "FLORIDA": "FL", "GEORGIA": "GA", "HAWAII": "HI", "IDAHO": "ID",
    "ILLINOIS": "IL", "INDIANA": "IN", "IOWA": "IA", "KANSAS": "KS",
    "KENTUCKY": "KY", "LOUISIANA": "LA", "MAINE": "ME", "MARYLAND": "MD",
    "MASSACHUSETTS": "MA", "MICHIGAN": "MI", "MINNESOTA": "MN", "MISSISSIPPI": "MS",
    "MISSOURI": "MO", "MONTANA": "MT", "NEBRASKA": "NE", "NEVADA": "NV",
    "NEW HAMPSHIRE": "NH", "NEW JERSEY": "NJ", "NEW MEXICO": "NM", "NEW YORK": "NY",
    "NORTH CAROLINA": "NC", "NORTH DAKOTA": "ND", "OHIO": "OH", "OKLAHOMA": "OK",
    "OREGON": "OR", "PENNSYLVANIA": "PA", "RHODE ISLAND": "RI", "SOUTH CAROLINA": "SC",
    "SOUTH DAKOTA": "SD", "TENNESSEE": "TN", "TEXAS": "TX", "UTAH": "UT",
    "VERMONT": "VT", "VIRGINIA": "VA", "WASHINGTON": "WA", "WEST VIRGINIA": "WV",
    "WISCONSIN": "WI", "WYOMING": "WY",
    "AMERICAN SAMOA": "AS", "GUAM": "GU", "NORTHERN MARIANA ISLANDS": "MP",
    "PUERTO RICO": "PR", "U.S. VIRGIN ISLANDS": "VI", "US VIRGIN ISLANDS": "VI"
}

# ------------------------------------------------------------------
# Constants & setup
# ------------------------------------------------------------------
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
    """Sanitize state name for filenames."""
    return "".join(c if c.isalnum() or c in " -" else "_" for c in state_input.strip().title())

def get_output_filename(country_code: str, state_name: Optional[str]) -> Path:
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    country_label = "US" if country_code == "1" else f"Country{country_code}"
    state_label = get_safe_state_name(state_name) if state_name else "Custom"
    return OUTPUT_DIR / f"{country_label}_{state_label}_{date_str}.txt"

def normalize_state_input(state_input: str) -> Tuple[Optional[str], List[str]]:
    """
    Returns (abbr_or_none, suggestions). Accepts full name or abbreviation.
    """
    raw = state_input.strip().upper()

    # Direct abbreviation
    if raw in STATE_AREA_CODES:
        return raw, []

    # Full name → abbreviation
    abbr = STATE_NAME_TO_ABBR.get(raw)
    if abbr and abbr in STATE_AREA_CODES:
        return abbr, []

    # Suggestions
    candidates = list(STATE_AREA_CODES.keys()) + list(STATE_NAME_TO_ABBR.keys())
    suggestions = difflib.get_close_matches(raw, candidates, n=3, cutoff=0.6)
    return None, suggestions

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
        attempts = 0
        while attempts < 3:
            state_input = input("Enter state (full name or abbreviation, e.g. Alabama or AL): ").strip()
            abbr, suggestions = normalize_state_input(state_input)
            if abbr:
                codes = STATE_AREA_CODES[abbr]
                print(f"Found {len(codes)} area codes for {abbr}: {codes}")
                return codes, abbr

            attempts += 1
            if suggestions:
                print(f"State not found. Did you mean: {', '.join(suggestions)}?")
            else:
                print("State not found. Please try again (e.g., 'Alabama' or 'AL').")

        print("Too many failed attempts. Switching to manual area code entry.")

    # Manual mode
    codes: List[str] = []
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
    area_codes_list, state_name = get_area_codes()
    current_state_name = state_name

    # Output file
    output_file = get_output_filename(country_code, state_name)
    current_output_file = output_file
    output_file.touch()

    # Resume?
    progress = load_progress()
    if progress and progress.get("output_file") == str(output_file):
        resume = input
