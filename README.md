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
* **Multi-Language Support:** User interface available in English (en) and German (de).  
* **Configurable Settings:**  
  * Adjust request timeout.  
  * Set random delays between requests (configurable times and probability) to avoid overwhelming the server.  
  * Toggle verbose output for detailed checking information.  
  * Enable/disable and configure multithreading.  
  * Change the interface language.  
* **Menu-Driven Interface:** Easy-to-use command-line menu for selecting models and adjusting settings.  
* **Numerical Sorting:** Found firmware files are sorted numerically by version.

## **Getting Started / How to Use**

There are two main ways to use this tool:

### **1\. For End-Users (Recommended \- Easiest)**

If you just want to use the tool without installing Python or dealing with code, download the pre-compiled executable (.exe for Windows) from the [**Releases Page**](https://github.com/tf-Hellsing/kindle-firmware-checker/releases).

1. Go to the [Releases Page](https://github.com/tf-Hellsing/kindle-firmware-checker/releases).  
2. Find the latest release.  
3. Under "Assets", download the .exe file (e.g., KindleFirmwareChecker\_vX.Y.Z\_Windows.exe).  
4. Save the .exe file somewhere on your computer.  
5. Double-click the .exe file to run the checker. No installation is needed.  
   (Note: Your browser or Windows might show a warning because the file is downloaded from the internet. This is normal for executables created with tools like PyInstaller.)

### **2\. For Developers (Running from Source)**

If you are comfortable with Python and the command line, you can run the script directly from the source code.

1. **Install Python 3:**  
   * If you don't have Python 3, download and install it from [python.org](https://www.python.org/downloads/).  
   * During installation on Windows, make sure to check the box that says "Add Python to PATH".  
2. **Get the Code:**  
   * **Option A (Git):** Clone the repository:  
     git clone https://github.com/tf-Hellsing/kindle-firmware-checker.git  
     cd kindle-firmware-checker

   * **Option B (Download ZIP):** Download the repository as a ZIP file from the main repository page ("Code" button \-\> "Download ZIP"), and extract it. Open a terminal or command prompt in that folder.  
3. **Install Dependencies:**  
   * Open your terminal/command prompt in the script's directory and run:  
     pip install \-r requirements.txt

     *(Note: You might need to use pip3 instead of pip)*  
4. **Run the Script:**  
   * In the same terminal/command prompt, run:  
     python kindle\_checker\_vX.Y.Z.py

     (Replace kindle\_checker\_vX.Y.Z.py with the actual Python script filename).  
5. **Follow Menu Prompts:** Use the command-line menu to select models, change settings (including language), and start the search.

## **Configuration & Model Data**

* The script relies on the kindle\_models dictionary within the code. This dictionary contains the base URLs, example filenames, default version ranges, and descriptions for each supported Kindle model.  
* **Important:** Amazon might change the URL paths or filename conventions over time. You may need to update the base\_url and example\_filename entries in the kindle\_models dictionary periodically to ensure the script works correctly for all models. Contributions via Pull Requests are welcome\!

## **Disclaimer**

This script is provided for informational purposes. Download URLs and filename structures are based on observed patterns and may change without notice. Use responsibly and be mindful of the load placed on Amazon's servers by adjusting delays and the number of threads appropriately.