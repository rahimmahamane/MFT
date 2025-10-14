import os
import subprocess
import platform
import sys
import sqlite3
import hashlib
import re
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
import time
from reportlab.lib.colors import black
from reportlab.lib.enums import TA_CENTER
import shlex

# --- Configuration IA ---
try:
    import google.generativeai as genai
    AI_ENABLED = True
except ImportError:
    AI_ENABLED = False
    print("AVERTISSEMENT: 'google.generativeai' non trouvé. Les fonctionnalités d'IA seront désactivées. Pour les activer, veuillez exécuter : pip install google-generativeai")

# --- Configuration de l'IA ---
# La clé API de Google est récupérée de manière sécurisée depuis une variable d'environnement.
# Définissez la variable d'environnement 'GOOGLE_API_KEY' avec votre clé.
# Si elle n'est pas définie, le script utilisera la valeur ci-dessous.
YOUR_API_KEY = os.environ.get("GOOGLE_API_KEY", "VOTRE_CLE_API_ICI")

# --- Configuration des Outils Externes ---
# Entrez ici le chemin complet vers l'exécutable 'ileapp.py' après l'avoir téléchargé.
# Exemple sur Windows : C:\Users\VotreNom\Documents\ileapp\ileapp.py
# Exemple sur Linux/macOS : /home/VotreNom/tools/ileapp/ileapp.py
ILEAPP_EXECUTABLE_PATH = ""
AB_DECODER_PATH = "ab_decoder.py"
ACQUISITION_DIR = "MFT_Acquisitions"


# --- Variables Globales pour la gestion des affaires ---
current_case = None
case_log_file = None

# --- Fonctions Utilitaires ---

def check_dependencies(tools):
    """Vérifie si les outils nécessaires sont installés et disponibles dans le PATH."""
    missing_tools = []
    for tool in tools:
        try:
            # Tente de lancer la commande avec des arguments pour éviter les fenêtres pop-up.
            subprocess.run([tool, "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing_tools.append(tool)
    if missing_tools:
        print("\n[ERREUR] Les outils suivants sont manquants et nécessaires pour ce script:")
        for tool in missing_tools:
            print(f"- {tool}")
        if 'adb' in missing_tools:
            print("  -> Veuillez installer les 'Android SDK Platform Tools' et les ajouter à votre variable PATH.")
        if 'idevicebackup2' in missing_tools or 'ideviceinfo' in missing_tools:
            print("  -> Veuillez installer 'libimobiledevice'.")
        sys.exit(1)

def clear_screen():
    """Efface le terminal pour une meilleure lisibilité."""
    os.system('cls' if platform.system() == 'Windows' else 'clear')

def print_banner():
    """Affiche la bannière du programme."""
    clear_screen()
    print("=" * 60)
    print("      Mobile Forensic Toolkit (MFT) - v8.0 - Optimisé          ")
    print("     par Mahamane - Outil Professionnel     ")
    print("=" * 60)
    print("\n   AVERTISSEMENT : Utilisation légale et éthique uniquement.\n")
    if current_case:
        print(f"-> Affaire en cours : {current_case}")
    print("-" * 60)

def ensure_acquisition_dir():
    """Crée le dossier principal pour stocker toutes les preuves."""
    if not os.path.exists(ACQUISITION_DIR):
        try:
            os.makedirs(ACQUISITION_DIR)
        except OSError as e:
            print(f"[ERREUR] Impossible de créer le dossier d'acquisition : {e}")
            sys.exit(1)

def run_command(command, log=True):
    """
    Exécute une commande système de manière sécurisée en utilisant une liste d'arguments
    pour éviter les injections de commandes.
    """
    if log and case_log_file:
        case_log_file.write(f"\n[CMD] Exécution de: {command}\n")

    print(f"\n[CMD] Exécution de: {command}")
    
    try:
        # Utilise shlex.split pour gérer les espaces et les guillemets dans la commande de manière sécurisée.
        args = shlex.split(command)
    except ValueError as e:
        print(f"[ERREUR] Erreur de syntaxe de commande : {e}")
        return ""
        
    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='ignore')
    output_lines = []
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output.strip())
            output_lines.append(output)
            if log and case_log_file:
                case_log_file.write(output)
    process.wait()
    return "".join(output_lines)


def calculate_sha256(filepath):
    """Calcule le hachage SHA256 d'un fichier."""
    if not os.path.exists(filepath):
        return "N/A - Fichier non trouvé"
    sha256 = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256.update(byte_block)
        return sha256.hexdigest()
    except Exception as e:
        log_action("Erreur", f"Erreur lors du calcul du hachage de {filepath}: {e}")
        return "N/A - Erreur de lecture"

def log_action(action_type, message, filepath=None):
    """Enregistre une action avec un horodatage dans le fichier de journal de l'affaire."""
    if not case_log_file:
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{action_type}] {message}"
    
    sha256_hash = ""
    if filepath and os.path.exists(filepath):
        sha256_hash = calculate_sha256(filepath)
    
    if sha256_hash:
        log_entry += f" | Hachage (SHA256) : {sha256_hash}"
    
    try:
        case_log_file.write(log_entry + "\n")
        print(f"\n[JOURNAL] {log_entry}")
    except Exception as e:
        print(f"[ERREUR] Impossible d'écrire dans le fichier journal : {e}")

