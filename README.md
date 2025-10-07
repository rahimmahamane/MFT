# Boîte à outils de Pentesting Wi-Fi avec IA

Ce projet est une boîte à outils basée sur Python pour les tests d'intrusion Wi-Fi. Il intègre une IA pour l'analyse de paquets et inclut plusieurs modules d'attaque à des fins éducatives.

## Fonctionnalités

-   **Scanner Wi-Fi :** Détecte les points d'accès et les clients connectés.
-   **Détecteur d'anomalies IA :** Utilise un modèle Isolation Forest pour détecter les anomalies dans le trafic réseau.
-   **Attaque de désauthentification :** Envoie des trames de désauthentification pour déconnecter un client d'un réseau.
-   **Attaque par inondation de balises (Beacon Flood) :** Génère une multitude de faux points d'accès.
-   **Interface en ligne de commande interactive :** Interface en ligne de commande facile à utiliser.

## Avertissement

Cet outil est destiné à des fins éducatives et éthiques uniquement. Utilisez-le exclusivement sur des réseaux pour lesquels vous avez une autorisation écrite explicite. Toute utilisation non autorisée est illégale et punissable par la loi. Les développeurs ne sont pas responsables de toute mauvaise utilisation de cet outil.

## Installation

### Prérequis

-   **Python 3.x**
-   **Suite aircrack-ng :** Cet outil est nécessaire pour gérer le mode moniteur sur les interfaces sans fil. Vous pouvez l'installer sur les systèmes basés sur Debian avec :
    ```bash
    sudo apt-get update
    sudo apt-get install aircrack-ng
    ```

### Dépendances

Le projet nécessite les bibliothèques Python suivantes :

-   `scapy`
-   `scikit-learn`
-   `pandas`

Vous pouvez les installer en utilisant pip et le fichier `requirements.txt` :

```bash
pip install -r requirements.txt
```

## Utilisation

Le script doit être exécuté avec les privilèges root pour accéder à l'interface Wi-Fi en mode moniteur.

1.  **Accédez au répertoire `app` :**
    ```bash
    cd app1/app
    ```

2.  **Exécutez le script principal :**
    ```bash
    sudo python3 main.py
    ```

3.  **Suivez le menu interactif :**
    -   Choisissez une interface Wi-Fi.
    -   Sélectionnez une option dans le menu principal (détecteur IA, attaques, etc.).

## Structure du projet

```
app1/
├── app/
│   ├── __init__.py
│   ├── ai_detector.py
│   ├── attacks.py
│   ├── scanner.py
│   ├── utils.py
│   └── main.py
├── tests/
│   ├── __init__.py
│   └── test_scanner.py
├── requirements.txt
└── README.md
```