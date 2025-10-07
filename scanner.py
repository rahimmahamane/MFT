# -*- coding: utf-8 -*-

from scapy.all import sniff, Dot11, Dot11Beacon, Dot11Elt

class NetworkScanner:
    """
    Classe pour scanner les réseaux Wi-Fi et les clients.
    """
    def __init__(self, interface):
        """
        Initialise le scanner.

        :param interface: L'interface réseau à utiliser pour le scan.
        """
        self.interface = interface
        self.aps = {}
        self.clients = {}

    def _scan_handler(self, packet):
        """
        Gestionnaire de paquets pour le scan réseau.
        """
        if packet.haslayer(Dot11Beacon):
            bssid = packet[Dot11].addr2
            try:
                ssid = packet[Dot11Elt].info.decode()
            except UnicodeDecodeError:
                ssid = packet[Dot11Elt].info.decode('latin-1')

            if bssid not in self.aps:
                self.aps[bssid] = ssid
                print(f"[AP Détecté] BSSID: {bssid} - SSID: {ssid}")
        elif packet.haslayer(Dot11) and packet.type == 2 and not packet.addr1.startswith("ff:ff:ff"):
            client_mac = packet.addr2
            ap_mac = packet.addr1
            if client_mac not in self.clients and ap_mac in self.aps:
                self.clients[client_mac] = self.aps[ap_mac]
                print(f"  [Client Détecté] MAC: {client_mac} -> Connecté à {self.aps[ap_mac]} ({ap_mac})")

    def scan(self, timeout=60):
        """
        Scanne les réseaux Wi-Fi et les clients.

        :param timeout: La durée du scan en secondes.
        :return: Un tuple contenant les dictionnaires des points d'accès et des clients trouvés.
        """
        self.aps = {}
        self.clients = {}
        print(f"[*] Démarrage du scan sur {self.interface}. Appuyez sur CTRL+C pour arrêter après {timeout} secondes.")
        try:
            sniff(iface=self.interface, prn=self._scan_handler, timeout=timeout)
        except Exception as e:
            print(f"Une erreur est survenue pendant le scan: {e}")
        
        print("\n[+] Scan terminé.")
        print(f"Total d'APs trouvés: {len(self.aps)}")
        print(f"Total de Clients trouvés: {len(self.clients)}")
        return self.aps, self.clients

def scan_networks(interface, timeout=60):
    """
    Fonction pour scanner les réseaux Wi-Fi et les clients.
    """
    scanner = NetworkScanner(interface)
    return scanner.scan(timeout)
