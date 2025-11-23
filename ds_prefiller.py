"""
Module de pré-remplissage pour Démarches Simplifiées.
Ce module gère la communication avec l'API Démarches Simplifiées
pour générer des URLs vers des dossiers pré-remplis uniquement pour ERASMIP.
"""

import requests
import os
from dotenv import load_dotenv
import json
from datetime import datetime

# Charger les variables d'environnement
load_dotenv()

# Configuration API Démarches Simplifiées
DEMARCHE_ID = os.getenv("DEMARCHE_ID", "70018")  # ID de démarche ERASMIP
API_TOKEN = os.getenv("API_TOKEN")  # Token API

def transformer_date(date_val):
    """
    Transforme une date au format ISO8601.
    Reprend exactement la logique du script original.
    """
    if not date_val or date_val == "None" or date_val == "null":
        return None
        
    try:
        # Essayer différents formats de dates possibles
        try:
            return datetime.strptime(str(date_val), "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            try:
                return datetime.strptime(str(date_val), "%d/%m/%Y").strftime("%Y-%m-%d")
            except ValueError:
                try:
                    # Format ISO avec heure
                    return datetime.strptime(str(date_val), "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d")
                except ValueError:
                    print(f"Format de date non reconnu: {date_val}")
                    return str(date_val)  # Retourner la valeur telle quelle si format inconnu
    except Exception as e:
        print(f"Erreur lors de la conversion de la date '{date_val}': {e}")
        return None

def generate_prefilled_url(data_dict):
    """
    Génère une URL vers un dossier pré-rempli sur Démarches Simplifiées pour ERASMIP.
    Suit exactement la structure du script original.
    
    Args:
        data_dict (dict): Dictionnaire des données du formulaire
        
    Returns:
        tuple: (success, result) où result est l'URL ou un message d'erreur
    """
    # Vérifier la présence du token API
    if not API_TOKEN:
        return False, "Token API non trouvé. Vérifiez votre fichier .env"
    
    # Extraire les données et appliquer les transformations
    civilite = data_dict.get("civilite", "")
    # Normaliser la civilité : "M" -> "M.", "Mme" reste "Mme"
    if civilite == "M":
        civilite = "M."
    nom = data_dict.get("nom", "")
    prenom = data_dict.get("prenom", "")
    date_naissance = transformer_date(data_dict.get("date_naissance"))
    format_mobilite = data_dict.get("format_mobilite", "")
    mobilite_apprenant = data_dict.get("mobilite_apprenant", "")
    date_depart = transformer_date(data_dict.get("date_depart"))
    date_retour = transformer_date(data_dict.get("date_retour"))
    pays_accueil = data_dict.get("pays_accueil", "")
    statut_participant = data_dict.get("statut_participant", "")
    
    # Log pour débogage
    print(f"Date de naissance après transformation: {date_naissance}")
    print(f"Date de départ après transformation: {date_depart}")
    print(f"Date de retour après transformation: {date_retour}")
    print(f"Mobilité apprenant: {mobilite_apprenant}")
    
    # Définir le statut de la mobilité hybride (convertir en true/false pour les champs booléens)
    mobilite_hybride = "true" if format_mobilite == "Mobilité hybride" else "false"
    
    # Logique simplifiée pour le type de mobilité
    # Pour ce champ, on utilise toujours "Stage" comme valeur par défaut,
    # quelle que soit la valeur de mobilite_apprenant
    type_mobilite_val = "Stage"
    
    # Logique pour valeur_mobilite_apprenant
    # Les deux valeurs possibles sont "Mobilité d'apprentissage de courte durée" et "Concours de compétence"
    if mobilite_apprenant == "Concours de compétence":
        valeur_mobilite_apprenant = "Concours de compétence"
    else:
        # Valeur par défaut ou si mobilité de stage
        valeur_mobilite_apprenant = "Mobilité d'apprentissage de courte durée"
    
    # Déterminer si l'apprenant est apprenti (même logique que script original)
    est_apprenti = "true" if statut_participant and statut_participant.lower() == "apprenti" else "false"
    
    # Déterminer le statut en fonction de est_apprenti
    statut_apprenant = "Apprenti" if est_apprenti == "true" else "Étudiant"
    
    # Construction du dictionnaire de données EXACT comme dans le script original
    # Reproduire exactement la structure pour être sûr que ça fonctionne
    donnees_mappees = {
        "champ_Q2hhbXAtMzM0ODUwMg": "Occitanie",  # Valeur fixe "Occitanie" au lieu de civilité
        "champ_Q2hhbXAtMTAzMjQ0Ng": civilite,  # Civilité
        "champ_Q2hhbXAtNzg1Mjcx": nom,       # Nom
        "champ_Q2hhbXAtNzg1Mjcy": prenom,    # Prénom
        "champ_Q2hhbXAtNjI2NjMx": date_naissance,  # Date naissance
        "champ_Q2hhbXAtMjc4NDc3MQ": valeur_mobilite_apprenant,  # Mobilité apprenant
        "champ_Q2hhbXAtMzAwMjA2MA": est_apprenti,  # Est apprenti (true/false)
        "champ_Q2hhbXAtMTAzMjQ0NQ": statut_apprenant,  # Statut basé sur est_apprenti
        "champ_Q2hhbXAtNDcwODc3MA": "true",  # Champ booléen - doit être "true" au lieu de "Oui"
        "champ_Q2hhbXAtNDcwODc3MQ": "true",  # Champ booléen - doit être "true" au lieu de "Oui"
        "champ_Q2hhbXAtMjE0MTIxNg": mobilite_hybride,  # Mobilité hybride (true/false)
        "champ_Q2hhbXAtNzEyMjc0": type_mobilite_val,  # Type de mobilité (toujours "Stage")
        "champ_Q2hhbXAtNjI2Njg2": date_depart,  # Date de départ
        "champ_Q2hhbXAtNjI2Njg4": date_retour,  # Date de retour
        "champ_Q2hhbXAtNDczNTI1MA": "Pays membre de l'Union Européenne",  # Valeur fixe
        "champ_Q2hhbXAtNDczNTAyNg": pays_accueil  # Pays d'accueil
    }
    
    # Filtrer les champs None pour éviter des problèmes d'API
    donnees_filtrees = {k: v for k, v in donnees_mappees.items() if v is not None}
    
    # Afficher le résultat du mapping pour le débogage
    print("\nDonnées mappées pour l'API:")
    print(json.dumps(donnees_filtrees, indent=2, default=str))
    
    # Préparer la requête API
    api_url = f'https://www.demarches-simplifiees.fr/api/public/v1/demarches/{DEMARCHE_ID}/dossiers'
    headers = {
        "Content-Type": "application/json", 
        "Authorization": f"Bearer {API_TOKEN}"
    }
    
    try:
        # Envoyer la requête à l'API
        print(f"Envoi de la requête à l'API: {api_url}")
        response = requests.post(api_url, headers=headers, json=donnees_filtrees)
        
        print(f"Code de réponse: {response.status_code}")
        print(f"Réponse complète: {response.text}")
        
        if response.status_code == 201:
            response_data = response.json()
            return True, response_data.get("dossier_url", "")
        else:
            return False, f"Erreur API DS: {response.text}"
    except Exception as e:
        return False, f"Exception: {str(e)}"

def generate_short_url(data_dict):
    """
    Génère une URL courte et explicite pour un dossier pré-rempli.
    Inclut le nom de l'apprenant dans l'URL pour une meilleure lisibilité.
    
    Args:
        data_dict (dict): Dictionnaire des données du formulaire
        
    Returns:
        tuple: (success, result) où result est l'URL courte ou un message d'erreur
    """
    # D'abord, générer l'URL standard
    success, url = generate_prefilled_url(data_dict)
    
    if not success:
        return False, url  # Renvoyer l'erreur
    
    try:
        # Extraire le nom et le prénom pour un lien plus descriptif
        nom = data_dict.get("nom", "").lower().replace(" ", "-")
        prenom = data_dict.get("prenom", "").lower().replace(" ", "-")
        
        # Construire un identifiant unique en utilisant la date de départ
        date_depart = data_dict.get("date_depart", "")
        if date_depart:
            # Convertir la date en chaîne sans séparateurs pour l'URL
            if isinstance(date_depart, str):
                date_str = date_depart.replace("-", "")[:8]  # Format YYYYMMDD
            else:
                date_str = date_depart.strftime("%Y%m%d")
        else:
            # Utiliser la date actuelle si la date de départ n'est pas disponible
            date_str = datetime.now().strftime("%Y%m%d")
        
        # Créer un identifiant unique pour l'URL
        nom_url = f"{prenom}-{nom}-{date_str}"
        
        # Construire l'URL courte en intégrant l'identifiant
        # Comme nous ne pouvons pas vraiment raccourcir l'URL de Démarches Simplifiées,
        # nous allons simplement ajouter cet identifiant comme ancre à l'URL
        short_url = f"{url}#{nom_url}"
        
        return True, short_url
    except Exception as e:
        print(f"Erreur lors de la génération de l'URL courte: {e}")
        # En cas d'erreur, revenir à l'URL standard
        return success, url

def test_api_connection():
    """
    Teste la connexion à l'API avec des données factices.
    
    Returns:
        tuple: (success, result) où result est l'URL ou un message d'erreur
    """
    # Données de test pour ERASMIP
    test_data = {
        "civilite": "M.",
        "nom": "DUPONT",
        "prenom": "Jean",
        "date_naissance": "1990-01-01",
        "format_mobilite": "Mobilité hybride",
        "mobilite_apprenant": "Concours de compétence",  # Test avec cette valeur
        "date_depart": "2025-03-01",
        "date_retour": "2025-04-30",
        "pays_accueil": "Irlande",
        "statut_participant": "Apprenant"  # Pas un apprenti, donc Élève
    }
    
    return generate_prefilled_url(test_data)

# Code pour tester le module si exécuté directement
if __name__ == "__main__":
    success, result = test_api_connection()
    
    if success:
        print(f"Test réussi ! URL générée : {result}")
    else:
        print(f"Échec du test : {result}")

