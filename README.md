# Kindle Firmware Checker

A Python script to check for the existence of Kindle firmware files on Amazon's download servers based on device model and version range.

## Overview

This script attempts to find available firmware `.bin` files for various Kindle models by iterating through potential version numbers (major.minor.patch) and checking if a corresponding file exists on the known Amazon S3 download URLs. It uses HTTP HEAD requests to check for file existence without downloading the entire file.

## Features

* **Model Support:** Pre-configured with various Kindle models (K4, K5, Paperwhite series, Oasis series, Scribe, etc.). Easily extendable by modifying the `kindle_models` dictionary.
* **Version Range Checking:** Specify a start and end version (Major.Minor.Patch) to search within. The script iterates through all possible patch versions (0-25) and minor versions (0-99) within the given major range.
* **Static Firmware Check:** Supports models with known, static firmware download links.
* **Filename Pattern Detection:** Attempts to automatically derive the correct filename pattern (e.g., `update_kindle_paperwhite_11th_*.bin`) from an example filename.
* **Search Modes:**
    * **Sequential:** Checks URLs one by one.
    * **Threaded:** Uses multiple threads for faster checking (configurable number of threads).
* **Configurable Settings:**
    * Adjust request timeout.
    * Set random delays between requests (configurable times and probability) to avoid overwhelming the server.
    * Toggle verbose output for detailed checking information.
    * Enable/disable and configure multithreading.
* **Menu-Driven Interface:** Easy-to-use command-line menu for selecting models and adjusting settings.

## How to Use

1.  **Prerequisites:** Make sure you have Python 3 and the `requests` library installed (`pip install requests`).
2.  **Run the script:** `python your_script_name.py` (replace `your_script_name.py` with the actual filename).
3.  **Main Menu:**
    * Choose `1` to start a firmware search.
    * Choose `2` to display the list of pre-configured Kindle models.
    * Choose `3` to change settings like threading, timeout, delays, or verbosity.
    * Choose `4` to exit the script.
4.  **Starting a Search:**
    * Select option `1`.
    * Enter the model identifier (e.g., `PW5`, `SCRIBE`) when prompted.
    * If the model uses dynamic version checking, you will be asked to enter the start and end versions for the search range (e.g., `5.14.0` to `5.17.25`). You can press Enter to accept the default range defined for the model.
    * The script will then start checking URLs. Found firmware filenames will be printed.

## Configuration & Model Data

* The script relies on the `kindle_models` dictionary within the code. This dictionary contains the base URLs, example filenames, default version ranges, and descriptions for each supported Kindle model.
* **Important:** Amazon might change the URL paths or filename conventions over time. You may need to update the `base_url` and `example_filename` entries in the `kindle_models` dictionary periodically to ensure the script works correctly for all models.

## Disclaimer

This script is provided for informational purposes. Download URLs and filename structures are based on observed patterns and may change without notice. Use responsibly and be mindful of the load placed on Amazon's servers by adjusting delays and the number of threads appropriately.
