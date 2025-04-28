import requests
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import math # Hinzugefügt für genauere Fortschrittsberechnung
import re
import os # Für os.path.splitext in get_filename_pattern
from packaging import version as pkg_version # Für robusten Versionsvergleich

# --- Konstanten ---
DEFAULT_TIMEOUT = 10
DEFAULT_MAX_THREADS = 5
DEFAULT_DELAY_PROBABILITY = 0.1
DEFAULT_DELAYS = [0.5, 1.0, 1.5, 2.0, 2.5]
DEFAULT_VERBOSE = False
DEFAULT_LANGUAGE = 'de' # Standardmäßig Deutsch

# --- Übersetzungen ---
TRANSLATIONS = {
    'de': {
        # Menü
        'main_menu_title': "--- Kindle Firmware Checker Hauptmenü ---",
        'menu_option_1': "1. Firmware-Suche starten",
        'menu_option_2': "2. Verfügbare Kindle Modelle anzeigen",
        'menu_option_3': "3. Einstellungen ändern",
        'menu_option_4': "4. Set Language",  # Geändert zu 4
        'menu_option_5': "5. Skript beenden", # Geändert zu 5
        'prompt_select_option': "Bitte wähle eine Option: ",
        'invalid_input_menu': "Ungültige Eingabe. Bitte wähle eine der Optionen {}.", # Platzhalter für Bereich hinzugefügt
        'script_exiting': "Skript wird beendet.",
        # Einstellungen
        'settings_menu_title': "--- Einstellungen ---",
        'setting_option_1': "1. Mögliche Verzögerungszeiten (aktuell: {})",
        'setting_option_2': "2. Wahrscheinlichkeit für Verzögerung (aktuell: {:.1f}%)",
        'setting_option_3': "3. Multithreading verwenden (aktuell: {})",
        'setting_option_4_on': "4. Maximale Threads (aktuell: {})",
        'setting_option_4_off': "4. Maximale Threads (N/A - Multithreading deaktiviert)",
        'setting_option_5': "5. Timeout für Anfragen (aktuell: {}s)",
        'setting_option_6': "6. Ausführliche Ausgabe (Verbose) (aktuell: {})",
        'setting_option_7': "7. Zurück zum Hauptmenü",
        'prompt_select_setting': "Wähle eine Option zum Ändern: ",
        'prompt_enter_delays': "Gib die Verzögerungszeiten durch Komma getrennt ein (z.B. 0.5,1.0,2.0): ",
        'error_invalid_delays_format': "Ungültige Eingabe: {}. Einstellungen nicht geändert.",
        'error_delays_must_be_positive': "Alle Verzögerungszeiten müssen >= 0 sein.",
        'setting_delays_set': "Verzögerungszeiten gesetzt auf: {}",
        'prompt_enter_delay_probability': "Gib die Wahrscheinlichkeit für eine Verzögerung zwischen 0 und 1 ein (z.B. 0.1 für 10%): ",
        'error_probability_range': "Wahrscheinlichkeit muss zwischen 0 und 1 liegen.",
        'setting_probability_set': "Wahrscheinlichkeit gesetzt auf: {:.1f}%",
        'prompt_use_threads': "Sollen Threads verwendet werden? (ja/nein): ",
        'setting_threads_enabled': "Multithreading aktiviert.",
        'setting_threads_disabled': "Multithreading deaktiviert.",
        'setting_threads_not_relevant': "Einstellung nur relevant, wenn Multithreading aktiviert ist.",
        'prompt_enter_max_threads': "Gib die maximale Anzahl an Threads ein (aktuell: {}): ",
        'error_threads_must_be_positive': "Anzahl der Threads muss positiv sein.",
        'setting_max_threads_set': "Maximale Threads gesetzt auf: {}",
        'prompt_enter_timeout': "Gib den Timeout-Wert in Sekunden ein (aktuell: {}): ",
        'error_timeout_must_be_positive': "Timeout muss positiv sein.",
        'setting_timeout_set': "Timeout gesetzt auf: {}s",
        'prompt_use_verbose': "Soll die Ausgabe ausführlich sein? (ja/nein): ",
        'setting_verbose_enabled': "Ausführliche Ausgabe aktiviert.",
        'setting_verbose_disabled': "Ausführliche Ausgabe deaktiviert.",
        'setting_returning_to_main': "Zurück zum Hauptmenü.",
        'invalid_input_settings': "Ungültige Eingabe.",
        'yes': "ja",
        'no': "nein",
        # Sprachauswahl
        'language_menu_title': "--- Set Language ---",
        'prompt_select_language': "Wähle eine Sprache / Select a language: ",
        'language_set_to': "Sprache auf {} gesetzt.",
        # Modellauswahl & Suche
        'available_models_title': "--- Verfügbare Kindle-Modelle ---",
        'prompt_enter_model': "Gib die Kindle-Modellbezeichnung ein (z.B. PW5) oder 'exit' zum Abbrechen: ",
        'error_model_invalid': "Ungültige Kindle-Modellbezeichnung. Bitte gib eine der unterstützten Bezeichnungen ein oder 'exit'.",
        'error_no_base_url': "Fehler: Keine Basis-URL für Modell {} definiert.",
        'searching_static_title': "\n--- Suche nach statischer Firmware für {} ---",
        'checking_url': "Prüfe: {}",
        'found_url': "Gefunden: {}",
        'not_found_url_status': "Nicht gefunden: {} (Status: {})",
        'error_accessing_url': "Fehler beim Zugriff auf {}: {} - {}",
        'error_unexpected_return_type': "Unerwarteter Rückgabetyp von check_url für {}: {}",
        'searching_dynamic_title': "\n--- Dynamische Suche für {} ---",
        'prompt_enter_start_version': "Gib die Startversion ein",
        'prompt_enter_end_version': "Gib die Endversion ein",
        'default_version_prompt': " (Standard: {})",
        'using_default_version': "Verwende Standardversion: {}",
        'error_version_format': "Fehler: Ungültiges Versionsformat ({}). Benötigt Major.Minor.Patch. Bitte erneut versuchen oder Enter für Standard drücken.",
        'error_version_negative': "Versionsnummern dürfen nicht negativ sein.",
        'error_start_version_greater': "Fehler: Die Startversion muss kleiner oder gleich der Endversion sein.",
        'search_summary_title': "\nSuche nach Firmware für {}",
        'search_summary_base_url': "Basis-URL: {}",
        'search_summary_pattern': "Muster: {}",
        'search_summary_range': "Bereich: {} bis {}",
        'search_summary_threads': "Threads: {} (Max: {})",
        'search_summary_threads_no': "Threads: Nein",
        'search_summary_timeout': "Timeout: {}s",
        'search_summary_delay': "Verzögerung: {}s (Wahrscheinlichkeit: {:.1f}%)",
        'search_summary_verbose': "Ausführlich: {}",
        'starting_sequential_search': "Starte sequenzielle Suche ({} Versionen)...",
        'starting_threaded_search': "Starte parallele Suche ({} Versionen mit max. {} Threads)...",
        'no_versions_to_check': "Keine Versionen im angegebenen Bereich zu prüfen.",
        'error_invalid_pattern': "\nFehler: Ungültiges Dateinamenmuster '{}'. Überspringe Version {}.",
        'progress_update': "\rFortschritt: {}/{} ({:.2f}%) [{} gefunden]",
        'sequential_search_complete': "\nSequenzielle Suche abgeschlossen.",
        'threaded_search_complete': "\nParallele Suche abgeschlossen.",
        'search_aborted_by_user': "\nSuche durch Benutzer abgebrochen.",
        'error_unexpected_search': "\nUnerwarteter Fehler während der Suche: {}",
        'firmware_found_count': "\nFolgende {} Firmware-Dateien wurden gefunden (sortiert):",
        'firmware_none_found': "\nKeine passenden Firmware-Dateien im angegebenen Versionsbereich gefunden.",
        'search_duration': "\nSuche dauerte {:.2f} Sekunden.",
        'error_incomplete_config': "Fehler: Unvollständige Konfiguration für Modell {} (fehlende 'static_version' oder 'example_filename'/'default_version_range').",
        'derived_pattern_regex': "Abgeleitetes Muster (Regex): {}",
        'derived_pattern_fallback': "Abgeleitetes Muster (Fallback '_'): {}",
        'warning_pattern_generic': "Warnung: Konnte kein klares Muster in '{}' erkennen. Verwende generisches Muster.",
        'warning_invalid_version_format': "Warnung: Ungültiges Versionsformat in '{}' gefunden.",
        'warning_no_version_for_sort': "Warnung: Keine Version in '{}' für die Sortierung gefunden.",
        'error_sorting_list': "\nFehler beim Sortieren der Firmware-Liste: {}",
        # Allgemein
        'error_eof': "\nEOF-Fehler bei Eingabe erkannt. Beende.",
        'error_user_interrupt': "\nBenutzerabbruch erkannt. Beende.",
        'error_user_interrupt_return': "\nBenutzerabbruch erkannt. Kehre zum Hauptmenü zurück.",
        'error_eof_return': "\nEOF-Fehler bei Eingabe erkannt. Kehre zum Hauptmenü zurück.",
        'error_library_missing': "Fehler: Benötigte Bibliothek nicht gefunden: {}. Bitte installiere sie (z.B. 'pip install {}')",
        'no_description': "Keine Beschreibung",
    },
    'en': {
        # Menü
        'main_menu_title': "--- Kindle Firmware Checker Main Menu ---",
        'menu_option_1': "1. Start Firmware Search",
        'menu_option_2': "2. Show Available Kindle Models",
        'menu_option_3': "3. Change Settings",
        'menu_option_4': "4. Set Language",  # Geändert zu 4
        'menu_option_5': "5. Exit Script", # Geändert zu 5
        'prompt_select_option': "Please select an option: ",
        'invalid_input_menu': "Invalid input. Please select one of the options {}.", # Platzhalter für Bereich hinzugefügt
        'script_exiting': "Exiting script.",
        # Einstellungen
        'settings_menu_title': "--- Settings ---",
        'setting_option_1': "1. Possible delay times (current: {})",
        'setting_option_2': "2. Probability for delay (current: {:.1f}%)",
        'setting_option_3': "3. Use multithreading (current: {})",
        'setting_option_4_on': "4. Maximum threads (current: {})",
        'setting_option_4_off': "4. Maximum threads (N/A - Multithreading disabled)",
        'setting_option_5': "5. Request timeout (current: {}s)",
        'setting_option_6': "6. Verbose output (current: {})",
        'setting_option_7': "7. Return to Main Menu",
        'prompt_select_setting': "Select an option to change: ",
        'prompt_enter_delays': "Enter delay times separated by comma (e.g., 0.5,1.0,2.0): ",
        'error_invalid_delays_format': "Invalid input: {}. Settings not changed.",
        'error_delays_must_be_positive': "All delay times must be >= 0.",
        'setting_delays_set': "Delay times set to: {}",
        'prompt_enter_delay_probability': "Enter probability for delay between 0 and 1 (e.g., 0.1 for 10%): ",
        'error_probability_range': "Probability must be between 0 and 1.",
        'setting_probability_set': "Probability set to: {:.1f}%",
        'prompt_use_threads': "Use threads? (yes/no): ",
        'setting_threads_enabled': "Multithreading enabled.",
        'setting_threads_disabled': "Multithreading disabled.",
        'setting_threads_not_relevant': "Setting only relevant when multithreading is enabled.",
        'prompt_enter_max_threads': "Enter the maximum number of threads (current: {}): ",
        'error_threads_must_be_positive': "Number of threads must be positive.",
        'setting_max_threads_set': "Maximum threads set to: {}",
        'prompt_enter_timeout': "Enter the timeout value in seconds (current: {}): ",
        'error_timeout_must_be_positive': "Timeout must be positive.",
        'setting_timeout_set': "Timeout set to: {}s",
        'prompt_use_verbose': "Should the output be verbose? (yes/no): ",
        'setting_verbose_enabled': "Verbose output enabled.",
        'setting_verbose_disabled': "Verbose output disabled.",
        'setting_returning_to_main': "Returning to main menu.",
        'invalid_input_settings': "Invalid input.",
        'yes': "yes",
        'no': "no",
        # Sprachauswahl
        'language_menu_title': "--- Set Language ---",
        'prompt_select_language': "Wähle eine Sprache / Select a language: ",
        'language_set_to': "Language set to {}.",
        # Modellauswahl & Suche
        'available_models_title': "--- Available Kindle Models ---",
        'prompt_enter_model': "Enter the Kindle model identifier (e.g., PW5) or 'exit' to cancel: ",
        'error_model_invalid': "Invalid Kindle model identifier. Please enter one of the supported identifiers or 'exit'.",
        'error_no_base_url': "Error: No base URL defined for model {}.",
        'searching_static_title': "\n--- Searching for static firmware for {} ---",
        'checking_url': "Checking: {}",
        'found_url': "Found: {}",
        'not_found_url_status': "Not found: {} (Status: {})",
        'error_accessing_url': "Error accessing {}: {} - {}",
        'error_unexpected_return_type': "Unexpected return type from check_url for {}: {}",
        'searching_dynamic_title': "\n--- Dynamic search for {} ---",
        'prompt_enter_start_version': "Enter the start version",
        'prompt_enter_end_version': "Enter the end version",
        'default_version_prompt': " (default: {})",
        'using_default_version': "Using default version: {}",
        'error_version_format': "Error: Invalid version format ({}). Requires Major.Minor.Patch. Please try again or press Enter for default.",
        'error_version_negative': "Version numbers cannot be negative.",
        'error_start_version_greater': "Error: Start version must be less than or equal to end version.",
        'search_summary_title': "\nSearching for firmware for {}",
        'search_summary_base_url': "Base URL: {}",
        'search_summary_pattern': "Pattern: {}",
        'search_summary_range': "Range: {} to {}",
        'search_summary_threads': "Threads: {} (Max: {})",
        'search_summary_threads_no': "Threads: No",
        'search_summary_timeout': "Timeout: {}s",
        'search_summary_delay': "Delay: {}s (Probability: {:.1f}%)",
        'search_summary_verbose': "Verbose: {}",
        'starting_sequential_search': "Starting sequential search ({} versions)...",
        'starting_threaded_search': "Starting parallel search ({} versions with max {} threads)...",
        'no_versions_to_check': "No versions to check in the specified range.",
        'error_invalid_pattern': "\nError: Invalid filename pattern '{}'. Skipping version {}.",
        'progress_update': "\rProgress: {}/{} ({:.2f}%) [{} found]",
        'sequential_search_complete': "\nSequential search completed.",
        'threaded_search_complete': "\nParallel search completed.",
        'search_aborted_by_user': "\nSearch aborted by user.",
        'error_unexpected_search': "\nUnexpected error during search: {}",
        'firmware_found_count': "\nThe following {} firmware files were found (sorted):",
        'firmware_none_found': "\nNo matching firmware files found in the specified version range.",
        'search_duration': "\nSearch took {:.2f} seconds.",
        'error_incomplete_config': "Error: Incomplete configuration for model {} (missing 'static_version' or 'example_filename'/'default_version_range').",
        'derived_pattern_regex': "Derived pattern (Regex): {}",
        'derived_pattern_fallback': "Derived pattern (Fallback '_'): {}",
        'warning_pattern_generic': "Warning: Could not detect a clear pattern in '{}'. Using generic pattern.",
        'warning_invalid_version_format': "Warning: Invalid version format found in '{}'.",
        'warning_no_version_for_sort': "Warning: No version found in '{}' for sorting.",
        'error_sorting_list': "\nError sorting firmware list: {}",
        # Allgemein
        'error_eof': "\nEOF error detected on input. Exiting.",
        'error_user_interrupt': "\nUser interrupt detected. Exiting.",
        'error_user_interrupt_return': "\nUser interrupt detected. Returning to main menu.",
        'error_eof_return': "\nEOF error detected on input. Returning to main menu.",
        'error_library_missing': "Error: Required library not found: {}. Please install it (e.g., 'pip install {}')",
        'no_description': "No description",
    }
}

