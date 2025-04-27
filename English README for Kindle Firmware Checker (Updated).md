# **Kindle Firmware Checker**

A Python script to check for the existence of Kindle firmware files on Amazon's download servers based on device model and version range.

## **Overview**

This script attempts to find available firmware .bin files for various Kindle models by iterating through potential version numbers (major.minor.patch) and checking if a corresponding file exists on the known Amazon S3 download URLs. It uses HTTP HEAD requests to check for file existence without downloading the entire file.

## **Features**

* **Model Support:** Pre-configured with various Kindle models (K4, K5, Paperwhite series, Oasis series, Scribe, etc.). Easily extendable by modifying the kindle\_models dictionary.  
* **Version Range Checking:** Specify a start and end version (Major.Minor.Patch) to search within. The script iterates through all possible patch versions (0-25) and minor versions (0-99) within the given major range.  
* **Static Firmware Check:** Supports models with known, static firmware download links.  
* **Filename Pattern Detection:** Attempts to automatically derive the correct filename pattern (e.g., update\_kindle\_paperwhite\_11th\_\*.bin) from an example filename.  
* **Search Modes:**  
  * **Sequential:** Checks URLs one by one.  
  * **Threaded:** Uses multiple threads for faster checking (configurable number of threads).  
* **Configurable Settings:**  
  * Adjust request timeout.  
  * Set random delays between requests (configurable times and probability) to avoid overwhelming the server.  
  * Toggle verbose output for detailed checking information.  
  * Enable/disable and configure multithreading.  
* **Menu-Driven Interface:** Easy-to-use command-line menu for selecting models and adjusting settings.  
* **Numerical Sorting:** Found firmware files are sorted numerically by version.

## **Installation & Setup**

To run this script, you need Python 3 installed on your system.

1. **Install Python 3:**  
   * If you don't have Python 3, download and install it from the official website: [python.org](https://www.python.org/downloads/)  
   * During installation on Windows, make sure to check the box that says "Add Python to PATH".  
2. **Get the Code:**  
   * **Option A (Git):** Clone the repository using Git:  
     git clone https://github.com/YOUR\_USERNAME/kindle-firmware-checker.git  
     cd kindle-firmware-checker

     (Replace YOUR\_USERNAME/kindle-firmware-checker with the actual URL of your repository).  
   * **Option B (Download ZIP):** Download the repository as a ZIP file from GitHub (using the "Code" button \-\> "Download ZIP"), and extract it to a folder on your computer. Open a terminal or command prompt in that folder.  
3. **Install Dependencies:**  
   * This script requires the requests and packaging libraries. Install them using pip and the provided requirements.txt file. Open your terminal or command prompt in the script's directory and run:  
     pip install \-r requirements.txt

     *(Note: Depending on your system, you might need to use pip3 instead of pip)*

## **How to Use**

1. **Open Terminal:** Navigate to the directory where you cloned or extracted the script using your terminal or command prompt.  
2. **Run the script:**  
   python your\_script\_name.py

   (Replace your\_script\_name.py with the actual filename, e.g., kindle\_checker.py).  
3. **Main Menu:**  
   * Choose 1 to start a firmware search.  
   * Choose 2 to display the list of pre-configured Kindle models.  
   * Choose 3 to change settings like threading, timeout, delays, or verbosity.  
   * Choose 4 to exit the script.  
4. **Starting a Search:**  
   * Select option 1\.  
   * Enter the model identifier (e.g., PW5, SCRIBE) when prompted.  
   * If the model uses dynamic version checking, you will be asked to enter the start and end versions for the search range (e.g., 5.14.0 to 5.17.25). You can press Enter to accept the default range defined for the model.  
   * The script will then start checking URLs. Found firmware filenames will be printed, sorted by version.

## **Configuration & Model Data**

* The script relies on the kindle\_models dictionary within the code. This dictionary contains the base URLs, example filenames, default version ranges, and descriptions for each supported Kindle model.  
* **Important:** Amazon might change the URL paths or filename conventions over time. You may need to update the base\_url and example\_filename entries in the kindle\_models dictionary periodically to ensure the script works correctly for all models.

## **Disclaimer**

This script is provided for informational purposes. Download URLs and filename structures are based on observed patterns and may change without notice. Use responsibly and be mindful of the load placed on Amazon's servers by adjusting delays and the number of threads appropriately.