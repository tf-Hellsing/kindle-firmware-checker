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
DEFAULT_MAX_THREADS = 5 # Standardwert für Threads auf 5 reduziert
DEFAULT_DELAY_PROBABILITY = 0.1
DEFAULT_DELAYS = [0.5, 1.0, 1.5, 2.0, 2.5] # Standardverzögerungen etwas reduziert
DEFAULT_VERBOSE = False # Standardmäßig nicht ausführlich

# --- Hilfsfunktionen ---

def calculate_total_checks(version_range):
    """Berechnet die *genaue* Anzahl der zu prüfenden Versionen."""
    start_major, start_minor, start_patch = version_range[0]
    end_major, end_minor, end_patch = version_range[1]
    total = 0
    max_patch = 25 # Patch geht von 0 bis 25 (insgesamt 26 Werte)
    max_minor_default = 99 # Standard-Maximum für Minor, wenn nicht im Endbereich

    # Prüfe auf ungültigen Bereich
    if start_major > end_major:
        return 0
    if start_major == end_major and start_minor > end_minor:
        return 0
    if start_major == end_major and start_minor == end_minor and start_patch > end_patch:
        return 0

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
    Führt die Anfrage für eine einzelne URL aus und gibt den Dateinamen oder einen Fehler zurück.
    Gibt bei Fehlern None zurück und loggt den Fehler nach stderr.

    Args:
        full_url (str): Die URL, die überprüft werden soll.
        possible_delays (list): Die Liste der möglichen Verzögerungszeiten.
        delay_probability (float): Die Wahrscheinlichkeit (0 bis 1) für eine Verzögerung.
        timeout (int): Timeout für die Anfrage.

    Returns:
        str: Der Dateiname, wenn die URL gefunden wird (Status 200).
        int: Der HTTP-Statuscode, wenn die Datei nicht gefunden wird (nicht 200).
        None: Wenn ein Request-Fehler auftritt (Timeout, ConnectionError etc.).
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
        # Logge den Fehler nach stderr und gib None zurück
        print(f"\nFehler bei {full_url}: {type(e).__name__} - {e}", file=sys.stderr)
        return None
    except Exception as e:
        # Fange andere unerwartete Fehler ab
        print(f"\nUnerwarteter interner Fehler bei URL {full_url}: {e}", file=sys.stderr)
        return None


def generate_firmware_urls(base_url, filename_pattern, version_range):
    """
    Generator-Funktion, die alle zu prüfenden URLs basierend auf dem Versionsbereich erzeugt.

    Args:
        base_url (str): Die Basis-URL.
        filename_pattern (str): Das Muster des Dateinamens (z.B. "update_*.bin").
        version_range (tuple): Ein Tupel mit der Start- und Endversion.

    Yields:
        str: Die vollständige URL zum Überprüfen.
    """
    start_major, start_minor, start_patch = version_range[0]
    end_major, end_minor, end_patch = version_range[1]
    max_patch_val = 25
    max_minor_default = 99

    # Prüfe auf ungültigen Bereich (redundant zu calculate_total_checks, aber sicher ist sicher)
    if start_major > end_major: return
    if start_major == end_major and start_minor > end_minor: return
    if start_major == end_major and start_minor == end_minor and start_patch > end_patch: return

    for major in range(start_major, end_major + 1):
        min_minor_loop = start_minor if major == start_major else 0
        max_minor_loop = end_minor if major == end_major else max_minor_default

        for minor in range(min_minor_loop, max_minor_loop + 1):
            min_patch_loop = start_patch if major == start_major and minor == start_minor else 0
            max_patch_loop = end_patch if major == end_major and minor == end_minor else max_patch_val

            if min_patch_loop > max_patch_loop:
                continue

            for patch in range(min_patch_loop, max_patch_loop + 1):
                version = f"{major}.{minor}.{patch}"
                try:
                    test_filename = filename_pattern.replace("*", version)
                    yield f"{base_url}{test_filename}"
                except AttributeError:
                    print(f"\nFehler: Ungültiges Dateinamenmuster '{filename_pattern}'. Überspringe Version {version}.", file=sys.stderr)
                    continue # Zum nächsten Patch springen


