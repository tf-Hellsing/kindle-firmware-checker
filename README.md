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

If you just want to use the tool without installing Python or dealing with code, download the pre-packaged application archive (.zip for Windows) from the [**Releases Page**](https://github.com/tf-Hellsing/kindle-firmware-checker/releases).

1. Go to the [Releases Page](https://github.com/tf-Hellsing/kindle-firmware-checker/releases).  
2. Find the latest release.  
3. Under "Assets", download the .zip file (e.g., KindleFirmwareChecker\_vX.Y.Z\_Windows.zip).  
4. Save the .zip file somewhere on your computer.  
5. **Extract the ZIP archive:** Right-click the downloaded .zip file and choose "Extract All..." (or use a tool like 7-Zip or WinRAR). This will create a new folder containing the application files.  
6. **Run the executable:** Open the newly extracted folder. Inside, find and double-click the main executable file (it will likely be named kindle\_checker\_vX.Y.Z.exe or similar). No installation is needed.

**Important Note on Antivirus Software:**

* You might receive a warning from your browser, Windows Defender, or other antivirus software when downloading the .zip file or running the .exe file inside it. **This is likely a false positive.**  
* **Why does this happen?** The executable is created using PyInstaller, which bundles the Python script and its libraries. Antivirus programs can sometimes be suspicious of these types of bundled files, especially if they are not digitally signed (which requires a paid certificate). The script also makes network connections (requests) to check Amazon's servers, which can sometimes trigger heuristic detection.  
* **Is it safe?** The source code for this script is publicly available in this repository for anyone to review. We believe the executable is safe, but if you have concerns, you can always run the script from the source code (see option 2 below).  
* **Transparency:** You can check the VirusTotal scan results for specific files:  
  * kindle\_checker\_v1.2.1-beta.exe  
    https://www.virustotal.com/gui/file/ea1d297963cc26d27ee49161a49848b491881b3d9bf597efecb98def6fa125eb  
  * kindle\_checker\_v1.2.1-beta.py  
    https://www.virustotal.com/gui/file/0b2757ef2dccc3f0abe03e395f179d083358921b210637e476766081e7c2ee72  
    (Note: These links are for a specific version. Links for the latest release might be found in the respective release notes.)

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
