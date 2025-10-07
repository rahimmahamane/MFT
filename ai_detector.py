# -*- coding: utf-8 -*-

import pandas as pd
from sklearn.ensemble import IsolationForest
from scapy.all import sniff, Dot11

class AnomalyDetector:
    """A class to detect network anomalies using Isolation Forest."""
    def __init__(self, contamination=0.05):
        self.model = IsolationForest(contamination=contamination, random_state=42)
        self.features_df = pd.DataFrame()
        self.is_trained = False

    def add_packet_data(self, packet_list):
        """Adds packet data to the dataframe for training."""
        self.features_df = pd.DataFrame(packet_list)
        self.features_df = self.features_df.fillna(0)

    def train_model(self):
        """Trains the Isolation Forest model."""
        if len(self.features_df) > 20:
            print("\n[+] Training AI model on collected data...")
            self.model.fit(self.features_df)
            self.is_trained = True
            print("[+] AI model trained successfully.")
        else:
            print("\n[-] Not enough data to train the AI model. Capture more packets.")

    def predict_anomaly(self, new_data):
        """Predicts if a new packet is an anomaly."""
        if self.is_trained:
            # Ensure columns match the training data
            new_df = pd.DataFrame([new_data], columns=self.features_df.columns)
            prediction = self.model.predict(new_df.fillna(0))
            return prediction[0] == -1
        return False

def run_ai_detector(interface):
    """Runs the AI-based anomaly detection process."""
    detector = AnomalyDetector()
    packets_for_training = []

    def training_packet_handler(packet):
        """Packet handler for collecting training data."""
        if packet.haslayer(Dot11):
            # Extract features from the packet
            rssi = packet.dBm_AntSignal if hasattr(packet, 'dBm_AntSignal') else -100
            data = {
                'packet_size': len(packet),
                'rssi': rssi,
                'is_beacon': 1 if packet.subtype == 8 else 0,
                'is_probe_req': 1 if packet.subtype == 4 else 0,
                'is_deauth': 1 if packet.subtype == 12 else 0
            }
            packets_for_training.append(data)

    try:
        duration = int(input("Enter data collection duration for training (in seconds, e.g., 60): "))
    except ValueError:
        print("[-] Invalid input. Please enter a number.")
        return

    print(f"[*] Starting data collection for AI training ({duration}s)...")
    sniff(iface=interface, prn=training_packet_handler, timeout=duration)
    
    detector.add_packet_data(packets_for_training)
    detector.train_model()

    if not detector.is_trained:
        return

    print("\n[*] Starting real-time anomaly detection. (Press CTRL+C to stop)")
    
    def anomaly_handler(packet):
        """Packet handler for detecting anomalies in real-time."""
        if packet.haslayer(Dot11):
            rssi = packet.dBm_AntSignal if hasattr(packet, 'dBm_AntSignal') else -100
            data = {
                'packet_size': len(packet),
                'rssi': rssi,
                'is_beacon': 1 if packet.subtype == 8 else 0,
                'is_probe_req': 1 if packet.subtype == 4 else 0,
                'is_deauth': 1 if packet.subtype == 12 else 0
            }
            if detector.predict_anomaly(data):
                print(f" [!!!] ANOMALY DETECTED: {packet.summary()}")

    try:
        sniff(iface=interface, prn=anomaly_handler, store=0)
    except KeyboardInterrupt:
        print("\n[+] Stopping detection.")
