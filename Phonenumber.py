import concurrent.futures
import argparse
import signal
import os
import json

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

def generate_phone_numbers_chunk(area_code, country_code, start, end):
    phone_numbers = []
    for number in range(start, end):
        phone_number = f"+{country_code}{area_code}{str(number).zfill(7)}"
        phone_numbers.append(phone_number)
    return phone_numbers

def generate_phone_numbers_multithreaded(country_code, area_codes, num_threads, start_from=0):
    phone_numbers = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        chunk_size = 1000000  # Define chunk size for each thread
        for area_code in area_codes:
            for start in range(start_from, 10000000, chunk_size):
                end = min(start + chunk_size, 10000000)
                futures.append(executor.submit(generate_phone_numbers_chunk, area_code, country_code, start, end))
        for future in concurrent.futures.as_completed(futures):
            phone_numbers.extend(future.result())
    return phone_numbers

def save_to_file(phone_numbers, filename):
    with open(filename, 'w') as file:
        for number in phone_numbers:
            file.write(f"{number}\n")

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
    current_position = {"start": start_from}  # Add any additional state details here
    save_progress(current_position)
    print("Progress saved. Exiting...")
    os._exit(0)  # Exit the program immediately

def main():
    global start_from
    signal.signal(signal.SIGINT, signal_handler)
    
    parser = argparse.ArgumentParser(description="Generate phone numbers by area code.")
    parser.add_argument('--min-threads', type=int, default=1, help="Minimum number of threads.")
    parser.add_argument('--max-threads', type=int, default=4, help="Maximum number of threads.")
    args = parser.parse_args()

    country_code = get_country_code()
    area_codes = get_area_codes()
    progress = load_progress()
    
    if progress:
        resume_option = input("Previous progress detected. Do you want to resume from the last session? (y/n): ")
        start_from = progress["start"] if resume_option.lower() == 'y' else 0
    else:
        start_from = 0
    
    min_threads = input(f"Enter minimum number of threads (default is {args.min_threads}): ") or args.min_threads
    max_threads = input(f"Enter maximum number of threads (default is {args.max_threads}): ") or args.max_threads
    num_threads = int(max_threads) if int(max_threads) > int(min_threads) else int(min_threads)

    phone_numbers = generate_phone_numbers_multithreaded(country_code, area_codes, num_threads, start_from=start_from)
    
    print("Generated phone numbers:")
    for phone_number in phone_numbers:
        print(phone_number)

    save_option = input("Do you want to save these phone numbers to a file? (y/n): ")
    if save_option.lower() == 'y':
        filename = input("Enter the filename (e.g., ChicagoAreaCodePhoneNumbers.txt): ")
        save_to_file(phone_numbers, filename)
        print(f"Phone numbers saved to {filename}")
    
    # Ask if user wants to try with a "+" before the country code
    retry_with_plus = input("Do you want to retry with a '+' before the country code? (y/n): ")
    if retry_with_plus.lower() == 'y':
        phone_numbers = generate_phone_numbers_multithreaded(country_code, area_codes, num_threads, start_from=start_from)
        print("Generated phone numbers with '+':")
        for phone_number in phone_numbers:
            print(f"+{phone_number}")

        save_option = input("Do you want to save these phone numbers to a file? (y/n): ")
        if save_option.lower() == 'y':
            filename = input("Enter the filename (e.g., ChicagoAreaCodePhoneNumbers.txt): ")
            save_to_file(phone_numbers, filename)
            print(f"Phone numbers saved to {filename}")

if __name__ == "__main__":
    main()