# --- Hilfsfunktionen ---

def get_text(key, lang):
    """Holt den übersetzten Text für einen Schlüssel in der angegebenen Sprache."""
    # Fallback auf Englisch, wenn Sprache nicht existiert oder Schlüssel fehlt
    return TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key, f"<{key}_MISSING>")

def calculate_total_checks(version_range):
    """Berechnet die *genaue* Anzahl der zu prüfenden Versionen."""
    start_major, start_minor, start_patch = version_range[0]
    end_major, end_minor, end_patch = version_range[1]
    total = 0
    max_patch = 25
    max_minor_default = 99

    if start_major > end_major: return 0
    if start_major == end_major and start_minor > end_minor: return 0
    if start_major == end_major and start_minor == end_minor and start_patch > end_patch: return 0

    for major in range(start_major, end_major + 1):
        min_minor_loop = start_minor if major == start_major else 0
        max_minor_loop = end_minor if major == end_major else max_minor_default
        for minor in range(min_minor_loop, max_minor_loop + 1):
            min_patch_loop = start_patch if major == start_major and minor == start_minor else 0
            max_patch_loop = end_patch if major == end_major and minor == end_minor else max_patch
            if min_patch_loop <= max_patch_loop:
                 total += (max_patch_loop - min_patch_loop + 1)
    return total


