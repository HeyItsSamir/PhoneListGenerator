import sys
import subprocess

# ------------------------------------------------------------
# Dependency check
# ------------------------------------------------------------
REQUIRED_LIBRARIES = ["py-area-codes"]

def check_dependencies():
    missing = []
    for lib in REQUIRED_LIBRARIES:
        try:
            __import__(lib.replace("-", "_"))  # import py_area_codes
        except ImportError:
            missing.append(lib)

    if missing:
        print("Missing dependencies detected:", ", ".join(missing))
        choice = input("Do you want to install them now? (y/n): ").strip().lower()
        if choice == "y":
            for lib in missing:
                print(f"Installing {lib}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
        else:
            print("Cannot continue without required dependencies. Exiting.")
            sys.exit(1)

# Run the check before anything else
check_dependencies()

import concurrent.futures
import argparse
import signal
import os
import json
import sys
from py_area_codes import AreaCodes   # ✅ Import the library

progress_file = "progress.json"
ac = AreaCodes()  # ✅ Initialize once

def get_country_code():
    while True:
        code = input("Enter the country code (e.g., 1 for USA): ").strip()
        if code.isdigit() and int(code) > 0:
            return code
        print("Invalid country code — positive digits only.")

def get_area_codes():
    choice = input("Do you want to use predefined area codes by state? (y/n): ").lower()
    if choice == "y":
        state = input("Enter the state name or abbreviation (e.g., California or CA): ").strip()
        codes = ac.get_area_codes(state)
        if codes:
            print(f"Using predefined area codes for {state}: {codes}")
            return codes
        else:
            print("State not found. Falling back to manual entry.")

    # Manual entry fallback
    area_codes = []
    while True:
        num_area_codes = input("How many area codes do you want to add? ").strip()
        if num_area_codes.isdigit() and int(num_area_codes) > 0:
            num_area_codes = int(num_area_codes)
            break
        print("Invalid input — must be a positive number.")

    for i in range(num_area_codes):
        while True:
            area_code = input(f"Enter area code {i + 1}: ").strip()
            if area_code.isdigit() and 1 <= len(area_code) <= 5:
                area_codes.append(area_code)
                break
            print("Invalid area code — digits only (1–5 digits).")
    return area_codes

# ------------------------------------------------------------
# OPTIMIZED CHUNK GENERATOR (batch writes)
# ------------------------------------------------------------
def generate_and_write_chunk(task):
    area_code, country_code, start, end, output_file = task
    prefix = f"+{country_code}{area_code}"
    lines = [f"{prefix}{i:07d}\n" for i in range(start, end)]
    with open(output_file, "a", buffering=1024 * 1024) as f:
        f.write("".join(lines))

# ------------------------------------------------------------
# STREAMING TASK GENERATOR
# ------------------------------------------------------------
def task_generator(country_code, area_codes, start_from, chunk_size):
    for area_code in area_codes:
        output_file = f"numbers_+{country_code}{area_code}.txt"
        open(output_file, 'a').close()
        for start in range(start_from, 10_000_000, chunk_size):
            end = min(start + chunk_size, 10_000_000)
            yield (area_code, country_code, start, end, output_file)

# ------------------------------------------------------------
# MULTIPROCESS CONTROLLER
# ------------------------------------------------------------
def generate_phone_numbers_multiprocess(country_code, area_codes, num_threads, start_from=0):
    chunk_size = 1_000_000
    tasks = task_generator(country_code, area_codes, start_from, chunk_size)
    with concurrent.futures.ProcessPoolExecutor(max_workers=num_threads) as executor:
        for _ in executor.map(generate_and_write_chunk, tasks, chunksize=1):
            pass

def save_progress(current_position):
    with open(progress_file, 'w') as file:
        json.dump(current_position, file)

def load_progress():
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as file:
            return json.load(file)
    return None

def signal_handler(sig, frame):
    print("Interrupt received, saving progress...")
    current_position = {"start": global_start_from}
    save_progress(current_position)
    print("Progress saved. Exiting...")
    sys.exit(0)

def main():
    global global_start_from
    signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser(description="Generate phone numbers by area code.")
    parser.add_argument('--min-threads', type=int, default=1, help="Minimum number of threads.")
    parser.add_argument('--max-threads', type=int, default=os.cpu_count(), help="Maximum number of threads (default: CPU count).")
    args = parser.parse_args()

    country_code = get_country_code()
    area_codes = get_area_codes()
    progress = load_progress()

    if progress:
        resume_option = input("Previous progress detected. Do you want to resume from the last session? (y/n): ")
        global_start_from = progress["start"] if resume_option.lower() == 'y' else 0
    else:
        global_start_from = 0

    min_threads_raw = input(f"Enter minimum number of threads (default is {args.min_threads}): ").strip()
    max_threads_raw = input(f"Enter maximum number of threads (default is {args.max_threads}): ").strip()

    def parse_threads(raw_value, default):
        if raw_value == "":
            return default
        if not raw_value.isdigit():
            print("Invalid input — using default.")
            return default
        v = int(raw_value)
        if v <= 0:
            print("Thread count must be positive — using default.")
            return default
        return v

    min_threads = parse_threads(min_threads_raw, args.min_threads)
    max_threads = parse_threads(max_threads_raw, args.max_threads)

    num_threads = min(max_threads, max(min_threads, 1))

    print(f"Generating numbers using {num_threads} processes...")
    generate_phone_numbers_multiprocess(country_code, area_codes, num_threads, start_from=global_start_from)

    print("Generation complete. Files created:")
    for area_code in area_codes:
        print(f"numbers_+{country_code}{area_code}.txt")

if __name__ == "__main__":
    main()
