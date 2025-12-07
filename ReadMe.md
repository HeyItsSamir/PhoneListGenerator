# Phone List Generating Script

This script is designed to iterate and create all possible phone numbers in specified geographic regions. By prompting the user for a country code and multiple area codes, it generates a comprehensive list of phone numbers, which can be saved to a file for further use. The generated wordlists can be used with brute-force tools.

> **Note:** This script is strictly for educational purposes and should be used as such.

---

## Features
- Prompt user for country code and multiple area codes  
- Generate phone numbers for specified area codes  
- Save generated phone numbers to a file  
- Option to resume from the last saved progress  

---

## Usage

### 1. Clone the Repository
```bash
git clone https://github.com/HeyItsSamir/PhoneListGenerator
```

### 2. Change Directory
```
cd PhoneListGenerator
```

### 3. Make the Script Executable
```
chmod +x Phonenumber.py
```

### 4. Create and Activate a Virtual Environment
```
python3 -m venv venv
source venv/bin/activate
```

### 5. Install Dependencies
```
pip install py-area-codes
```

### 6. Run the Script
```
python3 ./Phonenumber.py
```

### 7.Deactivate the Virtual Environment (when finished)
```
deactivate
```

### Important: Run Inside Virtual Environment

Before running the script, make sure you have activated the virtual environment you created in step 4. This ensures that all required dependencies (like `py-area-codes`) are available.

```bash
# Activate the virtual environment
source venv/bin/activate

# Run the script
python3 ./Phonenumber.py
