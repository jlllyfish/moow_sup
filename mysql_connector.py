"""
Module d'intégration avec MySQL pour Démarches Simplifiées.
Ce module gère la communication avec la base de données MySQL pour récupérer
les données des apprenants ERASMIP.
"""

import os
import mysql.connector
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
import json

# Charger les variables d'environnement
load_dotenv()

# Configuration MySQL
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER", os.getenv("USERNAME_MYSQL"))  # Prise en charge des deux variantes
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", os.getenv("PASSWORD_MYSQL"))
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_TABLE = os.getenv("MYSQL_TABLE", "ENSFEA_ERASMIP")  # Table ERASMIP par défaut

# Définition des noms de colonnes spécifiques
COL_ID = "dossier_id"
COL_DOSSIER_NUMBER = "dossier_number"
COL_CIVILITE = "civilite"
COL_NOM = "nom"
COL_PRENOM = "prenom"
COL_DATE_NAISSANCE = "date_naissance"
COL_FORMAT_MOBILITE = "format_mobilite"
COL_MOBILITE_APPRENANT = "mobilite_apprenant" 
COL_DATE_DEPART = "date_depart"
COL_DATE_RETOUR = "date_retour"
COL_PAYS_ACCUEIL = "pays_accueil"
COL_STATUT_PARTICIPANT = "statut_participant"
COL_DATE_DEPOT = "dateDepot"
COL_EPLEFPA = "etablissement"  # Colonne établissement


class MySQLClient:
    def __init__(self, host, user, password, database, port=3306):
        """
        Initialise un client pour la base de données MySQL.
        
        Args:
            host: Hôte de la base de données MySQL
            user: Nom d'utilisateur pour la connexion
            password: Mot de passe pour la connexion
            database: Nom de la base de données
            port: Port de connexion MySQL (par défaut 3306)
        """
        self.config = {
            "host": host,
            "user": user,
            "password": password,
            "database": database,
            "port": port
        }
        self.connection = None
        self.cursor = None

    def connect(self):
        """
        Établit une connexion à la base de données MySQL.
        
        Returns:
            bool: True si la connexion est réussie, False sinon
        """
        try:
            self.connection = mysql.connector.connect(**self.config)
            self.cursor = self.connection.cursor(dictionary=True)
            return True
        except mysql.connector.Error as err:
            print(f"Erreur de connexion à MySQL: {err}")
            return False

    def disconnect(self):
        """
        Ferme la connexion à la base de données MySQL.
        """
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    def execute_query(self, query, params=None):
        """
        Exécute une requête SQL et retourne les résultats.
        
        Args:
            query: Requête SQL à exécuter
            params: Paramètres pour la requête (optionnel)
            
        Returns:
            list: Liste des résultats ou None en cas d'erreur
        """
        try:
            if not self.connection or not self.connection.is_connected():
                if not self.connect():
                    return None

            self.cursor.execute(query, params or ())
            return self.cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"Erreur lors de l'exécution de la requête: {err}")
            return None


# Fonctions d'interface pour notre application
def get_mysql_client():
    """
    Crée et configure un client MySQL avec les paramètres de l'environnement.
    
    Returns:
        MySQLClient: Client MySQL configuré
    """
    return MySQLClient(
        MYSQL_HOST,
        MYSQL_USER,
        MYSQL_PASSWORD,
        MYSQL_DATABASE,
        MYSQL_PORT
    )


# Fonctions de transformation des données EFP
def transformer_date(date_val):
    """Transforme une date au format ISO8601"""
    if not date_val or date_val == "None" or date_val == "null":
        return None
        
    try:
        # Essai de différents formats de date possibles
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
                    return str(date_val)  # Retourne la valeur telle quelle si format inconnu
    except Exception as e:
        print(f"Erreur lors de la conversion de la date '{date_val}': {e}")
        return None