# --- Fonctions de l'Assistant IA ---

def analyze_with_ai():
    """Analyse un fichier de base de données à l'aide de l'IA générative."""
    if not current_case:
        print("\n[ERREUR] Veuillez d'abord créer ou charger une affaire.")
        input("\nAppuyez sur Entrée pour continuer...")
        return

    # Vérification de la configuration de l'IA
    if not AI_ENABLED:
        print("\n[ERREUR] La bibliothèque 'google-generativeai' n'est pas installée.")
        print("         Veuillez exécuter : pip install google-generativeai")
        log_action("Analyse IA", "Échec - Bibliothèque IA non installée")
        input("\nAppuyez sur Entrée pour continuer...")
        return
        
    if "VOTRE_CLE_API_ICI" in YOUR_API_KEY:
        print("\n[INFO] L'assistant IA n'est pas configuré.")
        print("         Veuillez définir la variable d'environnement 'GOOGLE_API_KEY' ou modifier la variable 'YOUR_API_KEY' dans le script.")
        log_action("Analyse IA", "Échec - Assistant IA non configuré")
        input("\nAppuyez sur Entrée pour continuer...")
        return

    file_path = input("Entrez le chemin complet du fichier à analyser (ex: acquisitions/affaire/Android_Acquisition/whatsapp.db) : ")
    if not os.path.exists(file_path):
        print("\n[ERREUR] Fichier non trouvé. Veuillez vérifier le chemin.")
        input("\nAppuyez sur Entrée pour continuer...")
        return
    
    genai.configure(api_key=YOUR_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-pro-latest')


    try:
        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()
        
        # Obtenir la structure du schéma
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        schema_info = "Schéma de la base de données:\n"
        for name, sql in tables:
            schema_info += f"Table: {name}\nSQL: {sql}\n\n"

        print(f"\n[INFO] Envoi des informations sur le schéma pour analyse IA...")
        
        prompt = (f"En tant qu'analyste forensique, examinez ce schéma de base de données SQLite "
                  f"et suggérez des requêtes SQL potentiellement utiles pour extraire des informations clés "
                  f"telles que des messages, des contacts, des journaux d'appels ou des emplacements. "
                  f"Ne fournissez que les requêtes SQL et leur description. Ne donnez pas d'explication du schéma. "
                  f"\n\n{schema_info}")

        response = model.generate_content(prompt)
        
        print("\n" + "="*60)
        print("          Rapport d'Analyse Assistée par IA          ")
        print("="*60 + "\n")
        print(response.text)
        print("\n" + "="*60)
        
        log_action("Analyse IA", f"Analyse assistée par IA du fichier : {file_path}")
        
    except sqlite3.Error as e:
        print(f"\n[ERREUR] Impossible de lire la base de données : {e}")
        log_action("Analyse IA", f"Échec - Impossible de lire le fichier {file_path}")
    except Exception as e:
        print(f"\n[ERREUR] Une erreur inattendue est survenue : {e}")
        log_action("Analyse IA", f"Échec - Erreur inattendue")
    finally:
        if 'conn' in locals() and conn:
            conn.close()
    input("\nAppuyez sur Entrée pour continuer...")

def search_keywords():
    """Recherche des mots-clés dans tous les fichiers de l'affaire en cours."""
    if not current_case:
        print("\n[ERREUR] Veuillez d'abord créer ou charger une affaire.")
        input("\nAppuyez sur Entrée pour continuer...")
        return
    
    case_dir = os.path.join(ACQUISITION_DIR, current_case)
    if not os.path.exists(case_dir):
        print(f"\n[ERREUR] Le dossier d'affaire '{current_case}' n'existe pas.")
        input("\nAppuyez sur Entrée pour continuer...")
        return

    keywords_input = input("Entrez les mots-clés à rechercher (séparés par une virgule) : ")
    keywords = [kw.strip().lower() for kw in keywords_input.split(',')]
    if not keywords:
        print("\n[INFO] Aucune recherche effectuée. Aucun mot-clé n'a été fourni.")
        input("\nAppuyez sur Entrée pour continuer...")
        return
    
    log_action("Recherche Mots-clés", f"Début de la recherche pour les mots-clés : {', '.join(keywords)}")
    
    print("\n" + "="*60)
    print(f"Recherche de mots-clés dans l'affaire '{current_case}'...")
    print("="*60 + "\n")
    
    found_matches = False
    for root, _, files in os.walk(case_dir):
        for filename in files:
            file_path = os.path.join(root, filename)
            # Ignorer les fichiers binaires et de log
            if any(file_path.lower().endswith(ext) for ext in ['.ab', '.jpg', '.png', '.mp4', '.pdf', '.log', '.db']):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_number, line in enumerate(f, 1):
                        for keyword in keywords:
                            if re.search(r'\b' + re.escape(keyword) + r'\b', line.lower()):
                                print(f"[TROUVÉ] Fichier: {file_path}, Ligne {line_number}")
                                print(f"-> {line.strip()}\n")
                                found_matches = True
            except Exception:
                # Gérer les erreurs de lecture de fichiers (permissions, encodage, etc.)
                pass

    if not found_matches:
        print("\n[INFO] Aucun résultat trouvé pour les mots-clés spécifiés.")
    
    print("="*60)
    log_action("Recherche Mots-clés", "Fin de la recherche de mots-clés")
    input("\nAppuyez sur Entrée pour continuer...")

# --- Fonctions de gestion des menus ---
def analysis_menu():
    """Menu pour l'analyse des preuves."""
    while True:
        print_banner()
        print("--- Analyse des Preuves ---")
        print("1. Recherche de mots-clés dans les preuves")
        print("2. Analyse assistée par IA d'une base de données")
        print("3. Analyser une Sauvegarde iOS avec iLEAPP")
        print("4. Retour au Menu Principal")
        choice = input("\nSélectionnez une option : ")

        if choice == '1':
            search_keywords()
        elif choice == '2':
            analyze_with_ai()
        elif choice == '3':
            analyze_ios_backup_ileapp()
        elif choice == '4':
            break

def android_menu():
    """Menu pour les opérations de forensique Android."""
    while True:
        print_banner()
        print("--- Forensique Android ---")
        print("1. Sauvegarde Complète (ADB)")
        print("2. Sauvegarde de Données de l'Application (ADB)")
        print("3. Sauvegarde Avancée (Sans déverrouillage - Nécessite un outil tiers)")
        print("4. Extraire les journaux d'événements (logcat)")
        print("5. Lister les applications installées")
        print("6. Diagnostic de l'appareil")
        print("7. Extraire un fichier ou un dossier")
        print("8. Naviguer le système de fichiers (non-destructif)")
        print("9. Informations sur l'Appareil")
        print("10. Décoder une Sauvegarde (.ab)")
        print("11. Retour au Menu Principal")
        choice = input("\nSélectionnez une option : ")

        if choice == '1':
            backup_android_adb()
        elif choice == '2':
            app_package = input("Entrez le nom du package de l'application (ex: com.whatsapp) : ")
            backup_android_adb(app_package)
        elif choice == '3':
            advanced_android_backup()
        elif choice == '4':
            extract_android_logcat()
        elif choice == '5':
            list_android_apps()
        elif choice == '6':
            diagnose_android_device()
        elif choice == '7':
            pull_android_file()
        elif choice == '8':
            browse_android_filesystem()
        elif choice == '9':
            get_android_info()
        elif choice == '10':
            decode_android_backup()
        elif choice == '11':
            break

def iphone_menu():
    """Menu pour les opérations de forensique iPhone."""
    while True:
        print_banner()
        print("--- Forensique iPhone ---")
        print("1. Sauvegarde Complète (idevicebackup2 - Nécessite le déverrouillage)")
        print("2. Sauvegarde Avancée (Sans déverrouillage - Nécessite un outil tiers)")
        print("3. Informations sur l'Appareil")
        print("4. Retour au Menu Principal")
        choice = input("\nSélectionnez une option : ")

        if choice == '1':
            backup_iphone_full()
        elif choice == '2':
            advanced_iphone_backup()
        elif choice == '3':
            get_iphone_info()
        elif choice == '4':
            break

def manage_cases():
    """Menu pour créer ou charger une affaire."""
    global current_case, case_log_file
    while True:
        print_banner()
        print("--- Gestion des Affaires ---")
        print("1. Créer une nouvelle affaire")
        print("2. Charger une affaire existante")
        print("3. Retour au Menu Principal")
        choice = input("\nSélectionnez une option : ")

        if choice == '1':
            case_name = input("Entrez le nom de la nouvelle affaire (ex: Affaire_Dupont) : ")
            if not case_name:
                print("\n[ERREUR] Le nom de l'affaire ne peut pas être vide.")
                input("\nAppuyez sur Entrée pour continuer...")
                continue
            case_dir = os.path.join(ACQUISITION_DIR, case_name)
            if os.path.exists(case_dir):
                print(f"\n[ERREUR] L'affaire '{case_name}' existe déjà.")
            else:
                try:
                    os.makedirs(case_dir)
                    current_case = case_name
                    log_filepath = os.path.join(case_dir, "journal.log")
                    case_log_file = open(log_filepath, "a", encoding='utf-8')
                    log_action("Affaire", f"Création d'une nouvelle affaire : {case_name}")
                    print(f"\n[SUCCÈS] Affaire '{case_name}' créée et chargée.")
                    input("\nAppuyez sur Entrée pour continuer...")
                    break
                except OSError as e:
                    print(f"[ERREUR] Impossible de créer le dossier de l'affaire : {e}")
            input("\nAppuyez sur Entrée pour continuer...")
        elif choice == '2':
            cases = [d for d in os.listdir(ACQUISITION_DIR) if os.path.isdir(os.path.join(ACQUISITION_DIR, d))]
            if not cases:
                print("\n[INFO] Aucune affaire existante trouvée.")
            else:
                print("\nAffaires existantes :")
                for i, case in enumerate(cases):
                    print(f"{i+1}. {case}")
                
                try:
                    case_index = int(input("\nEntrez le numéro de l'affaire à charger : ")) - 1
                    if 0 <= case_index < len(cases):
                        current_case = cases[case_index]
                        log_filepath = os.path.join(ACQUISITION_DIR, current_case, "journal.log")
                        case_log_file = open(log_filepath, "a", encoding='utf-8')
                        log_action("Affaire", f"Chargement de l'affaire : {current_case}")
                        print(f"\n[SUCCÈS] Affaire '{current_case}' chargée.")
                        input("\nAppuyez sur Entrée pour continuer...")
                        break
                    else:
                        print("\n[ERREUR] Numéro d'affaire invalide.")
                except ValueError:
                    print("\n[ERREUR] Entrée invalide. Veuillez entrer un numéro.")
            input("\nAppuyez sur Entrée pour continuer...")
        elif choice == '3':
            break

# --- Fonctions Forensiques Android ---

def get_android_info():
    """Affiche des informations de base sur l'appareil Android connecté."""
    print("\n[INFO] Récupération des informations de l'appareil Android...")
    log_action("Info Appareil", "Récupération des informations de l'appareil Android")
    run_command("adb devices")
    run_command("adb shell getprop ro.product.model")
    run_command("adb shell getprop ro.build.version.release")
    input("\nAppuyez sur Entrée pour continuer...")

def diagnose_android_device():
    """Effectue un diagnostic de l'état de l'appareil Android."""
    print("\n[INFO] Lancement du diagnostic de l'appareil...")
    
    devices = run_command("adb devices").split('\n')
    device_status = "N/A"
    
    for line in devices:
        if '\tdevice' in line:
            device_status = "Connecté (ADB activé)"
        elif '\toffline' in line:
            device_status = "Hors ligne"
        elif '\tunauthorized' in line:
            device_status = "Non autorisé (Autorisation ADB requise)"
            
    if device_status == "N/A":
        print("\n[DIAGNOSTIC] Aucun appareil Android détecté.")
        log_action("Diagnostic", "Aucun appareil détecté")
        input("\nAppuyez sur Entrée pour continuer...")
        return

    print(f"\n[DIAGNOSTIC] Appareil trouvé. Statut: {device_status}")
    log_action("Diagnostic", f"Appareil trouvé. Statut: {device_status}")

    if device_status == "Connecté (ADB activé)":
        print("[DIAGNOSTIC] L'appareil est détecté et autorisé.")
        print("Tentative d'accès root...")
        run_command("adb shell su -c id", log=False)
        
    elif device_status == "Non autorisé (Autorisation ADB requise)":
        print("[DIAGNOSTIC] L'autorisation ADB n'a pas été donnée sur l'appareil.")
        print("Veuillez déverrouiller l'appareil et accepter la demande 'Autoriser le débogage USB'.")
        
    input("\nAppuyez sur Entrée pour continuer...")

def pull_android_file():
    """Extrait un fichier ou un dossier spécifique de l'appareil."""
    if not current_case:
        print("\n[ERREUR] Veuillez d'abord créer ou charger une affaire.")
        input("\nAppuyez sur Entrée pour continuer...")
        return
        
    source_path = input("Entrez le chemin complet du fichier/dossier sur l'appareil (ex: /sdcard/DCIM) : ")
    if not source_path:
        print("\n[ANNULÉ] Le chemin source ne peut pas être vide.")
        input("\nAppuyez sur Entrée pour continuer...")
        return

    output_dir = os.path.join(ACQUISITION_DIR, current_case, "Android_Acquisition", "Pulled_Files")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    local_path = os.path.join(output_dir, os.path.basename(source_path))

    print(f"\n[INFO] Extraction en cours de '{source_path}' vers '{local_path}'...")
    log_action("Extraction Sélective", f"Début de l'extraction de '{source_path}'")
    
    command = f"adb pull \"{source_path}\" \"{local_path}\""
    run_command(command)
    
    if os.path.exists(local_path):
        if os.path.isfile(local_path):
            log_action("Extraction Sélective", f"Extraction de fichier terminée : '{local_path}'", local_path)
        else:
            log_action("Extraction Sélective", f"Extraction de dossier terminée : '{local_path}'")
        print(f"\n[SUCCÈS] Fichier(s) extrait(s) vers : '{local_path}'")
    else:
        print("\n[ERREUR] L'extraction a échoué. Le fichier/dossier n'a pas été trouvé ou l'autorisation a été refusée.")
        log_action("Extraction Sélective", f"Échec de l'extraction de '{source_path}'")
    input("\nAppuyez sur Entrée pour continuer...")

def browse_android_filesystem():
    """Permet de naviguer de manière non-destructif dans le système de fichiers de l'appareil."""
    print("\n[INFO] Lancement de l'explorateur de fichiers non-destructif...")
    
    devices = run_command("adb devices").split('\n')
    if "device" not in str(devices):
        print("\n[ERREUR] Aucun appareil Android autorisé n'a été trouvé.")
        input("\nAppuyez sur Entrée pour continuer...")
        return
    
    current_path = "/sdcard"
    log_action("Navigation Fichier", "Début de la navigation du système de fichiers")

    while True:
        print_banner()
        print("--- Navigateur de Fichiers Android ---")
        print(f"Chemin actuel : {current_path}")
        print("Commandes disponibles : ls, cd <dossier>, cd .., quit")
        print("ATTENTION : Les commandes de modification ou de suppression sont bloquées pour des raisons de sécurité.")
        
        user_input = input(f"\nforensique-shell:{current_path}$ ").strip()

        if user_input.lower() == "quit":
            print("\n[INFO] Fin de la navigation.")
            log_action("Navigation Fichier", "Fin de la navigation du système de fichiers")
            input("\nAppuyez sur Entrée pour continuer...")
            break
        elif user_input.lower() == "ls":
            command = f"adb shell ls -la \"{current_path}\""
            run_command(command, log=False)
            input("\nAppuyez sur Entrée pour continuer...")
        elif user_input.lower().startswith("cd "):
            target_dir = user_input[3:].strip()
            
            if target_dir == "..":
                current_path = os.path.dirname(current_path) if current_path != "/" else "/"
            else:
                new_path = os.path.join(current_path, target_dir).replace('\\', '/')
                command = f"adb shell ls \"{new_path}\""
                result = run_command(command, log=False)
                if "No such file or directory" not in result and "Permission denied" not in result:
                    current_path = new_path
                else:
                    print("[ERREUR] Impossible d'accéder à ce dossier. Le chemin n'existe pas ou les permissions sont insuffisantes.")
            input("\nAppuyez sur Entrée pour continuer...")
        else:
            print("\n[ERREUR] Commande non valide ou non autorisée. Veuillez utiliser 'ls', 'cd <dossier>', 'cd ..', ou 'quit'.")
            input("\nAppuyez sur Entrée pour continuer...")

def backup_android_adb(app_package=None):
    """Crée une sauvegarde complète ou par application via ADB."""
    if not current_case:
        print("\n[ERREUR] Veuillez d'abord créer ou charger une affaire.")
        input("\nAppuyez sur Entrée pour continuer...")
        return

    output_dir = os.path.join(ACQUISITION_DIR, current_case, "Android_Acquisition")
    os.makedirs(output_dir, exist_ok=True)
    
    if app_package:
        filename = f"{app_package}.ab"
        command = f"adb backup -f \"{os.path.join(output_dir, filename)}\" -noapk {app_package}"
        log_action("Sauvegarde ADB", f"Début de la sauvegarde de l'application '{app_package}'")
    else:
        filename = "full_backup.ab"
        command = f"adb backup -f \"{os.path.join(output_dir, filename)}\" -all -apk -shared"
        log_action("Sauvegarde ADB", "Début de la sauvegarde complète")

    run_command(command)
    print(f"\n[SUCCÈS] Sauvegarde terminée dans le dossier : '{output_dir}'")
    log_action("Sauvegarde ADB", f"Sauvegarde terminée pour le fichier '{filename}'", os.path.join(output_dir, filename))
    input("\nAppuyez sur Entrée pour continuer...")

def advanced_android_backup():
    """Function to guide an analyst through an advanced Android backup without USB Debugging enabled."""
    if not current_case:
        print("\n[ERREUR] Veuillez d'abord créer ou charger une affaire.")
        input("\nAppuyez sur Entrée pour continuer...")
        return
        
    print("\n" + "="*60)
    print("     Procédure de Sauvegarde Avancée sur Android Verrouillé    ")
    print("="*60 + "\n")
    print("ATTENTION : Cette méthode nécessite un outil tiers (ex: bootloader exploit, chip-off)")
    print("qui permet de contourner le débogage USB. Ce script ne lance pas l'outil, mais vous")
    print("guide à travers le processus pour documenter la chaîne de garde.")
    
    log_action("Sauvegarde Avancée Android", "Début de la procédure de sauvegarde avancée")
    
    print("\nÉtape 1 : Identifiez l'outil d'exploitation approprié pour votre appareil.")
    print("           - La plupart des méthodes exploitent le bootloader (ex: TWRP, Magisk).")
    print("           - Les techniques plus extrêmes impliquent le dessoudage de la puce (chip-off).")
    print("           - Soyez conscient que le déchiffrement des données reste un défi majeur.")
    input("\nAppuyez sur Entrée pour continuer...")
    
    print("\nÉtape 2 : Lancez votre outil externe et suivez les instructions du fabricant.")
    print("           - Le but est d'obtenir un accès root ou une copie complète des données.")
    print("           - Pour les méthodes physiques (chip-off), utilisez votre équipement spécialisé.")
    print("           - Sauvegardez les données extraites dans le dossier de l'affaire.")
    
    print("\nÉtape 3 : Documentez votre processus.")
    print("           - Copiez les commandes que vous utilisez et les détails de l'opération dans le journal.")
    
    print("\n" + "="*60)
    print("     Procédure terminée. L'acquisition se fait maintenant manuellement.     ")
    print("     Les fichiers acquis doivent être ajoutés manuellement au dossier de l'affaire.     ")
    print("="*60 + "\n")
    
    log_action("Sauvegarde Avancée Android", "Fin de la procédure. L'analyste doit effectuer l'extraction manuellement.")
    input("\nAppuyez sur Entrée pour continuer...")

def extract_android_logcat():
    """Extrait les journaux d'événements (logcat) d'un appareil Android."""
    if not current_case:
        print("\n[ERREUR] Veuillez d'abord créer ou charger une affaire.")
        input("\nAppuyez sur Entrée pour continuer...")
        return
    
    output_dir = os.path.join(ACQUISITION_DIR, current_case, "Android_Acquisition")
    os.makedirs(output_dir, exist_ok=True)
        
    filepath = os.path.join(output_dir, "logcat.txt")
    
    print("\n[INFO] Capture des journaux logcat. Appuyez sur CTRL+C pour arrêter.")
    log_action("Extraction Logcat", "Début de la capture des journaux logcat")
    
    try:
        command = f"adb logcat -d > \"{filepath}\""
        run_command(command, log=False)
        print(f"\n[SUCCÈS] Journaux enregistrés dans : {filepath}")
        log_action("Extraction Logcat", "Fin de la capture des journaux logcat", filepath)
    except KeyboardInterrupt:
        print("\n[INFO] Capture des journaux interrompue par l'utilisateur.")
        log_action("Extraction Logcat", "Capture des journaux interrompue par l'utilisateur", filepath)
    input("\nAppuyez sur Entrée pour continuer...")

def list_android_apps():
    """Liste les applications installées sur un appareil Android."""
    print("\n[INFO] Liste des applications installées...")
    log_action("Info Appareil", "Liste des applications installées")
    run_command("adb shell pm list packages")
    input("\nAppuyez sur Entrée pour continuer...")
    
def decode_android_backup():
    """Décode une sauvegarde Android (.ab) et l'extrait."""
    if not current_case:
        print("\n[ERREUR] Veuillez d'abord créer ou charger une affaire.")
        input("\nAppuyez sur Entrée pour continuer...")
        return

    ab_file = input("Entrez le chemin complet du fichier de sauvegarde .ab à décoder : ")
    if not os.path.exists(ab_file) or not ab_file.endswith('.ab'):
        print("\n[ERREUR] Fichier invalide ou non trouvé. Assurez-vous que le chemin est correct et que le fichier a l'extension '.ab'.")
        input("\nAppuyez sur Entrée pour continuer...")
        return

    if not os.path.exists(AB_DECODER_PATH):
        print(f"\n[ERREUR] '{AB_DECODER_PATH}' non trouvé.")
        print("Veuillez vous assurer que le script 'ab_decoder.py' est dans le même dossier.")
        input("\nAppuyez sur Entrée pour continuer...")
        return

    output_dir = os.path.join(ACQUISITION_DIR, current_case, "Android_Decoded")
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n[INFO] Lancement du décodage de la sauvegarde '{os.path.basename(ab_file)}'...")
    log_action("Décodage Sauvegarde Android", f"Début du décodage de '{ab_file}' vers '{output_dir}'")

    command = f'"{sys.executable}" "{AB_DECODER_PATH}" -i "{ab_file}" -o "{output_dir}"'
    run_command(command)

    log_action("Décodage Sauvegarde Android", "Décodage terminé")
    print(f"\n[SUCCÈS] Sauvegarde décodée dans le dossier : '{output_dir}'")
    input("\nAppuyez sur Entrée pour continuer...")

# --- Fonctions Forensiques iPhone ---

def get_iphone_info():
    """Affiche des informations de base sur l'appareil iPhone connecté."""
    print("\n[INFO] Récupération des informations de l'appareil iPhone...")
    log_action("Info Appareil", "Récupération des informations de l'appareil iPhone")
    run_command("ideviceinfo")
    input("\nAppuyez sur Entrée pour continuer...")

def backup_iphone_full():
    """Crée une sauvegarde complète d'un appareil iOS via idevicebackup2."""
    if not current_case:
        print("\n[ERREUR] Veuillez d'abord créer ou charger une affaire.")
        input("\nAppuyez sur Entrée pour continuer...")
        return
        
    print("\n[INFO] Sauvegarde complète en cours. Veuillez déverrouiller l'appareil...")
    output_dir = os.path.join(ACQUISITION_DIR, current_case, "iOS_Acquisition")
    os.makedirs(output_dir, exist_ok=True)

    log_action("Sauvegarde iOS", "Début de la sauvegarde complète")
    command = f"idevicebackup2 backup --full \"{output_dir}\""

    run_command(command)
    print(f"\n[SUCCÈS] Sauvegarde complète terminée dans le dossier : '{output_dir}'")
    log_action("Sauvegarde iOS", "Sauvegarde terminée", output_dir)
    input("\nAppuyez sur Entrée pour continuer...")

def advanced_iphone_backup():
    """Fonction de guidage pour une sauvegarde avancée sur un iPhone verrouillé."""
    if not current_case:
        print("\n[ERREUR] Veuillez d'abord créer ou charger une affaire.")
        input("\nAppuyez sur Entrée pour continuer...")
        return

    print("\n" + "="*60)
    print("     Procédure de Sauvegarde Avancée sur iPhone Verrouillé    ")
    print("="*60 + "\n")
    print("ATTENTION : Cette méthode nécessite un outil tiers (ex: checkra1n, payant)")
    print("qui exploite une faille Bootrom. Ce script ne lance pas l'outil, mais vous")
    print("guide à travers le processus pour documenter la chaîne de garde.")
    
    log_action("Sauvegarde Avancée iOS", "Début de la procédure de sauvegarde avancée")
    
    print("\nÉtape 1 : Mettez l'appareil en mode DFU (Device Firmware Update).")
    print("           - Appareil éteint, connectez le câble USB.")
    print("           - Suivez la procédure spécifique à votre modèle (ex: checkra1n vous guidera).")
    input("\nAppuyez sur Entrée pour continuer une fois l'appareil en mode DFU...")
    
    print("\nÉtape 2 : Lancez votre outil d'exploitation (checkra1n, etc.) et suivez les instructions.")
    print("           Le but est de démarrer l'appareil avec un shell root sans déverrouiller l'écran.")
    input("\nAppuyez sur Entrée une fois que l'outil a terminé et que vous avez un accès shell...")
    
    print("\nÉtape 3 : Une fois l'accès shell obtenu, vous pouvez utiliser des commandes comme 'scp' pour")
    print("           extraire des fichiers, ou des outils spécialisés pour faire une image complète.")
    print("           Exemple de commande SC P: scp -r root@<IP_de_l'appareil>:/var/mobile/Containers/Data/Application/ /votre/dossier/")
    
    print("\nÉtape 4 : Documentez votre processus.")
    print("           Vous êtes maintenant responsable d'exécuter les commandes d'extraction.")
    print("           Copiez les commandes que vous utilisez dans le journal de l'affaire.")
    
    print("\n" + "="*60)
    print("     Procédure terminée. L'acquisition se fait maintenant manuellement.     ")
    print("     Les fichiers acquis doivent être ajoutés manuellement au dossier de l'affaire.     ")
    print("="*60 + "\n")
    
    log_action("Sauvegarde Avancée iOS", "Fin de la procédure. L'analyste doit effectuer l'extraction manuellement.")
    input("\nAppuyez sur Entrée pour continuer...")


def analyze_ios_backup_ileapp():
    """Exécute iLEAPP pour analyser une sauvegarde iOS ou Android."""
    if not current_case:
        print("\n[ERREUR] Veuillez d'abord créer ou charger une affaire.")
        input("\nAppuyez sur Entrée pour continuer...")
        return
    
    if not ILEAPP_EXECUTABLE_PATH or not os.path.exists(ILEAPP_EXECUTABLE_PATH):
        print("\n[ERREUR] Le chemin vers l'exécutable iLEAPP n'est pas configuré ou est invalide.")
        print("         Veuillez télécharger iLEAPP depuis 'https://github.com/abrignoni/iLEAPP'")
        print("         et définir le chemin dans la variable 'ILEAPP_EXECUTABLE_PATH' en haut du script.")
        input("\nAppuyez sur Entrée pour continuer...")
        return
        
    backup_path = input("Entrez le chemin complet de la sauvegarde à analyser : ")
    if not os.path.exists(backup_path):
        print("\n[ERREUR] Sauvegarde non trouvée. Veuillez vérifier le chemin.")
        input("\nAppuyez sur Entrée pour continuer...")
        return
    
    # iLEAPP gère les deux types de sauvegardes, mais il est bon de demander pour la journalisation.
    platform_type_input = input("S'agit-il d'une sauvegarde iOS ou Android ? (laissez vide pour auto-détection par iLEAPP) : ").lower()
    log_action("Analyse iLEAPP", f"Préparation de l'analyse pour une sauvegarde de type: {platform_type_input}")

    output_dir = os.path.join(ACQUISITION_DIR, current_case, "iLEAPP_Reports")
    os.makedirs(output_dir, exist_ok=True)

    print("\n[INFO] Lancement de l'analyse iLEAPP. Cela peut prendre du temps...")
    log_action("Analyse iLEAPP", "Lancement de l'analyse avec l'outil externe iLEAPP")
    
    # Commande pour appeler le vrai outil iLEAPP
    # Note: iLEAPP n'a pas besoin des flags -p ou -a, il auto-détecte le type de sauvegarde.
    command = f'"{sys.executable}" "{ILEAPP_EXECUTABLE_PATH}" -o "{output_dir}" -i "{backup_path}"'
    run_command(command)
    
    print("\n[INFO] L'analyse iLEAPP est terminée. Un rapport a été généré (s'il n'y a pas eu d'erreurs).")
    log_action("Analyse iLEAPP", f"Analyse terminée avec iLEAPP. Rapport dans {output_dir}")
    input("\nAppuyez sur Entrée pour continuer...")


# --- Fonctions de rapport ---

def generate_pdf_report():
    """Génère un rapport PDF avec les informations de l'affaire."""
    if not current_case:
        print("\n[ERREUR] Veuillez d'abord créer ou charger une affaire.")
        input("\nAppuyez sur Entrée pour continuer...")
        return

    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        
        # NOTE : Les polices personnalisées 'Vera' ne sont pas incluses dans le projet.
        # Nous commentons ces lignes pour éviter une erreur et utilisons les polices par défaut.
        # Si vous souhaitez les utiliser, assurez-vous que les fichiers Vera.ttf et VeraBd.ttf
        # sont présents dans le même dossier que le script.
        # if not 'Vera' in pdfmetrics.getRegisteredFontNames():
        #     pdfmetrics.registerFont(TTFont('Vera', 'Vera.ttf'))
        # if not 'VeraBd' in pdfmetrics.getRegisteredFontNames():
        #     pdfmetrics.registerFont(TTFont('VeraBd', 'VeraBd.ttf'))
    except ImportError:
        print("\n[ERREUR] La bibliothèque 'reportlab' n'est pas installée.")
        print("Veuillez l'installer en exécutant : pip install reportlab")
        input("\nAppuyez sur Entrée pour continuer...")
        return
    except Exception as e:
        print(f"\n[ERREUR] Une erreur s'est produite lors de la préparation du rapport PDF : {e}")
        input("\nAppuyez sur Entrée pour continuer...")
        return

    analyst_name = input("Entrez votre nom pour le rapport : ")
    report_filepath = os.path.join(ACQUISITION_DIR, current_case, f"{current_case}_Rapport.pdf")
    doc = SimpleDocTemplate(report_filepath, pagesize=letter)
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Heading1', fontSize=18, leading=22, fontName='Helvetica-Bold', spaceAfter=12, alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='Heading2', fontSize=14, leading=18, fontName='Helvetica-Bold', spaceAfter=8))
    styles.add(ParagraphStyle(name='Normal', fontSize=10, leading=12, fontName='Helvetica'))
    
    story = []

    story.append(Paragraph(f"Rapport d'Affaire Numérique - {current_case}", styles['Heading1']))
    story.append(Paragraph(f"Date de création : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Paragraph(f"Analyste : {analyst_name}", styles['Normal']))
    story.append(Spacer(1, 0.25*inch))

    story.append(Paragraph("Résumé des acquisitions", styles['Heading2']))
    case_dir = os.path.join(ACQUISITION_DIR, current_case)
    acquired_files = []
    for root, dirs, files in os.walk(case_dir):
        for filename in files:
            if filename not in ["journal.log", f"{current_case}_Rapport.pdf"]:
                filepath = os.path.join(root, filename)
                acquired_files.append(filepath)

    if acquired_files:
        for fpath in acquired_files:
            file_hash = calculate_sha256(fpath)
            story.append(Paragraph(f"**Fichier :** {os.path.basename(fpath)}", styles['Normal']))
            story.append(Paragraph(f"**Chemin :** {fpath}", styles['Normal']))
            story.append(Paragraph(f"**SHA256 :** {file_hash}", styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
    else:
        story.append(Paragraph("Aucun fichier d'acquisition trouvé.", styles['Normal']))

    story.append(Spacer(1, 0.25*inch))
    story.append(Paragraph("Journal d'activités (Chaîne de Garde)", styles['Heading2']))
    log_filepath = os.path.join(case_dir, "journal.log")
    if os.path.exists(log_filepath):
        with open(log_filepath, "r", encoding='utf-8') as f:
            log_content = f.read()
        story.append(Paragraph(log_content.replace('\n', '<br/>'), styles['Normal']))
    else:
        story.append(Paragraph("Fichier journal non trouvé.", styles['Normal']))

    doc.build(story)

    print(f"\n[SUCCÈS] Rapport PDF généré avec succès à l'emplacement : '{report_filepath}'")
    log_action("Rapport PDF", f"Génération du rapport PDF de l'affaire", report_filepath)
    input("\nAppuyez sur Entrée pour continuer...")

# --- Menu Principal ---

def main_menu():
    """Menu principal du Mobile Forensic Toolkit."""
    # Vérifie les privilèges root (fonctionne sur Linux/macOS)
    if platform.system() != "Windows" and os.geteuid() == 0:
        print("\n[ATTENTION] Vous exécutez ce script avec les privilèges root (`sudo`).")
        print("Certaines opérations de forensique peuvent en avoir besoin, mais cela peut")
        print("également entraîner des problèmes de permissions de fichiers (les fichiers")
        print("créés par le script appartiendront à l'utilisateur 'root').")
        
        while True:
            confirm = input("Voulez-vous continuer avec les privilèges root ? (o/n) : ").lower()
            if confirm == 'o':
                break
            elif confirm == 'n':
                print("Le script va se fermer. Veuillez le relancer sans 'sudo' si vous le souhaitez.")
                sys.exit(0)
            else:
                print("Réponse invalide. Veuillez répondre par 'o' ou 'n'.")
                
    # Vérification des dépendances au démarrage
    check_dependencies(['adb', 'idevicebackup2', 'ideviceinfo'])
    ensure_acquisition_dir()
    while True:
        print_banner()
        print("--- Menu Principal ---")
        if not current_case:
            print("1. Gérer les affaires (obligatoire avant toute opération)")
        else:
            print("1. Gérer les affaires")
        print("2. Forensique Android")
        print("3. Forensique iPhone")
        print("4. Analyse des Preuves")
        print("5. Générer un rapport PDF")
        print("6. Quitter")
        choice = input("\nSélectionnez une option : ")

        if choice == '1':
            manage_cases()
        elif choice == '2':
            if not current_case:
                print("\n[ERREUR] Veuillez d'abord créer ou charger une affaire.")
                input("\nAppuyez sur Entrée pour continuer...")
            else:
                android_menu()
        elif choice == '3':
            if not current_case:
                print("\n[ERREUR] Veuillez d'abord créer ou charger une affaire.")
                input("\nAppuyez sur Entrée pour continuer...")
            else:
                iphone_menu()
        elif choice == '4':
            if not current_case:
                print("\n[ERREUR] Veuillez d'abord créer ou charger une affaire.")
                input("\nAppuyez sur Entrée pour continuer...")
            else:
                analysis_menu()
        elif choice == '5':
            generate_pdf_report()
        elif choice == '6':
            if case_log_file:
                case_log_file.close()
            print("Au revoir !")
            break
        else:
            print("\n[ERREUR] Option invalide. Veuillez réessayer.")
            input("\nAppuyez sur Entrée pour continuer...")

if __name__ == "__main__":
    main_menu()
