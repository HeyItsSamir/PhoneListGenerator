# Phone List Generating Script
This script is designed to iterate and create all possible phone numbers in specified geographic regions. 
By prompting the user for a country code and multiple area codes, it generates a comprehensive list of phone numbers, which can be saved to a file for further use. 
The generated wordlists can be used with brute-force tools.

**Note: This script is stricly for educational-purposes and should be used as such.**

## Features
* Prompt user for country code and multiple area codes
* Generate phone numbers for specified area codes
* Save generated phone numbers to a file
* Option to resume from the last saved progress

## Usage
Clone the Repository
```
git clone https://github.com/HeyItsSamir/PhoneListGenerator
```
Change Directory
```
cd PhoneListGenerator
```
Make the Script and Executable
````
sudo chmod +x Phonenumber.py
````
Run the Script with Python
````
python3 ./Phonenumber.py
````

## Example

![Phonenumber-py Completion](https://github.com/user-attachments/assets/b3413e13-c867-4958-9c90-f5d4cd6eac97)

* Multi-threaded execution for faster generation

![Phonenumber-py Completion](https://github.com/user-attachments/assets/9bf05e3d-4165-45c0-86cd-edcac6736557)

![CD Dir](https://github.com/user-attachments/assets/5e3673bf-6f9d-41f9-a861-c321d9c19c1f)
* May need to move file to a .txt   Sudo mv ChicagoPhoneNumbers > ChicagoPhoneNumbers.txt