def rechercher_dossier_par_nom_et_numero(nom, numero_dossier):
    """
    Recherche un dossier ERASMIP dans la table qui correspond au nom et au numéro.
    
    Args:
        nom (str): Nom de famille 
        numero_dossier (str): Numéro du dossier
    
    Returns:
        tuple: (success, result) où result est les données du dossier ou un message d'erreur
    """
    try:
        print(f"Recherche de dossier avec nom: {nom} et numéro: {numero_dossier}")
        client = get_mysql_client()
        
        if not client.connect():
            return False, "Impossible de se connecter à la base de données"
        
        # Recherche par nom et numéro de dossier
        query = f"""
        SELECT * 
        FROM {MYSQL_TABLE} 
        WHERE {COL_NOM} = %s AND {COL_DOSSIER_NUMBER} = %s
        """
        
        results = client.execute_query(query, (nom, numero_dossier))
        client.disconnect()
        
        if not results:
            # Si aucun résultat, essayer de filtrer seulement par numéro de dossier
            client.connect()
            query_num = f"""
            SELECT * 
            FROM {MYSQL_TABLE} 
            WHERE {COL_DOSSIER_NUMBER} = %s
            """
            results_num = client.execute_query(query_num, (numero_dossier,))
            client.disconnect()
            
            if results_num:
                print(f"Trouvé dossier par numéro, mais le nom ne correspond pas.")
                return False, "Le numéro de dossier existe, mais le nom ne correspond pas."
            else:
                print("Aucun dossier trouvé avec ce numéro.")
                return False, "Aucun dossier trouvé avec ce numéro."
        
        # Prendre le premier dossier correspondant
        dossier = results[0]
        
        # Log des données pour débogage
        print(f"Données brutes trouvées dans MySQL:")
        for k, v in dossier.items():
            if k in [COL_CIVILITE, COL_NOM, COL_PRENOM, COL_DATE_NAISSANCE, COL_FORMAT_MOBILITE, 
                    COL_MOBILITE_APPRENANT, COL_DATE_DEPART, COL_DATE_RETOUR, COL_PAYS_ACCUEIL]:
                print(f"  {k}: {v} (type: {type(v)})")
        
        # Formater le résultat
        result = {
            "id": dossier.get(COL_ID),
            "fields": dossier
        }
        
        print(f"Dossier trouvé avec ID: {result['id']}")
        return True, result
    
    except Exception as e:
        print(f"Exception lors de la recherche du dossier: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, f"Exception: {str(e)}"


def rechercher_dossier_par_nom_et_etablissement(nom, etablissement, numero_dossier=None):
    """
    Recherche un dossier ERASMIP dans la table qui correspond au nom et à l'établissement.
    Le numéro de dossier est optionnel.
    
    Args:
        nom (str): Nom de famille
        etablissement (str): Nom de l'établissement (EPLEFPA)
        numero_dossier (str, optional): Numéro du dossier, optionnel
        
    Returns:
        tuple: (success, result) où result est les données du dossier ou un message d'erreur
    """
    try:
        print(f"Recherche de dossier avec nom: {nom}, établissement: {etablissement}, numéro: {numero_dossier or 'Non fourni'}")
        client = get_mysql_client()
        
        if not client.connect():
            return False, "Impossible de se connecter à la base de données"
        
        # Construire la requête en fonction des paramètres fournis
        if numero_dossier:
            # Si le numéro de dossier est fourni, l'utiliser avec le nom et l'établissement
            query = f"""
            SELECT * 
            FROM {MYSQL_TABLE} 
            WHERE {COL_NOM} = %s AND {COL_EPLEFPA} = %s AND {COL_DOSSIER_NUMBER} = %s
            """
            params = (nom, etablissement, numero_dossier)
        else:
            # Sinon, rechercher uniquement par nom et établissement
            query = f"""
            SELECT * 
            FROM {MYSQL_TABLE} 
            WHERE {COL_NOM} = %s AND {COL_EPLEFPA} = %s
            """
            params = (nom, etablissement)
        
        results = client.execute_query(query, params)
        client.disconnect()
        
        if not results:
            return False, "Aucun dossier trouvé avec ces critères."
        
        # Si plusieurs résultats, les renvoyer tous pour que l'utilisateur puisse choisir
        if len(results) > 1:
            dossiers = []
            for dossier in results:
                dossier_info = {
                    "id": dossier.get(COL_ID),
                    "numero": dossier.get(COL_DOSSIER_NUMBER),
                    "nom": dossier.get(COL_NOM),
                    "prenom": dossier.get(COL_PRENOM),
                    "etablissement": dossier.get(COL_EPLEFPA),
                    "date_depot": dossier.get(COL_DATE_DEPOT),
                    "fields": dossier
                }
                dossiers.append(dossier_info)
            
            print(f"Plusieurs dossiers trouvés ({len(dossiers)}) pour ces critères.")
            return True, {"multiple": True, "dossiers": dossiers}
        
        # Sinon, renvoyer le dossier unique
        dossier = results[0]
        print(f"Dossier unique trouvé avec ID: {dossier.get(COL_ID)}")
        
        # Log des données pour débogage
        print(f"Données brutes trouvées dans MySQL:")
        for k, v in dossier.items():
            if k in [COL_CIVILITE, COL_NOM, COL_PRENOM, COL_DATE_NAISSANCE, COL_FORMAT_MOBILITE, 
                    COL_MOBILITE_APPRENANT, COL_DATE_DEPART, COL_DATE_RETOUR, COL_PAYS_ACCUEIL]:
                print(f"  {k}: {v} (type: {type(v)})")
        
        # Formater le résultat
        result = {
            "id": dossier.get(COL_ID),
            "fields": dossier
        }
        
        return True, result
    
    except Exception as e:
        print(f"Exception lors de la recherche du dossier: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, f"Exception: {str(e)}"


def obtenir_liste_etablissements():
    """
    Récupère la liste des établissements disponibles dans la base de données.
    
    Returns:
        tuple: (success, result) où result est la liste des établissements ou un message d'erreur
    """
    try:
        client = get_mysql_client()
        
        if not client.connect():
            return False, "Impossible de se connecter à la base de données"
        
        query = f"""
        SELECT DISTINCT {COL_EPLEFPA} 
        FROM {MYSQL_TABLE} 
        WHERE {COL_EPLEFPA} IS NOT NULL AND {COL_EPLEFPA} != ''
        ORDER BY {COL_EPLEFPA}
        """
        
        results = client.execute_query(query)
        client.disconnect()
        
        if not results:
            return False, "Aucun établissement trouvé dans la base de données."
        
        # Extraire la liste des établissements
        etablissements = [r.get(COL_EPLEFPA) for r in results if r.get(COL_EPLEFPA)]
        
        return True, etablissements
    
    except Exception as e:
        print(f"Exception lors de la récupération des établissements: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, f"Exception: {str(e)}"

def obtenir_etablissements_par_nom(nom):
    """
    Récupère la liste des établissements associés à un nom d'apprenant donné.
    
    Args:
        nom (str): Nom de famille de l'apprenant
    
    Returns:
        tuple: (success, result) où result est la liste des établissements ou un message d'erreur
    """
    try:
        client = get_mysql_client()
        
        if not client.connect():
            return False, "Impossible de se connecter à la base de données"
        
        # Recherche des établissements pour ce nom
        query = f"""
        SELECT DISTINCT {COL_EPLEFPA} 
        FROM {MYSQL_TABLE} 
        WHERE {COL_NOM} = %s AND {COL_EPLEFPA} IS NOT NULL AND {COL_EPLEFPA} != ''
        ORDER BY {COL_EPLEFPA}
        """
        
        results = client.execute_query(query, (nom,))
        client.disconnect()
        
        if not results or len(results) == 0:
            return False, "Aucun établissement trouvé pour ce nom d'apprenant."
        
        # Extraire la liste des établissements
        etablissements = [r.get(COL_EPLEFPA) for r in results if r.get(COL_EPLEFPA)]
        
        return True, etablissements
    
    except Exception as e:
        print(f"Exception lors de la récupération des établissements par nom: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, f"Exception: {str(e)}"

def rechercher_apprenants_par_date_et_etablissement(date_depart, etablissement):
    """
    Recherche les apprenants par date de départ et établissement.
    
    Args:
        date_depart (str): Date de départ dans n'importe quel format supporté
        etablissement (str): Nom de l'établissement (EPLEFPA)
        
    Returns:
        tuple: (success, result) où result est la liste des apprenants ou un message d'erreur
    """
    try:
        # Transformer la date au format ISO8601 pour la requête SQL
        date_depart_iso = transformer_date(date_depart)
        
        if not date_depart_iso:
            return False, "Format de date non valide"
        
        print(f"Recherche d'apprenants avec date de départ: {date_depart_iso} et établissement: {etablissement}")
        client = get_mysql_client()
        
        if not client.connect():
            return False, "Impossible de se connecter à la base de données"
        
        # Recherche des apprenants pour cette date et cet établissement
        query = f"""
        SELECT * 
        FROM {MYSQL_TABLE} 
        WHERE {COL_DATE_DEPART} = %s AND {COL_EPLEFPA} = %s
        """
        
        results = client.execute_query(query, (date_depart_iso, etablissement))
        client.disconnect()
        
        if not results:
            return False, "Aucun apprenant trouvé pour cette date et cet établissement."
        
        # Préparer la liste des apprenants
        apprenants = []
        for dossier in results:
            # Mapper les données pour l'API
            mapped_data = mapper_donnees_mobilite(dossier)
            # Ajouter l'ID et le numéro de dossier pour référence
            mapped_data["id"] = dossier.get(COL_ID)
            mapped_data["dossier_number"] = dossier.get(COL_DOSSIER_NUMBER)
            apprenants.append(mapped_data)
        
        print(f"Trouvé {len(apprenants)} apprenant(s)")
        return True, apprenants
    
    except Exception as e:
        print(f"Exception lors de la recherche des apprenants: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, f"Exception: {str(e)}"


def mapper_donnees_mobilite(dossier_fields):
    """
    Mappe les données d'un apprenant pour l'API selon le script ERASMIP.
    Utilise exactement la même méthode que dans le script paste.txt.
    
    Args:
        dossier_fields (dict): Champs du dossier extraits de la base de données
        
    Returns:
        dict: Dictionnaire avec les données mappées pour l'API
    """
    # Extraction des données brutes
    civilite = dossier_fields.get(COL_CIVILITE, "")
    nom = dossier_fields.get(COL_NOM, "")
    prenom = dossier_fields.get(COL_PRENOM, "")
    date_naissance = dossier_fields.get(COL_DATE_NAISSANCE)
    format_mobilite = dossier_fields.get(COL_FORMAT_MOBILITE, "")
    mobilite_apprenant = dossier_fields.get(COL_MOBILITE_APPRENANT, "")
    date_depart = dossier_fields.get(COL_DATE_DEPART)
    date_retour = dossier_fields.get(COL_DATE_RETOUR)
    pays_accueil = dossier_fields.get(COL_PAYS_ACCUEIL, "")
    statut_participant = dossier_fields.get(COL_STATUT_PARTICIPANT, "")
    etablissement = dossier_fields.get(COL_EPLEFPA, "")
    
    # Log pour débogage des dates
    print(f"Date de naissance brute: {date_naissance}")
    print(f"Date de départ brute: {date_depart}")
    print(f"Date de retour brute: {date_retour}")
    
    # Définir le statut de la mobilité hybride
    mobilite_hybride = "Oui" if format_mobilite == "Mobilité hybride" else "Non"
    
    # Déterminer le type de mobilité
    type_mobilite_val = ""
    if mobilite_apprenant == "Mobilité de stage (SMT)":
        type_mobilite_val = "Stage"
    elif mobilite_apprenant == "Mobilité d'étude (SMS)":
        type_mobilite_val = "Etudes"
    else:
        # Détermination par défaut si non précisé
        type_mobilite_val = "Stage"  # Valeur par défaut
    
    # Mappage du type de mobilité spécifique
    valeur_mobilite_apprenant = None
    if mobilite_apprenant == 'Mobilité de stage (SMT)':
        valeur_mobilite_apprenant = 'Mobilité d\'apprentissage de courte durée'
    else:
        # Valeur par défaut si non renseigné
        valeur_mobilite_apprenant = 'Mobilité d\'apprentissage de courte durée'
    
    # Déterminer si l'apprenant est apprenti
    est_apprenti = "true" if statut_participant and statut_participant.lower() == "apprenti" else "false"
    
    # Construction du dictionnaire de résultats
    data_mappee = {
        # Données originales brutes (nécessaires pour ds_prefiller.py)
        "civilite": civilite,
        "nom": nom,
        "prenom": prenom,
        "date_naissance": date_naissance,
        "format_mobilite": format_mobilite,
        "mobilite_apprenant": mobilite_apprenant,
        "date_depart": date_depart,
        "date_retour": date_retour,
        "pays_accueil": pays_accueil,
        "statut_participant": statut_participant,
        "etablissement": etablissement,  # Ajout de l'établissement
        
        # Données transformées (pour l'affichage et le mapping)
        "mobilite_hybride": mobilite_hybride,
        "type_mobilite_val": type_mobilite_val,
        "valeur_mobilite_apprenant": valeur_mobilite_apprenant,
        "est_apprenti": est_apprenti,
        "region": "Occitanie",  # Valeur fixe
        "statut": "Étudiant"     # Valeur fixe
    }
    
    # Log de débogage des données mappées
    print("Données mappées:")
    for k, v in data_mappee.items():
        print(f"  {k}: {v}")
    
    return data_mappee


def valider_combinaison_nom_etablissement(nom, etablissement, numero_dossier=None):
    """
    Vérifie si la combinaison nom + établissement existe dans la base MySQL
    et récupère les données pour ERASMIP. Le numéro de dossier est optionnel.
    
    Args:
        nom (str): Nom de famille
        etablissement (str): Nom de l'établissement (EPLEFPA)
        numero_dossier (str, optional): Numéro du dossier, optionnel
    
    Returns:
        tuple: (success, result) où result est un dictionnaire de données mappées ou un message d'erreur
    """
    print(f"Validation de la combinaison nom: {nom}, établissement: {etablissement}, numéro: {numero_dossier or 'Non fourni'}")
    
    # Rechercher le dossier
    success_dossier, result_dossier = rechercher_dossier_par_nom_et_etablissement(nom, etablissement, numero_dossier)
    
    if not success_dossier:
        return False, result_dossier
    
    # Vérifier si plusieurs dossiers ont été trouvés
    if isinstance(result_dossier, dict) and result_dossier.get("multiple", False):
        return True, result_dossier  # Renvoyer la liste des dossiers
    
    # Extraire les champs du dossier
    dossier_fields = result_dossier.get("fields", {})
    
    # Mapper les données pour ERASMIP
    mapped_data = mapper_donnees_mobilite(dossier_fields)
    
    # Log complet des données mappées
    print(f"Données mappées complètes: {json.dumps(mapped_data, default=str)}")
    
    return True, mapped_data


def valider_combinaison_nom_et_numero(nom, numero_dossier):
    """
    Vérifie si la combinaison nom + numéro de dossier existe dans la base MySQL
    et récupère les données pour ERASMIP.
    
    Args:
        nom (str): Nom de famille
        numero_dossier (str): Numéro du dossier
    
    Returns:
        tuple: (success, result) où result est un dictionnaire de données mappées ou un message d'erreur
    """
    print(f"Validation de la combinaison nom: {nom} et numéro de dossier: {numero_dossier}")
    
    # Rechercher le dossier
    success_dossier, result_dossier = rechercher_dossier_par_nom_et_numero(nom, numero_dossier)
    if not success_dossier:
        return False, result_dossier
    
    # Extraire les champs du dossier
    dossier_fields = result_dossier.get("fields", {})
    
    # Mapper les données pour ERASMIP
    mapped_data = mapper_donnees_mobilite(dossier_fields)
    
    # Log complet des données mappées
    print(f"Données mappées complètes: {json.dumps(mapped_data, default=str)}")
    
    return True, mapped_data


def test_mysql_connection():
    """
    Teste la connexion à la base de données MySQL.
    
    Returns:
        tuple: (success, result) où result est un message de succès ou d'erreur
    """
    try:
        client = get_mysql_client()
        
        # Afficher les informations de connexion
        print(f"Hôte: {client.config['host']}")
        print(f"Base de données: {client.config['database']}")
        
        if not client.connect():
            return False, "Impossible de se connecter à la base de données MySQL"
        
        # Tester la présence de la table ERASMIP
        query = f"SHOW TABLES LIKE '{MYSQL_TABLE}'"
        result = client.execute_query(query)
        client.disconnect()
        
        if not result:
            return False, f"La table {MYSQL_TABLE} n'existe pas dans la base de données"
        
        return True, f"Connexion réussie à MySQL. Table {MYSQL_TABLE} disponible."
    
    except Exception as e:
        return False, f"Exception: {str(e)}"


# Code pour tester le module si exécuté directement
if __name__ == "__main__":
    # Tester la connexion à la base de données MySQL
    print("\n=== Test de connexion à MySQL ===")
    success, result = test_mysql_connection()
    print(f"Résultat: {'Succès' if success else 'Échec'} - {result}")
    
    if success:
        # Test avec des données factices
        print("\n=== Test de recherche avec des données factices ===")
        success, result = valider_combinaison_nom_etablissement("STEFANIDES", "EPLEFPA de Test")  # Exemple
        print(f"Résultat: {'Succès' if success else 'Échec'}")
        if success:
            print("Données récupérées:")
            for key, value in result.items():
                print(f"  {key}: {value}")