def extract_version_key(filename):
    """
    Extrahiert ein Versionsobjekt aus einem Dateinamen für die Sortierung.
    Verwendet eine Regex, um Versionsnummern wie X.Y.Z oder X.Y.Z.A zu finden.
    Gibt ein niedriges Versionsobjekt zurück, wenn keine Version gefunden wird.
    """
    # Versucht, die Version zu extrahieren (angepasste Regex)
    match = re.search(r'(\d+\.\d+\.\d+(?:\.\d+)*)', filename)
    if match:
        try:
            # Verwende packaging.version für robustes Parsen und Vergleichen
            return pkg_version.parse(match.group(1))
        except pkg_version.InvalidVersion:
            # Fallback, wenn das Parsen fehlschlägt
            print(f"Warnung: Ungültiges Versionsformat in '{filename}' gefunden.", file=sys.stderr)
            return pkg_version.parse("0.0.0") # Gib eine niedrige Version für die Sortierung zurück
    else:
        # Fallback, wenn keine Version gefunden wird
         print(f"Warnung: Keine Version in '{filename}' für die Sortierung gefunden.", file=sys.stderr)
         return pkg_version.parse("0.0.0")


def sort_firmwares_by_version(firmware_list):
    """
    Sortiert eine Liste von Firmware-Dateinamen numerisch nach ihrer Version.
    """
    if not firmware_list:
        return []

    # Sortiere die Liste mithilfe des extrahierten Versionsobjekts als Schlüssel
    try:
        firmware_list.sort(key=extract_version_key)
        return firmware_list
    except Exception as e:
        print(f"\nFehler beim Sortieren der Firmware-Liste: {e}", file=sys.stderr)
        # Gib die unsortierte Liste im Fehlerfall zurück
        return firmware_list

# --- Suchfunktionen ---

def check_firmware_version(base_url, filename_pattern, version_range, possible_delays, delay_probability, timeout=DEFAULT_TIMEOUT, verbose=DEFAULT_VERBOSE):
    """
    Überprüft *sequenziell*, ob Firmware-Dateien existieren.
    Verwendet jetzt den URL-Generator.
    """
    found_files = []
    total_checks = calculate_total_checks(version_range)
    if total_checks == 0:
        print("Keine Versionen im angegebenen Bereich zu prüfen.")
        return []
    checks_done = 0

    print(f"Starte sequenzielle Suche ({total_checks} Versionen)...")

    # Verwende den Generator, um URLs zu erhalten
    for full_url in generate_firmware_urls(base_url, filename_pattern, version_range):
        # check_url gibt Dateiname (str), Statuscode (int) oder None (Fehler) zurück
        result = check_url(full_url, possible_delays, delay_probability, timeout)
        checks_done += 1
        progress = (checks_done / total_checks) * 100 if total_checks > 0 else 100

        # Ausgabe basierend auf dem Ergebnis und Verbose-Einstellung
        if isinstance(result, str): # Datei gefunden (Status 200)
            found_files.append(result)
            # Lösche Fortschrittszeile nur, wenn nicht verbose
            if not verbose: sys.stdout.write("\r" + " " * 80 + "\r")
            print(f"Gefunden: {full_url}")
            if not verbose:
                 sys.stdout.write(f"\rFortschritt: {checks_done}/{total_checks} ({progress:.2f}%) [{len(found_files)} gefunden]")
                 sys.stdout.flush()
        elif isinstance(result, int): # Datei nicht gefunden (anderer Statuscode)
            if verbose:
                # Im Verbose-Modus keine Fortschrittszeile, nur die Meldung
                print(f"Nicht gefunden: {full_url} (Status: {result})")
            elif not verbose: # Nur Fortschritt aktualisieren
                sys.stdout.write(f"\rFortschritt: {checks_done}/{total_checks} ({progress:.2f}%) [{len(found_files)} gefunden]")
                sys.stdout.flush()
        elif result is None: # Fehler (Timeout, ConnectionError etc.) - Fehler wurde bereits in check_url geloggt
            if verbose:
                 # Im Verbose-Modus wurde der Fehler bereits ausgegeben.
                 pass
            elif not verbose: # Nur Fortschritt aktualisieren
                sys.stdout.write(f"\rFortschritt: {checks_done}/{total_checks} ({progress:.2f}%) [{len(found_files)} gefunden]")
                sys.stdout.flush()
        else: # Unerwarteter Rückgabetyp von check_url
             if not verbose: sys.stdout.write("\r" + " " * 80 + "\r")
             print(f"Unerwarteter Rückgabetyp von check_url für {full_url}: {type(result)}", file=sys.stderr)
             if not verbose:
                sys.stdout.write(f"\rFortschritt: {checks_done}/{total_checks} ({progress:.2f}%) [{len(found_files)} gefunden]")
                sys.stdout.flush()


    # Abschluss der Suche
    if not verbose:
        sys.stdout.write("\r" + " " * 80 + "\r") # Letzte Fortschrittszeile löschen
    print("\nSequenzielle Suche abgeschlossen.")
    return found_files


