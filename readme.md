# **Mobile Forensic Toolkit (MFT)**

### **Auteur : Mahamane**

## **Aperçu du projet**

Ce **Mobile Forensic Toolkit (MFT)** est une solution en ligne de commande conçue pour l'acquisition et l'analyse de preuves numériques sur les appareils mobiles Android et iOS. Cet outil est développé dans le but de fournir aux professionnels de la criminalistique numérique et aux défenseurs un moyen sécurisé, fiable et traçable de traiter les données.

L'application est conçue pour être utilisée dans un cadre légal et éthique, en garantissant l'intégrité de la chaîne de garde grâce à la journalisation et à la vérification de l'intégrité des données (hachage SHA256).

## **Fonctionnalités clés**

* **Gestion des Cas d'Affaires** : Créez et gérez des dossiers d'affaires dédiés pour organiser les preuves.  
* **Acquisition de Données** : Effectuez des sauvegardes complètes (full backups) pour les appareils Android (via ADB) et iOS (via idevicebackup2).  
* **Journalisation Automatique** : Toutes les commandes et actions sont enregistrées dans un journal d'activités pour une traçabilité complète.  
* **Vérification de l'Intégrité (SHA256)** : Les hachages sont calculés automatiquement pour les sauvegardes afin de garantir que les données n'ont pas été altérées.  
* **Extraction Sûre des Fichiers** : Naviguez dans le système de fichiers de manière non-destructive et extrayez des fichiers ou dossiers spécifiques.  
* **Génération de Rapports PDF** : Créez un rapport professionnel qui résume l'affaire, y compris les détails des preuves et le journal de l'activité.  
* **Analyse Assistée par l'IA** : Utilisez un assistant basé sur Gemini pour rechercher des informations critiques dans les données extraites.

## **Avertissement d'utilisation**

**Cet outil est destiné à un usage légal et éthique uniquement.** Le développeur n'est pas responsable de son utilisation illégale.

L'utilisation de cet outil avec sudo ou des privilèges d'administrateur peut être nécessaire pour certaines opérations, mais cela peut entraîner des problèmes de permission et des risques de sécurité. Utilisez-le avec prudence et en toute connaissance de cause.

## **Installation**

### **Dépendances requises**

Pour utiliser le MFT, vous devez installer les dépendances suivantes.

#### **1\. Outils de ligne de commande**

Pour Android :  
Installez la plateforme Android SDK qui inclut adb.

* **macOS** : brew install \--cask android-platform-tools  
* **Linux (Debian/Ubuntu)** : sudo apt-get install android-tools-adb  
* **Windows** : Téléchargez les outils de la plateforme Android à partir du site officiel de Google et ajoutez-les à votre PATH système.

Pour iOS :  
Installez libimobiledevice qui inclut idevicebackup2.

* **macOS** : brew install libimobiledevice  
* **Linux (Debian/Ubuntu)** : sudo apt-get install libimobiledevice-utils  
* **Windows** : Téléchargez les binaires de libimobiledevice à partir de GitHub.

#### **2\. Dépendances Python**

Installez les bibliothèques Python nécessaires en utilisant pip.

pip install reportlab google-generativeai

## **Utilisation**

1. **Exécutez l'application** :  
   python3 mobile_forensic_toolkit1.py

2. Sélectionnez une option :  
   Le menu interactif vous guidera à travers les différentes fonctionnalités.  
   * **Forensique Android** : Pour interagir avec des appareils Android.  
   * **Forensique iPhone** : Pour interagir avec des appareils iOS.  
   * **Analyse de Preuves** : Pour effectuer des recherches de mots-clés et utiliser l'assistant IA.

## **Structure des Fichiers**

```
.
├── ab_decoder.py
├── mobile_forensic_toolkit1.py
└── readme.md
```

## **Contact**

Si vous avez des questions ou des suggestions, n'hésitez pas à me contacter via mon compte Github.
rahim.mahamane@gimail.com