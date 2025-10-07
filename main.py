# -*- coding: utf-8 -*- 

import sys
import logging
from scapy.all import conf

# Importation des modules locaux
from utils import check_root, get_interfaces, set_monitor_mode, stop_monitor_mode
from scanner import scan_networks
from attacks import deauth_attack, beacon_flood
from ai_detector import run_ai_detector

# --- Configuration Globale ---
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
conf.verb = 0

class Application:
    """
    Classe principale de l'application.
    """
    def __init__(self):
        """
        Initialise l'application.
        """
        self.interface = None
        self.monitor_interface = None

    def _attacks_menu(self):
        """
        Affiche le menu des attaques et gère les entrées de l'utilisateur.
        """
        while True:
            print("\n" + "="*20 + " MENU ATTAQUES " + "="*20)
            print("   /!\\ ATTENTION /!\\")
            print("   L'utilisation de ces fonctions est illégale sans autorisation.")
            print("   Assurez-vous d'être dans un environnement contrôlé et autorisé.")
            print("="*56)
            print("1. Scanner les réseaux pour trouver des cibles")
            print("2. Attaque de désauthentification")
            print("3. Inondation de balises (Beacon Flood)")
            print("4. Retour au menu principal")
            choice = input("Votre choix : ")

            if choice == '1':
                scan_networks(self.monitor_interface)
            elif choice == '2':
                bssid = input("Entrez le BSSID du point d'accès cible : ")
                target = input("Entrez l'adresse MAC du client cible (ou 'ff:ff:ff:ff:ff:ff' pour tous) : ")
                try:
                    count = int(input("Nombre de paquets à envoyer : "))
                    deauth_attack(self.monitor_interface, target, bssid, count)
                except ValueError:
                    print("[-] Entrée invalide pour le nombre de paquets.")
            elif choice == '3':
                ssid_base = input("Entrez un nom de base pour les faux SSID : ")
                beacon_flood(self.monitor_interface, ssid_base)
            elif choice == '4':
                break
            else:
                print("[-] Choix invalide. Veuillez réessayer.")

    def run(self):
        """
        Exécute l'application.
        """
        check_root()
        interfaces = get_interfaces()
        if not interfaces:
            print("[-] Aucune interface Wi-Fi compatible trouvée. Assurez-vous que votre matériel est détecté.")
            return

        print("Interfaces Wi-Fi disponibles :", ", ".join(interfaces))
        self.interface = input("Choisissez l'interface à utiliser : ")
        if self.interface not in interfaces:
            print("[-] Interface invalide.")
            return

        self.monitor_interface = set_monitor_mode(self.interface)
        if not self.monitor_interface:
            return

        try:
            while True:
                print("\n" + "="*20 + " MENU PRINCIPAL " + "="*20)
                print(f"Interface en mode moniteur : {self.monitor_interface}")
                print("1. Détecteur d'anomalies IA")
                print("2. Menu Attaques")
                print("3. Quitter")
                choice = input("Votre choix : ")

                if choice == '1':
                    run_ai_detector(self.monitor_interface)
                elif choice == '2':
                    self._attacks_menu()
                elif choice == '3':
                    break
                else:
                    print("[-] Choix invalide. Veuillez réessayer.")
        finally:
            stop_monitor_mode(self.monitor_interface)
            print("\n[+] Script terminé.")

if __name__ == "__main__":
    app = Application()
    app.run()