def check_firmware_version_threaded(base_url, filename_pattern, version_range, possible_delays, delay_probability, timeout=DEFAULT_TIMEOUT, max_threads=DEFAULT_MAX_THREADS, verbose=DEFAULT_VERBOSE):
    """
    Überprüft *parallel* mit Threads, ob Firmware-Dateien existieren.
    Verwendet jetzt den URL-Generator.
    """
    found_files = []
    futures = {} # Dictionary verwenden: {future: url}
    total_checks = calculate_total_checks(version_range)
    if total_checks == 0:
        print("Keine Versionen im angegebenen Bereich zu prüfen.")
        return []
    checks_done = 0
    actual_max_threads = max_threads

    print(f"Starte parallele Suche ({total_checks} Versionen mit max. {actual_max_threads} Threads)...")

    with ThreadPoolExecutor(max_workers=actual_max_threads) as executor:
        # Tasks übergeben mithilfe des Generators
        for url in generate_firmware_urls(base_url, filename_pattern, version_range):
            future = executor.submit(check_url, url, possible_delays, delay_probability, timeout)
            futures[future] = url

        # Ergebnisse verarbeiten
        for future in as_completed(futures):
            url = futures[future]
            try:
                # Ergebnis holen: Dateiname (str), Statuscode (int) oder None (Fehler)
                result = future.result()
            except Exception as exc:
                 # Fehler beim Holen des Results (sollte selten sein, da check_url Exceptions fängt)
                 print(f"\nFehler beim Abrufen des Ergebnisses für {url}: {exc}", file=sys.stderr)
                 result = None # Behandle als Fehler

            checks_done += 1
            progress = (checks_done / total_checks) * 100 if total_checks > 0 else 100

            # Ausgabe basierend auf dem Ergebnis und Verbose-Einstellung
            if isinstance(result, str): # Datei gefunden (Status 200)
                found_files.append(result)
                if not verbose: sys.stdout.write("\r" + " " * 80 + "\r")
                print(f"Gefunden: {url}")
                if not verbose:
                    sys.stdout.write(f"\rFortschritt: {checks_done}/{total_checks} ({progress:.2f}%) [{len(found_files)} gefunden]")
                    sys.stdout.flush()
            elif isinstance(result, int): # Datei nicht gefunden (anderer Statuscode)
                if verbose:
                    print(f"Nicht gefunden: {url} (Status: {result})")
                elif not verbose: # Nur Fortschritt aktualisieren
                    sys.stdout.write(f"\rFortschritt: {checks_done}/{total_checks} ({progress:.2f}%) [{len(found_files)} gefunden]")
                    sys.stdout.flush()
            elif result is None: # Fehler (Timeout, ConnectionError etc.) - Fehler wurde bereits in check_url geloggt
                if verbose:
                     pass # Fehler wurde schon geloggt
                elif not verbose: # Nur Fortschritt aktualisieren
                    sys.stdout.write(f"\rFortschritt: {checks_done}/{total_checks} ({progress:.2f}%) [{len(found_files)} gefunden]")
                    sys.stdout.flush()
            else: # Unerwarteter Rückgabetyp
                 if not verbose: sys.stdout.write("\r" + " " * 80 + "\r")
                 print(f"Unerwarteter Rückgabetyp von check_url für {url}: {type(result)}", file=sys.stderr)
                 if not verbose:
                    sys.stdout.write(f"\rFortschritt: {checks_done}/{total_checks} ({progress:.2f}%) [{len(found_files)} gefunden]")
                    sys.stdout.flush()


    # Abschluss der Suche
    if not verbose:
        sys.stdout.write("\r" + " " * 80 + "\r") # Letzte Fortschrittszeile löschen
    print("\nParallele Suche abgeschlossen.")

    return found_files


# --- UI / Menü Funktionen ---

