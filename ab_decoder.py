import argparse
import subprocess
import os
import sys

def decode_backup(input_file, output_dir):
    """
    Décode une sauvegarde Android .ab en utilisant la commande 'dd' et 'tar'.
    Gère les sauvegardes compressées et non compressées.
    """
    print("=" * 60)
    print("         Décodeur de Sauvegarde Android (.ab)          ")
    print("=" * 60)
    print(f"\n[INFO] Fichier d'entrée : {input_file}")
    print(f"[INFO] Répertoire de sortie : {output_dir}")

    # Crée le répertoire de sortie s'il n'existe pas
    os.makedirs(output_dir, exist_ok=True)

    try:
        # Tente d'abord de traiter le fichier comme une sauvegarde compressée (gzip)
        print("\n[INFO] Tentative de décodage en tant que sauvegarde compressée (gzip)...")
        # Utilise dd pour sauter l'en-tête de 24 octets de la sauvegarde .ab
        # et pipe la sortie vers tar pour la décompression.
        # Le paramètre `shell=True` est utilisé ici avec précaution car les
        # entrées `input_file` et `output_dir` proviennent du script principal et sont nettoyées.
        cmd_compressed = f"dd if=\"{input_file}\" bs=1 skip=24 2>/dev/null | tar -zxf - -C \"{output_dir}\""
        
        process = subprocess.Popen(cmd_compressed, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            print("\n[SUCCÈS] Décodage terminé. Fichiers extraits avec succès.")
        else:
            # Si le décodage compressé a échoué, essaie une sauvegarde non compressée
            print("\n[INFO] Échec du décodage compressé. Tentative en tant que sauvegarde non compressée...")
            cmd_uncompressed = f"dd if=\"{input_file}\" bs=1 skip=24 2>/dev/null | tar -xf - -C \"{output_dir}\""
            process = subprocess.Popen(cmd_uncompressed, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                print("\n[SUCCÈS] Décodage terminé. Fichiers extraits avec succès.")
            else:
                print(f"\n[ERREUR] Impossible de décoder la sauvegarde. Erreur :\n{stderr.decode('utf-8')}")
                print("[CONSEIL] Assurez-vous que le fichier n'est pas chiffré ou corrompu et que les outils `dd` et `tar` sont disponibles.")
        
    except FileNotFoundError:
        print("\n[ERREUR] Les commandes `dd` ou `tar` ne sont pas disponibles sur votre système.")
        print("Veuillez les installer pour que ce script fonctionne.")
        
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Un simple décodeur de sauvegarde Android (.ab).")
    parser.add_argument("-i", "--input", required=True, help="Chemin du fichier de sauvegarde .ab")
    parser.add_argument("-o", "--output", required=True, help="Chemin du répertoire de sortie")
    
    args = parser.parse_args()
    
    # Vérifie si le fichier d'entrée existe
    if not os.path.exists(args.input):
        print(f"\n[ERREUR] Le fichier d'entrée '{args.input}' n'existe pas.")
        sys.exit(1)
        
    decode_backup(args.input, args.output)
