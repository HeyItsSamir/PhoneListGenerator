import concurrent.futures
import argparse
import signal
import os
import json
import sys  # Added for better exit handling

progress_file = "progress.json"

def get_country_code():
    country_code = input("Enter the country code (e.g., 1 for USA): ")
    return country_code

def get_area_codes():
    area_codes = []
    num_area_codes = int(input("How many area codes do you want to add? "))
    for i in range(num_area_codes):
        area_code = input(f"Enter area code {i + 1}: ")
        area_codes.append(area_code)
    return area_codes

def generate_and_write_chunk(task):
    area_code, country_code, start, end, output_file = task
    prefix = f"+{country_code}{area_code}"
    with open(output_file, 'a') as f:
        for i in range(start, end):
            f.write(f"{prefix}{i:07d}\n")

def generate_phone_numbers_multiprocess(country_code, area_codes, num_threads, start_from=0):
    chunk_size = 1_000_000  # Adjustable chunk size for balance between speed and overhead
    tasks = []
    for area_code in area_codes:
        # One file per area code for better organization and parallelism
        output_file = f"numbers_+{country_code}{area_code}.txt"
        # Ensure file exists (touch it)
        open(output_file, 'a').close()
        
        # Resume from start_from, but adjust per area code if needed (simplified here)
        for start in range(start_from, 10_000_000, chunk_size):
            end = min(start + chunk_size, 10_000_000)
            tasks.append((area_code, country_code, start, end, output_file))
    
    with concurrent.futures.ProcessPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(generate_and_write_chunk, task) for task in tasks]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()  # Raise any exceptions
            except Exception as e:
                print(f"Error in chunk: {e}")

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
    # For simplicity, we save a global start_from; enhance for per-area-code if needed
    current_position = {"start": global_start_from}
    save_progress(current_position)
    print("Progress saved. Exiting...")
    sys.exit(0)  # Clean exit

def main():
    global global_start_from  # For signal handler access
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
    
    min_threads = input(f"Enter minimum number of threads (default is {args.min_threads}): ") or args.min_threads
    max_threads = input(f"Enter maximum number of threads (default is {args.max_threads}): ") or args.max_threads
    num_threads = max(int(min_threads), int(max_threads))  # Use the larger one for simplicity

    print(f"Generating numbers using {num_threads} processes...")
    generate_phone_numbers_multiprocess(country_code, area_codes, num_threads, start_from=global_start_from)
    
    print("Generation complete. Files created:")
    for area_code in area_codes:
        print(f"numbers_+{country_code}{area_code}.txt")
    
    # Removed the retry with '+' since it's already included
    # Removed printing all numbers since it's impractical for large sets

if __name__ == "__main__":
    main()