def display_kindle_models(models):
    """Zeigt die verfügbaren Kindle-Modelle an."""
    print("\n--- Verfügbare Kindle-Modelle ---")
    try:
        max_len = max(len(key) for key in models.keys()) if models else 10
    except ValueError:
        max_len = 10
    for model_key, data in models.items():
        print(f"- {model_key:<{max_len}} : {data.get('description', 'Keine Beschreibung')}")
    print("-" * (max_len + 20))


def get_version_input(prompt, default_version_tuple):
    """
    Fragt den Benutzer nach einer Version im Format M.m.p und validiert sie.
    Gibt bei ungültiger Eingabe die Standardversion zurück.
    Fängt EOFError/KeyboardInterrupt ab.
    """
    default_version_str = ".".join(map(str, default_version_tuple))
    while True:
        try:
            version_input = input(f"{prompt} (Standard: {default_version_str}): ")
            if not version_input:
                 print(f"Verwende Standardversion: {default_version_str}")
                 return default_version_tuple
            try:
                # Versuche, mit packaging.version zu parsen, um mehr Formate zu erlauben
                parsed_version = pkg_version.parse(version_input)
                # Extrahiere die ersten drei Teile (Major, Minor, Patch)
                version_parts = parsed_version.release[:3]
                # Fülle mit Nullen auf, falls weniger als 3 Teile vorhanden sind
                while len(version_parts) < 3:
                    version_parts += (0,)
                # Stelle sicher, dass alle Teile nicht negativ sind
                if any(v < 0 for v in version_parts):
                     raise ValueError("Versionsnummern dürfen nicht negativ sein.")
                return version_parts
            except (ValueError, pkg_version.InvalidVersion) as e:
                print(f"Fehler: Ungültiges Versionsformat ({e}). Benötigt Major.Minor.Patch. Bitte erneut versuchen oder Enter für Standard drücken.")
        except EOFError:
            print("\nEOF-Fehler bei Eingabe erkannt. Beende.")
            sys.exit(1)
        except KeyboardInterrupt:
             print("\nBenutzerabbruch erkannt. Beende.")
             sys.exit(0)


def get_filename_pattern_simple(example_filename):
    """
    Versucht, das Versionsmuster (*) aus einem Beispiel-Dateinamen zu extrahieren.
    Sucht nach typischen Versionsmustern (X.Y.Z oder X.Y.Z.A).
    """
    if not example_filename or '.' not in example_filename:
        print(f"Warnung: Ungültiger Beispiel-Dateiname '{example_filename}'. Verwende generisches Muster.", file=sys.stderr)
        return "update_kindle_*.bin"

    # Verbesserte Regex, um die Version (mindestens M.m.p) zu finden,
    # auch wenn danach noch Suffixe kommen
    match = re.search(r'^(.*?)(\d+\.\d+\.\d+(?:\.\d+)*)((?:_[a-zA-Z0-9]+)*?)(\.\w+)$', example_filename)

    if match:
        prefix = match.group(1)
        suffix_after_version = match.group(3) # Zusätze wie _11th
        extension = match.group(4) # Dateiendung .bin
        pattern = f"{prefix}*{suffix_after_version}{extension}"
        print(f"Abgeleitetes Muster (Regex): {pattern}")
        return pattern
    else:
        # Fallback: Ersetze den Teil nach dem letzten Unterstrich (vor der Erweiterung)
        base, ext = os.path.splitext(example_filename)
        parts = base.split('_')
        if len(parts) > 1:
            prefix = "_".join(parts[:-1]) + "_"
            pattern = prefix + "*" + ext
            print(f"Abgeleitetes Muster (Fallback '_'): {pattern}")
            return pattern
        else:
            # Letzter Fallback
            print(f"Warnung: Konnte kein klares Muster in '{example_filename}' erkennen. Verwende generisches Muster.", file=sys.stderr)
            return "update_kindle_*.bin"