def check_url(full_url, possible_delays, delay_probability, timeout):
    """
    Führt die Anfrage für eine einzelne URL aus.
    Gibt Dateiname (str), Statuscode (int) oder None (Fehler) zurück.
    Loggt Fehler nach stderr.
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.head(full_url, timeout=timeout, headers=headers, allow_redirects=True)

        if random.random() < delay_probability:
            if possible_delays:
                time.sleep(random.choice(possible_delays))

        if response.status_code == 200:
            return full_url.split("/")[-1]
        else:
            return response.status_code
    except requests.exceptions.RequestException as e:
        # Logge Fehler nur einmal hier
        print(f"\nFehler bei {full_url}: {type(e).__name__} - {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"\nUnerwarteter interner Fehler bei URL {full_url}: {e}", file=sys.stderr)
        return None


def generate_firmware_urls(base_url, filename_pattern, version_range, lang):
    """
    Generator-Funktion, die alle zu prüfenden URLs basierend auf dem Versionsbereich erzeugt.
    """
    start_major, start_minor, start_patch = version_range[0]
    end_major, end_minor, end_patch = version_range[1]
    max_patch_val = 25
    max_minor_default = 99

    if start_major > end_major: return
    if start_major == end_major and start_minor > end_minor: return
    if start_major == end_major and start_minor == end_minor and start_patch > end_patch: return

    for major in range(start_major, end_major + 1):
        min_minor_loop = start_minor if major == start_major else 0
        max_minor_loop = end_minor if major == end_major else max_minor_default
        for minor in range(min_minor_loop, max_minor_loop + 1):
            min_patch_loop = start_patch if major == start_major and minor == start_minor else 0
            max_patch_loop = end_patch if major == end_major and minor == end_minor else max_patch_val
            if min_patch_loop > max_patch_loop: continue
            for patch in range(min_patch_loop, max_patch_loop + 1):
                version = f"{major}.{minor}.{patch}"
                try:
                    test_filename = filename_pattern.replace("*", version)
                    yield f"{base_url}{test_filename}"
                except AttributeError:
                    print(get_text('error_invalid_pattern', lang).format(filename_pattern, version), file=sys.stderr)
                    continue


def extract_version_key(filename, lang):
    """
    Extrahiert ein Versionsobjekt aus einem Dateinamen für die Sortierung.
    """
    match = re.search(r'(\d+\.\d+\.\d+(?:\.\d+)*)', filename)
    if match:
        try:
            return pkg_version.parse(match.group(1))
        except pkg_version.InvalidVersion:
            print(get_text('warning_invalid_version_format', lang).format(filename), file=sys.stderr)
            return pkg_version.parse("0.0.0")
    else:
         print(get_text('warning_no_version_for_sort', lang).format(filename), file=sys.stderr)
         return pkg_version.parse("0.0.0")


def sort_firmwares_by_version(firmware_list, lang):
    """
    Sortiert eine Liste von Firmware-Dateinamen numerisch nach ihrer Version.
    """
    if not firmware_list:
        return []
    try:
        # Verwende eine Lambda-Funktion, um die Sprache an extract_version_key zu übergeben
        firmware_list.sort(key=lambda fname: extract_version_key(fname, lang))
        return firmware_list
    except Exception as e:
        print(get_text('error_sorting_list', lang).format(e), file=sys.stderr)
        return firmware_list

# --- Suchfunktionen ---

def check_firmware_version(base_url, filename_pattern, version_range, settings):
    """
    Überprüft *sequenziell*, ob Firmware-Dateien existieren.
    """
    lang = settings['language']
    verbose = settings['verbose']
    possible_delays = settings['possible_delays']
    delay_probability = settings['delay_probability']
    timeout = settings['timeout']

    found_files = []
    total_checks = calculate_total_checks(version_range)
    if total_checks == 0:
        print(get_text('no_versions_to_check', lang))
        return []
    checks_done = 0

    print(get_text('starting_sequential_search', lang).format(total_checks))

    for full_url in generate_firmware_urls(base_url, filename_pattern, version_range, lang):
        result = check_url(full_url, possible_delays, delay_probability, timeout)
        checks_done += 1
        progress = (checks_done / total_checks) * 100 if total_checks > 0 else 100

        if isinstance(result, str): # Gefunden
            found_files.append(result)
            if not verbose: sys.stdout.write("\r" + " " * 80 + "\r")
            print(get_text('found_url', lang).format(full_url))
            if not verbose:
                 sys.stdout.write(get_text('progress_update', lang).format(checks_done, total_checks, progress, len(found_files)))
                 sys.stdout.flush()
        elif isinstance(result, int): # Nicht gefunden
            if verbose:
                print(get_text('not_found_url_status', lang).format(full_url, result))
            elif not verbose:
                sys.stdout.write(get_text('progress_update', lang).format(checks_done, total_checks, progress, len(found_files)))
                sys.stdout.flush()
        elif result is None: # Fehler
            if not verbose:
                sys.stdout.write(get_text('progress_update', lang).format(checks_done, total_checks, progress, len(found_files)))
                sys.stdout.flush()
        else: # Unerwartet
             if not verbose: sys.stdout.write("\r" + " " * 80 + "\r")
             print(get_text('error_unexpected_return_type', lang).format(full_url, type(result)), file=sys.stderr)
             if not verbose:
                sys.stdout.write(get_text('progress_update', lang).format(checks_done, total_checks, progress, len(found_files)))
                sys.stdout.flush()

    if not verbose:
        sys.stdout.write("\r" + " " * 80 + "\r")
    print(get_text('sequential_search_complete', lang))
    return found_files


def check_firmware_version_threaded(base_url, filename_pattern, version_range, settings):
    """
    Überprüft *parallel* mit Threads, ob Firmware-Dateien existieren.
    """
    lang = settings['language']
    verbose = settings['verbose']
    possible_delays = settings['possible_delays']
    delay_probability = settings['delay_probability']
    timeout = settings['timeout']
    max_threads = settings['max_threads']

    found_files = []
    futures = {}
    total_checks = calculate_total_checks(version_range)
    if total_checks == 0:
        print(get_text('no_versions_to_check', lang))
        return []
    checks_done = 0

    print(get_text('starting_threaded_search', lang).format(total_checks, max_threads))

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        for url in generate_firmware_urls(base_url, filename_pattern, version_range, lang):
            future = executor.submit(check_url, url, possible_delays, delay_probability, timeout)
            futures[future] = url

        for future in as_completed(futures):
            url = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                 print(f"\nFehler beim Abrufen des Ergebnisses für {url}: {exc}", file=sys.stderr) # Bleibt Englisch für Debugging
                 result = None

            checks_done += 1
            progress = (checks_done / total_checks) * 100 if total_checks > 0 else 100

            if isinstance(result, str): # Gefunden
                found_files.append(result)
                if not verbose: sys.stdout.write("\r" + " " * 80 + "\r")
                print(get_text('found_url', lang).format(url))
                if not verbose:
                    sys.stdout.write(get_text('progress_update', lang).format(checks_done, total_checks, progress, len(found_files)))
                    sys.stdout.flush()
            elif isinstance(result, int): # Nicht gefunden
                if verbose:
                    print(get_text('not_found_url_status', lang).format(url, result))
                elif not verbose:
                    sys.stdout.write(get_text('progress_update', lang).format(checks_done, total_checks, progress, len(found_files)))
                    sys.stdout.flush()
            elif result is None: # Fehler
                 if not verbose:
                    sys.stdout.write(get_text('progress_update', lang).format(checks_done, total_checks, progress, len(found_files)))
                    sys.stdout.flush()
            else: # Unerwartet
                 if not verbose: sys.stdout.write("\r" + " " * 80 + "\r")
                 print(get_text('error_unexpected_return_type', lang).format(url, type(result)), file=sys.stderr)
                 if not verbose:
                    sys.stdout.write(get_text('progress_update', lang).format(checks_done, total_checks, progress, len(found_files)))
                    sys.stdout.flush()

    if not verbose:
        sys.stdout.write("\r" + " " * 80 + "\r")
    print(get_text('threaded_search_complete', lang))
    return found_files


# --- UI / Menü Funktionen ---

def display_kindle_models(models, lang):
    """Zeigt die verfügbaren Kindle-Modelle an."""
    print(f"\n{get_text('available_models_title', lang)}")
    try:
        max_len = max(len(key) for key in models.keys()) if models else 10
    except ValueError:
        max_len = 10
    for model_key, data in models.items():
        # Hole die Beschreibung in der aktuellen Sprache, Fallback auf Englisch, dann auf Standardtext
        description = data.get('description', {}).get(lang,
                      data.get('description', {}).get('en', get_text('no_description', lang)))
        print(f"- {model_key:<{max_len}} : {description}")
    print("-" * (max_len + 20))


def get_version_input(prompt_key, default_version_tuple, lang):
    """
    Fragt den Benutzer nach einer Version im Format M.m.p und validiert sie.
    """
    prompt_text = get_text(prompt_key, lang)
    default_version_str = ".".join(map(str, default_version_tuple))
    prompt_full = f"{prompt_text}{get_text('default_version_prompt', lang).format(default_version_str)}: "

    while True:
        try:
            version_input = input(prompt_full)
            if not version_input:
                 print(get_text('using_default_version', lang).format(default_version_str))
                 return default_version_tuple
            try:
                parsed_version = pkg_version.parse(version_input)
                version_parts = parsed_version.release[:3]
                while len(version_parts) < 3: version_parts += (0,)
                if any(v < 0 for v in version_parts):
                     raise ValueError(get_text('error_version_negative', lang))
                return version_parts
            except (ValueError, pkg_version.InvalidVersion) as e:
                print(get_text('error_version_format', lang).format(e))
        except EOFError:
            print(get_text('error_eof', lang))
            sys.exit(1)
        except KeyboardInterrupt:
             print(get_text('error_user_interrupt', lang))
             sys.exit(0)


def get_filename_pattern_simple(example_filename, lang):
    """
    Versucht, das Versionsmuster (*) aus einem Beispiel-Dateinamen zu extrahieren.
    """
    if not example_filename or '.' not in example_filename:
        print(get_text('warning_pattern_generic', lang).format(example_filename), file=sys.stderr)
        return "update_kindle_*.bin"

    match = re.search(r'^(.*?)(\d+\.\d+\.\d+(?:\.\d+)*)((?:_[a-zA-Z0-9]+)*?)(\.\w+)$', example_filename)
    if match:
        prefix = match.group(1)
        suffix_after_version = match.group(3)
        extension = match.group(4)
        pattern = f"{prefix}*{suffix_after_version}{extension}"
        print(get_text('derived_pattern_regex', lang).format(pattern))
        return pattern
    else:
        base, ext = os.path.splitext(example_filename)
        parts = base.split('_')
        if len(parts) > 1:
            prefix = "_".join(parts[:-1]) + "_"
            pattern = prefix + "*" + ext
            print(get_text('derived_pattern_fallback', lang).format(pattern))
            return pattern
        else:
            print(get_text('warning_pattern_generic', lang).format(example_filename), file=sys.stderr)
            return "update_kindle_*.bin"


def start_search(kindle_models, settings):
    """
    Startet die Firmware-Suche basierend auf der Benutzerauswahl und den Einstellungen.
    """
    lang = settings['language']
    while True:
        display_kindle_models(kindle_models, lang)
        try:
            kindle_input = input(get_text('prompt_enter_model', lang)).upper()
        except EOFError:
            print(get_text('error_eof_return', lang))
            return
        except KeyboardInterrupt:
            print(get_text('error_user_interrupt_return', lang))
            return

        if kindle_input == "EXIT":
            return
        elif kindle_input in kindle_models:
            selected_model = kindle_models[kindle_input]
            base_url = selected_model.get("base_url")
            example_filename = selected_model.get("example_filename")
            default_version_range = selected_model.get("default_version_range")
            static_version_filename = selected_model.get("static_version")

            if not base_url:
                print(get_text('error_no_base_url', lang).format(kindle_input), file=sys.stderr)
                continue

            if not base_url.endswith('/'): base_url += '/'

            if static_version_filename:
                print(get_text('searching_static_title', lang).format(kindle_input))
                print(get_text('checking_url', lang).format(static_version_filename))
                full_url = f"{base_url}{static_version_filename}"
                result = check_url(full_url, settings['possible_delays'], settings['delay_probability'], settings['timeout'])

                if isinstance(result, str):
                    print(get_text('found_url', lang).format(full_url))
                elif isinstance(result, int):
                     print(get_text('not_found_url_status', lang).format(full_url, result))
                elif result is None: pass # Fehler wurde schon geloggt
                else:
                     print(get_text('error_unexpected_return_type', lang).format(full_url, type(result)), file=sys.stderr)
                print("-" * 30)
                continue

            elif example_filename and default_version_range:
                filename_pattern = get_filename_pattern_simple(example_filename, lang)
                print(get_text('searching_dynamic_title', lang).format(kindle_input))
                start_version = get_version_input('prompt_enter_start_version', default_version_range[0], lang)
                end_version = get_version_input('prompt_enter_end_version', default_version_range[1], lang)

                if start_version > end_version:
                    print(get_text('error_start_version_greater', lang), file=sys.stderr)
                    continue

                print(get_text('search_summary_title', lang).format(kindle_input))
                print(get_text('search_summary_base_url', lang).format(base_url))
                print(get_text('search_summary_pattern', lang).format(filename_pattern))
                print(get_text('search_summary_range', lang).format('.'.join(map(str, start_version)), '.'.join(map(str, end_version))))
                if settings['use_threads']:
                    print(get_text('search_summary_threads', lang).format(get_text('yes', lang), settings['max_threads']))
                else:
                    print(get_text('search_summary_threads_no', lang).format(get_text('no', lang)))
                print(get_text('search_summary_timeout', lang).format(settings['timeout']))
                print(get_text('search_summary_delay', lang).format(settings['possible_delays'], settings['delay_probability'] * 100))
                print(get_text('search_summary_verbose', lang).format(get_text('yes', lang) if settings['verbose'] else get_text('no', lang)))
                print("-" * 30)

                version_range_to_search = (start_version, end_version)
                start_time = time.time()
                found_firmwares = []
                try:
                    if settings['use_threads']:
                        found_firmwares = check_firmware_version_threaded(base_url, filename_pattern, version_range_to_search, settings)
                    else:
                        found_firmwares = check_firmware_version(base_url, filename_pattern, version_range_to_search, settings)
                except KeyboardInterrupt:
                     print(get_text('search_aborted_by_user', lang))
                except Exception as e:
                     print(get_text('error_unexpected_search', lang).format(e), file=sys.stderr)
                end_time = time.time()
                print("-" * 30)

                if found_firmwares:
                    sorted_firmwares = sort_firmwares_by_version(found_firmwares, lang)
                    print(get_text('firmware_found_count', lang).format(len(sorted_firmwares)))
                    for file in sorted_firmwares: print(f"- {file}")
                else:
                    print(get_text('firmware_none_found', lang))
                print(get_text('search_duration', lang).format(end_time - start_time))
                print("-" * 30)
            else:
                 if not static_version_filename:
                     print(get_text('error_incomplete_config', lang).format(kindle_input), file=sys.stderr)
                 print("-" * 30)
                 continue
        else:
            print(get_text('error_model_invalid', lang))
            print("-" * 30)


def configure_settings(settings):
    """
    Lässt den Benutzer die Skripteinstellungen ändern.
    """
    lang = settings['language']
    yes_str = get_text('yes', lang)
    no_str = get_text('no', lang)

    while True:
        print(f"\n{get_text('settings_menu_title', lang)}")
        print(get_text('setting_option_1', lang).format(settings['possible_delays']))
        print(get_text('setting_option_2', lang).format(settings['delay_probability'] * 100))
        print(get_text('setting_option_3', lang).format(yes_str if settings['use_threads'] else no_str))
        if settings['use_threads']:
            print(get_text('setting_option_4_on', lang).format(settings['max_threads']))
        else:
             print(get_text('setting_option_4_off', lang))
        print(get_text('setting_option_5', lang).format(settings['timeout']))
        print(get_text('setting_option_6', lang).format(yes_str if settings['verbose'] else no_str))
        print(get_text('setting_option_7', lang))
        print("-" * 30)

        try:
            choice = input(get_text('prompt_select_setting', lang))

            if choice == "1":
                delays_input = input(get_text('prompt_enter_delays', lang))
                try:
                    if not delays_input.strip(): new_delays = []
                    else: new_delays = [float(delay.strip()) for delay in delays_input.split(",") if delay.strip()]
                    if not all(delay >= 0 for delay in new_delays): raise ValueError(get_text('error_delays_must_be_positive', lang))
                    settings['possible_delays'] = new_delays
                    print(get_text('setting_delays_set', lang).format(settings['possible_delays']))
                except ValueError as e:
                    print(get_text('error_invalid_delays_format', lang).format(e), file=sys.stderr)
            elif choice == "2":
                prob_input = input(get_text('prompt_enter_delay_probability', lang))
                try:
                    new_prob = float(prob_input)
                    if not 0 <= new_prob <= 1: raise ValueError(get_text('error_probability_range', lang))
                    settings['delay_probability'] = new_prob
                    print(get_text('setting_probability_set', lang).format(settings['delay_probability'] * 100))
                except ValueError as e:
                    print(get_text('error_invalid_delays_format', lang).format(e), file=sys.stderr)
            elif choice == "3":
                threads_input = input(get_text('prompt_use_threads', lang)).lower()
                if threads_input == yes_str.lower():
                    settings['use_threads'] = True; print(get_text('setting_threads_enabled', lang))
                elif threads_input == no_str.lower():
                    settings['use_threads'] = False; print(get_text('setting_threads_disabled', lang))
                else: print(get_text('invalid_input_settings', lang))
            elif choice == "4":
                if not settings['use_threads']:
                    print(get_text('setting_threads_not_relevant', lang)); continue
                threads_input = input(get_text('prompt_enter_max_threads', lang).format(settings['max_threads']))
                try:
                    new_max_threads = int(threads_input)
                    if new_max_threads <= 0: raise ValueError(get_text('error_threads_must_be_positive', lang))
                    settings['max_threads'] = new_max_threads
                    print(get_text('setting_max_threads_set', lang).format(settings['max_threads']))
                except ValueError as e:
                    print(get_text('error_invalid_delays_format', lang).format(e), file=sys.stderr)
            elif choice == "5":
                timeout_input = input(get_text('prompt_enter_timeout', lang).format(settings['timeout']))
                try:
                    new_timeout = int(timeout_input)
                    if new_timeout <= 0: raise ValueError(get_text('error_timeout_must_be_positive', lang))
                    settings['timeout'] = new_timeout
                    print(get_text('setting_timeout_set', lang).format(settings['timeout']))
                except ValueError as e:
                    print(get_text('error_invalid_delays_format', lang).format(e), file=sys.stderr)
            elif choice == "6":
                verbose_input = input(get_text('prompt_use_verbose', lang)).lower()
                if verbose_input == yes_str.lower():
                    settings['verbose'] = True; print(get_text('setting_verbose_enabled', lang))
                elif verbose_input == no_str.lower():
                    settings['verbose'] = False; print(get_text('setting_verbose_disabled', lang))
                else: print(get_text('invalid_input_settings', lang))
            elif choice == "7":
                print(get_text('setting_returning_to_main', lang)); break
            else: print(get_text('invalid_input_settings', lang))
        except EOFError:
            print(get_text('error_eof_return', lang)); break
        except KeyboardInterrupt:
             print(get_text('error_user_interrupt_return', lang)); break
    return settings

def select_language(settings):
    """Lässt den Benutzer die Sprache auswählen."""
    print(f"\n{get_text('language_menu_title', settings['language'])}") # Titel in aktueller Sprache
    # Sprachen immer gleich anzeigen
    print("1. Deutsch")
    print("2. English")
    print("-" * 30)
    while True:
        try:
            choice = input(get_text('prompt_select_language', settings['language'])) # Prompt in aktueller Sprache
            if choice == "1":
                settings['language'] = 'de'
                print(get_text('language_set_to', 'de').format("Deutsch"))
                break
            elif choice == "2":
                settings['language'] = 'en'
                print(get_text('language_set_to', 'en').format("English"))
                break
            else:
                # Fehlermeldung in beiden Sprachen anzeigen, da unklar ist, welche der User versteht
                print(f"{get_text('invalid_input_settings', 'de')} / {get_text('invalid_input_settings', 'en')}")
        except EOFError:
            print(get_text('error_eof_return', settings['language'])); break # Zurück zum Menü
        except KeyboardInterrupt:
             print(get_text('error_user_interrupt_return', settings['language'])); break # Zurück zum Menü
    return settings


def main():
    """Hauptfunktion des Skripts, die das Menü steuert."""
    # Kindle Modelldaten mit übersetzten Beschreibungen
    kindle_models = {
        "K5": {"description": {"de": "Kindle 5 (Touch)", "en": "Kindle 5 (Touch)"}, "base_url": "https://s3.amazonaws.com/G7G_FirmwareUpdates_WebDownloads/", "example_filename": "update_kindle_5.6.1.1.bin", "default_version_range": ((5, 3, 0), (5, 6, 25))},
        "K4": {"description": {"de": "Kindle 4 (ohne Touch, Silber/Graphit)", "en": "Kindle 4 (Non-Touch, Silver/Graphite)"}, "base_url": "https://s3.amazonaws.com/firmwareupdates/", "static_version": "update_kindle_4.1.4.bin"},
        "K4B": {"description": {"de": "Kindle 4 (ohne Touch, Schwarz)", "en": "Kindle 4 (Non-Touch, Black)"}, "base_url": "https://s3.amazonaws.com/firmwareupdates/", "static_version": "update_kindle_4.1.4.bin"},
        "PW": {"description": {"de": "Kindle Paperwhite 1 (2012)", "en": "Kindle Paperwhite 1 (2012)"}, "base_url": "https://s3.amazonaws.com/G7G_FirmwareUpdates_WebDownloads/", "example_filename": "update_kindle_5.6.1.1.bin", "default_version_range": ((5, 0, 0), (5, 6, 25))},
        "PW2": {"description": {"de": "Kindle Paperwhite 2 (2013)", "en": "Kindle Paperwhite 2 (2013)"}, "base_url": "https://s3.amazonaws.com/firmwaredownloads/", "example_filename": "update_kindle_paperwhite_v2_5.12.2.2.bin", "default_version_range": ((5, 4, 0), (5, 12, 25))},
        "KT2": {"description": {"de": "Kindle 7 (Basis, 2014)", "en": "Kindle 7 (Basic, 2014)"}, "base_url": "https://s3.amazonaws.com/firmwaredownloads/", "example_filename": "update_kindle_5.12.2.2.bin", "default_version_range": ((5, 6, 0), (5, 12, 25))},
        "KV": {"description": {"de": "Kindle Voyage (2014)", "en": "Kindle Voyage (2014)"}, "base_url": "https://s3.amazonaws.com/firmwaredownloads/", "static_version": "update_kindle_voyage_5.13.7.0.1.bin"},
        "PW3": {"description": {"de": "Kindle Paperwhite 3 (2015)", "en": "Kindle Paperwhite 3 (2015)"}, "base_url": "https://s3.amazonaws.com/firmwaredownloads/", "example_filename": "update_kindle_all_new_paperwhite_5.15.1.1.bin", "default_version_range": ((5, 7, 0), (5, 15, 25))},
        "KOA1": {"description": {"de": "Kindle Oasis 1 (2016)", "en": "Kindle Oasis 1 (2016)"}, "base_url": "https://s3.amazonaws.com/firmwaredownloads/", "example_filename": "update_kindle_oasis_5.15.1.1.bin", "default_version_range": ((5, 8, 0), (5, 15, 25))},
        "KT3": {"description": {"de": "Kindle 8 (Basis, 2016)", "en": "Kindle 8 (Basic, 2016)"}, "base_url": "https://s3.amazonaws.com/firmwaredownloads/", "example_filename": "update_kindle_8th_5.15.1.1.bin", "default_version_range": ((5, 8, 0), (5, 15, 25))},
        "KOA2": {"description": {"de": "Kindle Oasis 2 (2017)", "en": "Kindle Oasis 2 (2017)"}, "base_url": "https://s3.amazonaws.com/firmwaredownloads/", "example_filename": "update_kindle_all_new_oasis_5.16.2.1.1.bin", "default_version_range": ((5, 9, 0), (5, 16, 25))},
        "PW4": {"description": {"de": "Kindle Paperwhite 4 (2018)", "en": "Kindle Paperwhite 4 (2018)"}, "base_url": "https://s3.amazonaws.com/firmwaredownloads/", "example_filename": "update_kindle_paperwhite_10th_5.16.2.1.1.bin", "default_version_range": ((5, 10, 0), (5, 16, 25))},
        "KT4": {"description": {"de": "Kindle 10 (Basis, 2019)", "en": "Kindle 10 (Basic, 2019)"}, "base_url": "https://s3.amazonaws.com/firmwaredownloads/", "example_filename": "update_kindle_10th_5.16.2.1.1.bin", "default_version_range": ((5, 11, 0), (5, 16, 25))},
        "KOA3": {"description": {"de": "Kindle Oasis 3 (2019)", "en": "Kindle Oasis 3 (2019)"}, "base_url": "https://s3.amazonaws.com/firmwaredownloads/", "example_filename": "update_kindle_oasis_10th_5.16.2.1.1.bin", "default_version_range": ((5, 12, 0), (5, 16, 25))},
        "PW5": {"description": {"de": "Kindle Paperwhite 5 (11. Gen, 2021)", "en": "Kindle Paperwhite 5 (11th Gen, 2021)"}, "base_url": "https://s3.amazonaws.com/firmwaredownloads/", "example_filename": "update_kindle_all_new_paperwhite_11th_5.16.8.bin", "default_version_range": ((5, 14, 0), (5, 17, 25))},
        "PW5SE": {"description": {"de": "Kindle Paperwhite 5 SE (11. Gen, 2021)", "en": "Kindle Paperwhite 5 Signature Edition (11th Gen, 2021)"}, "base_url": "https://s3.amazonaws.com/firmwaredownloads/", "example_filename": "update_kindle_all_new_paperwhite_11th_5.16.8.bin", "default_version_range": ((5, 14, 0), (5, 17, 25))},
        "K11": {"description": {"de": "Kindle 11 (Basis, 2022)", "en": "Kindle 11 (Basic, 2022)"}, "base_url": "https://s3.amazonaws.com/firmwaredownloads/", "example_filename": "update_kindle_11th_5.16.8.bin", "default_version_range": ((5, 15, 0), (5, 17, 25))},
        "Scribe": {"description": {"de": "Kindle Scribe (2022)", "en": "Kindle Scribe (2022)"}, "base_url": "https://s3.amazonaws.com/firmwaredownloads/", "example_filename": "update_kindle_scribe_5.16.8.bin", "default_version_range": ((5, 16, 0), (5, 17, 25))},
    }

    settings = {
        'language': DEFAULT_LANGUAGE, # Starte mit Deutsch
        'possible_delays': DEFAULT_DELAYS,
        'use_threads': True,
        'delay_probability': DEFAULT_DELAY_PROBABILITY,
        'timeout': DEFAULT_TIMEOUT,
        'verbose': DEFAULT_VERBOSE,
        'max_threads': DEFAULT_MAX_THREADS
    }

    while True:
        lang = settings['language'] # Aktuelle Sprache für Menü holen
        print(f"\n{get_text('main_menu_title', lang)}")
        print(get_text('menu_option_1', lang))
        print(get_text('menu_option_2', lang))
        print(get_text('menu_option_3', lang))
        # Option 4 ist jetzt "Set Language"
        print(get_text('menu_option_4', 'en')) # Zeige "Set Language" immer gleich an
        # Option 5 ist jetzt "Skript beenden"
        print(get_text('menu_option_5', lang))
        print("-" * 30)

        try:
            choice = input(get_text('prompt_select_option', lang))
        except EOFError:
            print(get_text('error_eof', lang)); break
        except KeyboardInterrupt:
             print(get_text('error_user_interrupt', lang)); break

        if choice == "1":
            start_search(kindle_models, settings)
        elif choice == "2":
            display_kindle_models(kindle_models, lang)
        elif choice == "3":
            settings = configure_settings(settings)
        elif choice == "4": # Geändert zu Sprachauswahl
            settings = select_language(settings)
        elif choice == "5": # Geändert zu Beenden
            print(get_text('script_exiting', lang)); break
        else:
            # Korrekter Bereich für die Fehlermeldung
            print(get_text('invalid_input_menu', lang).format("1-5"))

if __name__ == "__main__":
    # Überprüfe Abhängigkeiten
    missing_libs = []
    try: import requests
    except ImportError: missing_libs.append("'requests'")
    try: from packaging import version as pkg_version
    except ImportError: missing_libs.append("'packaging'")

    if missing_libs:
        # Versuche, die Fehlermeldung in der Standardsprache auszugeben
        lang = DEFAULT_LANGUAGE
        lib_str = " and ".join(missing_libs)
        pip_str = " ".join(lib.strip("'") for lib in missing_libs)
        print(get_text('error_library_missing', lang).format(lib_str, pip_str), file=sys.stderr)
        sys.exit(1)

    main()