def start_search(kindle_models, settings):
    """
    Startet die Firmware-Suche basierend auf der Benutzerauswahl und den Einstellungen.
    Fängt EOFError und KeyboardInterrupt ab.
    """
    while True:
        display_kindle_models(kindle_models)
        try:
            kindle_input = input("Gib die Kindle-Modellbezeichnung ein (z.B. PW5) oder 'exit' zum Abbrechen: ").upper()
        except EOFError:
            print("\nEOF-Fehler bei Eingabe erkannt. Kehre zum Hauptmenü zurück.")
            return
        except KeyboardInterrupt:
            print("\nBenutzerabbruch erkannt. Kehre zum Hauptmenü zurück.")
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
                print(f"Fehler: Keine Basis-URL für Modell {kindle_input} definiert.", file=sys.stderr)
                continue

            if not base_url.endswith('/'):
                base_url += '/'

            if static_version_filename:
                print(f"\n--- Suche nach statischer Firmware für {kindle_input} ---")
                print(f"Prüfe: {static_version_filename}")
                full_url = f"{base_url}{static_version_filename}"
                result = check_url(full_url, settings['possible_delays'], settings['delay_probability'], settings['timeout'])

                if isinstance(result, str):
                    print(f"Gefunden: {full_url}")
                elif isinstance(result, int):
                     print(f"Nicht gefunden: {full_url} (Status: {result})")
                elif result is None: # Fehler
                     # Fehlermeldung wurde bereits in check_url ausgegeben
                     pass
                else:
                     print(f"Unerwarteter Rückgabetyp von check_url für {full_url}: {type(result)}", file=sys.stderr)

                print("-" * 30)
                continue

            elif example_filename and default_version_range:
                filename_pattern = get_filename_pattern_simple(example_filename)

                print(f"\n--- Dynamische Suche für {kindle_input} ---")
                start_version = get_version_input("Gib die Startversion ein", default_version_range[0])
                end_version = get_version_input("Gib die Endversion ein", default_version_range[1])

                if start_version > end_version:
                    print("Fehler: Die Startversion muss kleiner oder gleich der Endversion sein.", file=sys.stderr)
                    continue

                print(f"\nSuche nach Firmware für {kindle_input}")
                print(f"Basis-URL: {base_url}")
                print(f"Muster: {filename_pattern}")
                print(f"Bereich: {'.'.join(map(str, start_version))} bis {'.'.join(map(str, end_version))}")
                print(f"Threads: {'Ja' if settings['use_threads'] else 'Nein'} (Max: {settings['max_threads'] if settings['use_threads'] else 'N/A'})")
                print(f"Timeout: {settings['timeout']}s")
                print(f"Verzögerung: {settings['possible_delays']}s (Wahrscheinlichkeit: {settings['delay_probability'] * 100:.1f}%)")
                print(f"Ausführlich: {'Ja' if settings['verbose'] else 'Nein'}")
                print("-" * 30)

                version_range_to_search = (start_version, end_version)

                start_time = time.time()
                found_firmwares = []
                try:
                    if settings['use_threads']:
                        found_firmwares = check_firmware_version_threaded(
                            base_url, filename_pattern, version_range_to_search,
                            settings['possible_delays'], settings['delay_probability'],
                            settings['timeout'], settings['max_threads'], settings['verbose']
                        )
                    else:
                        found_firmwares = check_firmware_version(
                            base_url, filename_pattern, version_range_to_search,
                            settings['possible_delays'], settings['delay_probability'],
                            settings['timeout'], settings['verbose']
                        )
                except KeyboardInterrupt:
                     print("\nSuche durch Benutzer abgebrochen.")
                except Exception as e:
                     print(f"\nUnerwarteter Fehler während der Suche: {e}", file=sys.stderr)

                end_time = time.time()

                print("-" * 30)
                if found_firmwares:
                    # Sortiere die Ergebnisse numerisch
                    sorted_firmwares = sort_firmwares_by_version(found_firmwares)
                    print(f"\nFolgende {len(sorted_firmwares)} Firmware-Dateien wurden gefunden (sortiert):")
                    for file in sorted_firmwares:
                        print(f"- {file}")
                else:
                    print("\nKeine passenden Firmware-Dateien im angegebenen Versionsbereich gefunden.")


                print(f"\nSuche dauerte {end_time - start_time:.2f} Sekunden.")
                print("-" * 30)

            else:
                 if not static_version_filename:
                     print(f"Fehler: Unvollständige Konfiguration für Modell {kindle_input} (fehlende 'static_version' oder 'example_filename'/'default_version_range').", file=sys.stderr)
                 print("-" * 30)
                 continue

        else:
            print("Ungültige Kindle-Modellbezeichnung. Bitte gib eine der unterstützten Bezeichnungen ein oder 'exit'.")
            print("-" * 30)


def configure_settings(current_settings):
    """
    Lässt den Benutzer die Skripteinstellungen ändern.
    Fängt EOFError und KeyboardInterrupt ab.
    """
    while True:
        print("\n--- Einstellungen ---")
        print(f"1. Mögliche Verzögerungszeiten (aktuell: {current_settings['possible_delays']})")
        print(f"2. Wahrscheinlichkeit für Verzögerung (aktuell: {current_settings['delay_probability'] * 100:.1f}%)")
        print(f"3. Multithreading verwenden (aktuell: {'Ja' if current_settings['use_threads'] else 'Nein'})")
        if current_settings['use_threads']:
            print(f"4. Maximale Threads (aktuell: {current_settings['max_threads']})")
        else:
             print("4. Maximale Threads (N/A - Multithreading deaktiviert)")
        print(f"5. Timeout für Anfragen (aktuell: {current_settings['timeout']}s)")
        print(f"6. Ausführliche Ausgabe (Verbose) (aktuell: {'Ja' if current_settings['verbose'] else 'Nein'})")
        print("7. Zurück zum Hauptmenü")
        print("-" * 30)

        try:
            choice = input("Wähle eine Option zum Ändern: ")

            if choice == "1":
                delays_input = input("Gib die Verzögerungszeiten durch Komma getrennt ein (z.B. 0.5,1.0,2.0): ")
                try:
                    if not delays_input.strip():
                         new_delays = []
                    else:
                        new_delays = [float(delay.strip()) for delay in delays_input.split(",") if delay.strip()]

                    if not all(delay >= 0 for delay in new_delays):
                        raise ValueError("Alle Verzögerungszeiten müssen >= 0 sein.")
                    current_settings['possible_delays'] = new_delays
                    print(f"Verzögerungszeiten gesetzt auf: {current_settings['possible_delays']}")
                except ValueError as e:
                    print(f"Ungültige Eingabe: {e}. Einstellungen nicht geändert.", file=sys.stderr)
            elif choice == "2":
                prob_input = input("Gib die Wahrscheinlichkeit für eine Verzögerung zwischen 0 und 1 ein (z.B. 0.1 für 10%): ")
                try:
                    new_prob = float(prob_input)
                    if not 0 <= new_prob <= 1:
                        raise ValueError("Wahrscheinlichkeit muss zwischen 0 und 1 liegen.")
                    current_settings['delay_probability'] = new_prob
                    print(f"Wahrscheinlichkeit gesetzt auf: {current_settings['delay_probability'] * 100:.1f}%")
                except ValueError as e:
                    print(f"Ungültige Eingabe: {e}. Einstellungen nicht geändert.", file=sys.stderr)
            elif choice == "3":
                threads_input = input("Sollen Threads verwendet werden? (ja/nein): ").lower()
                if threads_input == "ja":
                    current_settings['use_threads'] = True
                    print("Multithreading aktiviert.")
                elif threads_input == "nein":
                    current_settings['use_threads'] = False
                    print("Multithreading deaktiviert.")
                else:
                    print("Ungültige Eingabe. Einstellungen nicht geändert.")
            elif choice == "4":
                if not current_settings['use_threads']:
                    print("Einstellung nur relevant, wenn Multithreading aktiviert ist.")
                    continue
                threads_input = input(f"Gib die maximale Anzahl an Threads ein (aktuell: {current_settings['max_threads']}): ")
                try:
                    new_max_threads = int(threads_input)
                    if new_max_threads <= 0:
                        raise ValueError("Anzahl der Threads muss positiv sein.")
                    current_settings['max_threads'] = new_max_threads
                    print(f"Maximale Threads gesetzt auf: {current_settings['max_threads']}")
                except ValueError as e:
                    print(f"Ungültige Eingabe: {e}. Einstellungen nicht geändert.", file=sys.stderr)
            elif choice == "5":
                timeout_input = input(f"Gib den Timeout-Wert in Sekunden ein (aktuell: {current_settings['timeout']}): ")
                try:
                    new_timeout = int(timeout_input)
                    if new_timeout <= 0:
                        raise ValueError("Timeout muss positiv sein.")
                    current_settings['timeout'] = new_timeout
                    print(f"Timeout gesetzt auf: {current_settings['timeout']}s")
                except ValueError as e:
                    print(f"Ungültige Eingabe: {e}. Einstellungen nicht geändert.", file=sys.stderr)
            elif choice == "6":
                verbose_input = input("Soll die Ausgabe ausführlich sein? (ja/nein): ").lower()
                if verbose_input == "ja":
                    current_settings['verbose'] = True
                    print("Ausführliche Ausgabe aktiviert.")
                elif verbose_input == "nein":
                    current_settings['verbose'] = False
                    print("Ausführliche Ausgabe deaktiviert.")
                else:
                    print("Ungültige Eingabe. Einstellungen nicht geändert.")
            elif choice == "7":
                print("Zurück zum Hauptmenü.")
                break
            else:
                print("Ungültige Eingabe.")

        except EOFError:
            print("\nEOF-Fehler bei Eingabe erkannt. Kehre zum Hauptmenü zurück.")
            break
        except KeyboardInterrupt:
             print("\nBenutzerabbruch erkannt. Kehre zum Hauptmenü zurück.")
             break

    return current_settings


def main():
    """Hauptfunktion des Skripts, die das Menü steuert."""
    # Kindle Modelldaten (URLs und Namen könnten veraltet sein!)
    # HINWEIS: Diese Daten regelmäßig überprüfen und aktualisieren!
    kindle_models = {
        "K5": {
            "description": "Kindle 5 (Touch)",
            "base_url": "https://s3.amazonaws.com/G7G_FirmwareUpdates_WebDownloads/",
            "example_filename": "update_kindle_5.6.1.1.bin",
            "default_version_range": ((5, 3, 0), (5, 6, 25))
        },
        "K4": {
            "description": "Kindle 4 (Non-Touch, Silver/Graphite)",
            "base_url": "https://s3.amazonaws.com/firmwareupdates/",
            "static_version": "update_kindle_4.1.4.bin"
        },
        "K4B": {
            "description": "Kindle 4 (Non-Touch, Black)",
             "base_url": "https://s3.amazonaws.com/firmwareupdates/",
             "static_version": "update_kindle_4.1.4.bin"
        },
        "PW": {
            "description": "Kindle Paperwhite 1 (2012)",
            "base_url": "https://s3.amazonaws.com/G7G_FirmwareUpdates_WebDownloads/",
            "example_filename": "update_kindle_5.6.1.1.bin",
            "default_version_range": ((5, 0, 0), (5, 6, 25))
        },
        "PW2": {
            "description": "Kindle Paperwhite 2 (2013)",
            "base_url": "https://s3.amazonaws.com/firmwaredownloads/",
            "example_filename": "update_kindle_paperwhite_v2_5.12.2.2.bin",
            "default_version_range": ((5, 4, 0), (5, 12, 25))
        },
        "KT2": {
            "description": "Kindle 7 (Basic, 2014)",
            "base_url": "https://s3.amazonaws.com/firmwaredownloads/",
            "example_filename": "update_kindle_5.12.2.2.bin",
            "default_version_range": ((5, 6, 0), (5, 12, 25))
        },
        "KV": {
            "description": "Kindle Voyage (2014)",
            "base_url": "https://s3.amazonaws.com/firmwaredownloads/",
            # Geändert zu statischer Version aufgrund der 4-teiligen Versionsnummer
            "static_version": "update_kindle_voyage_5.13.7.0.1.bin"
            # "example_filename": "update_kindle_voyage_5.13.7.0.1.bin",
            # "default_version_range": ((5, 6, 0), (5, 13, 25)) # War nur 3-teilig
        },
        "PW3": {
            "description": "Kindle Paperwhite 3 (2015)",
            "base_url": "https://s3.amazonaws.com/firmwaredownloads/",
            "example_filename": "update_kindle_all_new_paperwhite_5.15.1.1.bin",
            "default_version_range": ((5, 7, 0), (5, 15, 25))
        },
        "KOA1": {
            "description": "Kindle Oasis 1 (2016)",
            "base_url": "https://s3.amazonaws.com/firmwaredownloads/",
            "example_filename": "update_kindle_oasis_5.15.1.1.bin",
            "default_version_range": ((5, 8, 0), (5, 15, 25))
        },
        "KT3": {
            "description": "Kindle 8 (Basic, 2016)",
            "base_url": "https://s3.amazonaws.com/firmwaredownloads/",
            "example_filename": "update_kindle_8th_5.15.1.1.bin",
            "default_version_range": ((5, 8, 0), (5, 15, 25))
        },
        "KOA2": {
            "description": "Kindle Oasis 2 (2017)",
            "base_url": "https://s3.amazonaws.com/firmwaredownloads/",
            "example_filename": "update_kindle_all_new_oasis_5.16.2.1.1.bin",
            "default_version_range": ((5, 9, 0), (5, 16, 25))
        },
        "PW4": {
            "description": "Kindle Paperwhite 4 (2018)",
            "base_url": "https://s3.amazonaws.com/firmwaredownloads/",
            "example_filename": "update_kindle_paperwhite_10th_5.16.2.1.1.bin",
            "default_version_range": ((5, 10, 0), (5, 16, 25))
        },
        "KT4": {
             "description": "Kindle 10 (Basic, 2019)",
            "base_url": "https://s3.amazonaws.com/firmwaredownloads/",
            "example_filename": "update_kindle_10th_5.16.2.1.1.bin",
            "default_version_range": ((5, 11, 0), (5, 16, 25))
        },
        "KOA3": {
            "description": "Kindle Oasis 3 (2019)",
            "base_url": "https://s3.amazonaws.com/firmwaredownloads/",
            "example_filename": "update_kindle_oasis_10th_5.16.2.1.1.bin",
            "default_version_range": ((5, 12, 0), (5, 16, 25))
        },
        "PW5": {
            "description": "Kindle Paperwhite 5 (11th Gen, 2021)",
            "base_url": "https://s3.amazonaws.com/firmwaredownloads/",
            "example_filename": "update_kindle_all_new_paperwhite_11th_5.16.8.bin",
            "default_version_range": ((5, 14, 0), (5, 17, 25))
        },
        "PW5SE": {
            "description": "Kindle Paperwhite 5 Signature Edition (11th Gen, 2021)",
            "base_url": "https://s3.amazonaws.com/firmwaredownloads/",
            "example_filename": "update_kindle_all_new_paperwhite_11th_5.16.8.bin",
            "default_version_range": ((5, 14, 0), (5, 17, 25))
        },
        "K11": {
            "description": "Kindle 11 (Basic, 2022)",
            "base_url": "https://s3.amazonaws.com/firmwaredownloads/",
            "example_filename": "update_kindle_11th_5.16.8.bin",
            "default_version_range": ((5, 15, 0), (5, 17, 25))
        },
        "Scribe": {
            "description": "Kindle Scribe (2022)",
            "base_url": "https://s3.amazonaws.com/firmwaredownloads/",
            "example_filename": "update_kindle_scribe_5.16.8.bin",
            "default_version_range": ((5, 16, 0), (5, 17, 25))
        },
    }

    settings = {
        'possible_delays': DEFAULT_DELAYS,
        'use_threads': True,
        'delay_probability': DEFAULT_DELAY_PROBABILITY,
        'timeout': DEFAULT_TIMEOUT,
        'verbose': DEFAULT_VERBOSE,
        'max_threads': DEFAULT_MAX_THREADS
    }

    while True:
        print("\n--- Kindle Firmware Checker Hauptmenü ---")
        print("1. Firmware-Suche starten")
        print("2. Verfügbare Kindle Modelle anzeigen")
        print("3. Einstellungen ändern")
        print("4. Skript beenden")
        print("-" * 30)

        try:
            choice = input("Bitte wähle eine Option: ")
        except EOFError:
            print("\nEOF-Fehler bei Eingabe erkannt. Beende Skript.")
            break
        except KeyboardInterrupt:
             print("\nBenutzerabbruch erkannt. Beende Skript.")
             break

        if choice == "1":
            start_search(kindle_models, settings)
        elif choice == "2":
            display_kindle_models(kindle_models)
        elif choice == "3":
            settings = configure_settings(settings)
        elif choice == "4":
            print("Skript wird beendet.")
            break
        else:
            print("Ungültige Eingabe. Bitte wähle eine der Optionen 1-4.")

if __name__ == "__main__":
    try:
        import requests
        from concurrent.futures import ThreadPoolExecutor, as_completed
        # Importiere packaging nur, wenn es auch verwendet wird (für die Sortierung)
        from packaging import version as pkg_version
    except ImportError as e:
        print(f"Fehler: Benötigte Bibliothek nicht gefunden: {e}. Bitte installiere sie (z.B. 'pip install requests packaging')", file=sys.stderr)
        sys.exit(1)

    main()
