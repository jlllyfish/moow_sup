"""
Module d'intégration avec Grist pour Démarches Simplifiées.
Ce module gère la communication avec l'API Grist pour récupérer
les données des apprenants ERASMIP.
"""

import os
import requests
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
import json
import urllib.parse

# Charger les variables d'environnement
load_dotenv()

# Configuration Grist
GRIST_SERVER = os.getenv("GRIST_SERVER", "https://grist.numerique.gouv.fr")
GRIST_API_KEY = os.getenv("GRIST_API_KEY")
GRIST_DOC_ID = os.getenv("GRIST_DOC_ID")
GRIST_TABLE_ID = os.getenv("GRIST_TABLE_ID", "Table1")  # Nom de la table par défaut

# Définition des noms de colonnes (à adapter selon votre document Grist)
# Ces constantes permettent de mapper les colonnes Grist vers les variables internes
COL_ID = "id"  # ID interne Grist
COL_DOSSIER_NUMBER = "dossier_number"
COL_CIVILITE = "civilite"
COL_NOM = "nom_participant"
COL_PRENOM = "prenom_participant"
COL_DATE_NAISSANCE = "date_de_naissance"
COL_FORMAT_MOBILITE = "format_de_la_mobilite_apprenant"
COL_MOBILITE_APPRENANT = "mobilite_apprenant" 
COL_DATE_DEPART = "date_depart"
COL_DATE_RETOUR = "date_retour"
COL_PAYS_ACCUEIL = "pays_d_accueil"
COL_STATUT_PARTICIPANT = "statut_des_participants_de_la_mobilite"
COL_DATE_DEPOT = "ref_dossiers_date_depot"
COL_EPLEFPA = "votre_etablissement"

class GristClient:
    def __init__(self, api_key, doc_id, table_id, server="https://grist.numerique.gouv.fr"):
        """
        Initialise un client pour l'API Grist.
        
        Args:
            api_key: Clé API Grist
            doc_id: ID du document Grist
            table_id: ID de la table Grist
            server: URL du serveur Grist
        """
        self.api_key = api_key
        self.doc_id = doc_id
        self.table_id = table_id
        self.server = server.rstrip('/')
        self.base_url = f"{self.server}/api/docs/{self.doc_id}/tables/{self.table_id}/records"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def get_records(self, filter_dict=None):
        """
        Récupère les enregistrements de la table Grist, avec filtrage optionnel.
        
        Args:
            filter_dict: Dictionnaire de filtres {colonne: valeur}
            
        Returns:
            list: Liste des enregistrements
        """
        try:
            url = self.base_url
            params = {}
            
            if filter_dict:
                # Grist utilise un format JSON pour le paramètre 'filter'
                # Exemple: ?filter={"nom": ["Dupont"]}
                # Note: Grist attend une liste de valeurs pour chaque colonne dans le filtre
                grist_filter = {k: [v] for k, v in filter_dict.items()}
                params["filter"] = json.dumps(grist_filter)
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            return data.get("records", [])
            
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la requÃªte Grist: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Détails: {e.response.text}")
            return None

# Fonctions d'interface pour notre application
def get_grist_client():
    """
    Crée et configure un client Grist avec les paramètres de l'environnement.
    
    Returns:
        GristClient: Client Grist configuré
    """
    return GristClient(
        GRIST_API_KEY,
        GRIST_DOC_ID,
        GRIST_TABLE_ID,
        GRIST_SERVER
    )

# Fonctions de transformation des données ERASMIP
def transformer_date(date_val):
    """Transforme une date au format ISO8601"""
    if not date_val or date_val == "None" or date_val == "null":
        return None
        
    try:
        # Si c'est un timestamp (Grist renvoie parfois des timestamps)
        # Gère les entiers, flottants, et les chaînes numériques
        if isinstance(date_val, (int, float)):
             return datetime.fromtimestamp(date_val).strftime("%Y-%m-%d")
        
        # Si c'est une chaîne qui ressemble à un nombre (ex: "167888888")
        if isinstance(date_val, str) and date_val.replace('.', '', 1).isdigit():
            try:
                return datetime.fromtimestamp(float(date_val)).strftime("%Y-%m-%d")
            except ValueError:
                pass # Continuer vers les autres formats si ce n'est pas un timestamp valide

        # Convertir en string pour le traitement
        date_str = str(date_val)
        
        # Gérer le format ISO avec timezone (ex: 2025-01-21T18:55:17+01:00)
        if "T" in date_str:
            try:
                # Extraire juste la partie date avant le 'T'
                date_part = date_str.split("T")[0]
                return datetime.strptime(date_part, "%Y-%m-%d").strftime("%Y-%m-%d")
            except ValueError:
                pass
        
        # Essai de différents formats de date possibles
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            try:
                return datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
            except ValueError:
                try:
                    # Format ISO avec heure (sans timezone)
                    return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d")
                except ValueError:
                    print(f"Format de date non reconnu: {date_val}")
                    return str(date_val)
    except Exception as e:
        print(f"Erreur lors de la conversion de la date '{date_val}': {e}")
        return None

def rechercher_dossier_par_nom_et_numero(nom, numero_dossier):
    """
    Recherche un dossier ERASMIP dans Grist qui correspond au nom et au numéro.
    """
    try:
        print(f"Recherche de dossier avec nom: {nom} et numéro: {numero_dossier}")
        client = get_grist_client()
        
        # Filtre pour Grist
        filters = {
            COL_NOM: nom,
            COL_DOSSIER_NUMBER: numero_dossier
        }
        
        records = client.get_records(filters)
        
        if not records:
            # Essayer de filtrer seulement par numéro de dossier pour donner un feedback précis
            records_num = client.get_records({COL_DOSSIER_NUMBER: numero_dossier})
            
            if records_num:
                print(f"Trouvé dossier par numéro, mais le nom ne correspond pas.")
                return False, "Le numéro de dossier existe, mais le nom ne correspond pas."
            else:
                print("Aucun dossier trouvé avec ce numéro.")
                return False, "Aucun dossier trouvé avec ce numéro."
        
        # Prendre le premier dossier correspondant
        record = records[0]
        dossier = record.get("fields", {})
        dossier[COL_ID] = record.get("id") # Ajouter l'ID Grist
        
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

def obtenir_etablissements_par_nom(nom):
    """
    Récupère la liste des établissements associés à un nom d'apprenant donné.
    """
    try:
        client = get_grist_client()
        
        # Filtre par nom
        filters = {COL_NOM: nom}
        
        records = client.get_records(filters)
        
        if not records:
            return False, "Aucun établissement trouvé pour ce nom d'apprenant."
        
        # Extraire la liste des établissements uniques
        etablissements = set()
        for record in records:
            fields = record.get("fields", {})
            etab = fields.get(COL_EPLEFPA)
            if etab:
                etablissements.add(etab)
        
        return True, sorted(list(etablissements))
    
    except Exception as e:
        print(f"Exception lors de la récupération des établissements par nom: {str(e)}")
        return False, f"Exception: {str(e)}"

def obtenir_liste_etablissements():
    """
    Récupère la liste complète des établissements disponibles.
    """
    try:
        client = get_grist_client()
        
        # Récupérer tous les enregistrements (sans filtre)
        records = client.get_records()
        
        if not records:
            return False, "Aucun établissement trouvé dans la base de données."
        
        # Extraire la liste des établissements uniques
        etablissements = set()
        for record in records:
            fields = record.get("fields", {})
            etab = fields.get(COL_EPLEFPA)
            if etab:
                etablissements.add(etab)
        
        return True, sorted(list(etablissements))
    
    except Exception as e:
        print(f"Exception lors de la récupération des établissements: {str(e)}")
        return False, f"Exception: {str(e)}"

def rechercher_dossier_par_nom_et_etablissement(nom, etablissement, numero_dossier=None):
    """
    Recherche un dossier ERASMIP dans Grist qui correspond au nom et à l'établissement.
    """
    try:
        print(f"Recherche de dossier avec nom: {nom}, établissement: {etablissement}, numéro: {numero_dossier or 'Non fourni'}")
        client = get_grist_client()
        
        # Construire le filtre
        filters = {
            COL_NOM: nom,
            COL_EPLEFPA: etablissement
        }
        
        if numero_dossier:
            filters[COL_DOSSIER_NUMBER] = numero_dossier
        
        records = client.get_records(filters)
        
        if not records:
            return False, "Aucun dossier trouvé avec ces critères."
        
        # Si plusieurs résultats
        if len(records) > 1:
            dossiers = []
            for record in records:
                fields = record.get("fields", {})
                dossier_info = {
                    "id": record.get("id"),
                    "numero": fields.get(COL_DOSSIER_NUMBER),
                    "nom": fields.get(COL_NOM),
                    "prenom": fields.get(COL_PRENOM),
                    "etablissement": fields.get(COL_EPLEFPA),
                    "date_depot": fields.get(COL_DATE_DEPOT),
                    "fields": fields
                }
                dossiers.append(dossier_info)
            
            print(f"Plusieurs dossiers trouvés ({len(dossiers)}) pour ces critères.")
            return True, {"multiple": True, "dossiers": dossiers}
        
        # Dossier unique
        record = records[0]
        dossier = record.get("fields", {})
        dossier[COL_ID] = record.get("id")
        
        result = {
            "id": dossier.get(COL_ID),
            "fields": dossier
        }
        
        return True, result
    
    except Exception as e:
        print(f"Exception lors de la recherche du dossier: {str(e)}")
        return False, f"Exception: {str(e)}"

def rechercher_apprenants_par_date_et_etablissement(date_depart, etablissement=None):
    """
    Recherche les apprenants par date de départ et établissement (optionnel).
    Si etablissement est None, recherche tous les apprenants pour cette date.
    """
    try:
        # Transformer la date au format ISO8601 (YYYY-MM-DD)
        date_depart_iso = transformer_date(date_depart)
        
        if not date_depart_iso:
            return False, "Format de date non valide"
        
        print(f"Recherche d'apprenants avec date de départ: {date_depart_iso}" + (f" et établissement: {etablissement}" if etablissement else ""))
        client = get_grist_client()
        
        # Construire les filtres
        filters = {}
        if etablissement:
            filters[COL_EPLEFPA] = etablissement
        
        records = client.get_records(filters) if filters else client.get_records()
        
        if not records:
            return False, "Aucun apprenant trouvé." if not etablissement else "Aucun apprenant trouvé pour cet établissement."
            
        apprenants = []
        for record in records:
            fields = record.get("fields", {})
            
            # Vérifier la date
            record_date = fields.get(COL_DATE_DEPART)
            record_date_iso = transformer_date(record_date)
            
            if record_date_iso == date_depart_iso:
                # Mapper les données
                mapped_data = mapper_donnees_mobilite(fields)
                mapped_data["id"] = record.get("id")
                mapped_data["dossier_number"] = fields.get(COL_DOSSIER_NUMBER)
                apprenants.append(mapped_data)
        
        if not apprenants:
             return False, "Aucun apprenant trouvé pour cette date" + (" et cet établissement." if etablissement else ".")

        print(f"Trouvé {len(apprenants)} apprenant(s)")
        return True, apprenants
    
    except Exception as e:
        print(f"Exception lors de la recherche des apprenants: {str(e)}")
        return False, f"Exception: {str(e)}"

def mapper_donnees_mobilite(dossier_fields):
    """
    Mappe les données d'un apprenant pour l'API selon le script ERASMIP.
    """
    # Extraction des données brutes
    civilite = dossier_fields.get(COL_CIVILITE, "")
    nom = dossier_fields.get(COL_NOM, "")
    prenom = dossier_fields.get(COL_PRENOM, "")
    date_naissance = transformer_date(dossier_fields.get(COL_DATE_NAISSANCE))
    format_mobilite = dossier_fields.get(COL_FORMAT_MOBILITE, "")
    mobilite_apprenant = dossier_fields.get(COL_MOBILITE_APPRENANT, "")
    date_depart = transformer_date(dossier_fields.get(COL_DATE_DEPART))
    date_retour = transformer_date(dossier_fields.get(COL_DATE_RETOUR))
    pays_accueil = dossier_fields.get(COL_PAYS_ACCUEIL, "")
    statut_participant = dossier_fields.get(COL_STATUT_PARTICIPANT, "")
    etablissement = dossier_fields.get(COL_EPLEFPA, "")
    
    # Définir le statut de la mobilité hybride
    mobilite_hybride = "Oui" if format_mobilite == "Mobilité hybride" else "Non"
    
    # Déterminer le type de mobilité
    type_mobilite_val = ""
    if mobilite_apprenant == "Mobilité de stage (SMT)":
        type_mobilite_val = "Stage"
    elif mobilite_apprenant == "Mobilité d'étude (SMS)":
        type_mobilite_val = "Etudes"
    else:
        type_mobilite_val = "Stage"  # Valeur par défaut
    
    # Mappage du type de mobilité spécifique
    valeur_mobilite_apprenant = None
    if mobilite_apprenant == 'Mobilité de stage (SMT)':
        valeur_mobilite_apprenant = 'Mobilité d\'apprentissage de courte durée'
    else:
        valeur_mobilite_apprenant = 'Mobilité d\'apprentissage de courte durée'
    
    # Déterminer si l'apprenant est apprenti
    est_apprenti = "true" if statut_participant and str(statut_participant).lower() == "apprenti" else "false"
    
    # Construction du dictionnaire de résultats
    data_mappee = {
        # Données originales brutes
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
        "etablissement": etablissement,
        
        # Données transformées
        "mobilite_hybride": mobilite_hybride,
        "type_mobilite_val": type_mobilite_val,
        "valeur_mobilite_apprenant": valeur_mobilite_apprenant,
        "est_apprenti": est_apprenti,
        "region": "Occitanie",
        "statut": "étudiant"
    }
    
    return data_mappee

def rechercher_dossier_par_numero(numero_dossier):
    """
    Recherche un dossier uniquement par son numéro.
    """
    try:
        print(f"Recherche de dossier avec numéro: {numero_dossier}")
        client = get_grist_client()
        
        filters = {COL_DOSSIER_NUMBER: numero_dossier}
        records = client.get_records(filters)
        
        if not records:
            return False, "Aucun dossier trouvé avec ce numéro."
        
        if len(records) > 1:
            # Plusieurs dossiers avec le même numéro (ne devrait pas arriver)
            dossiers = []
            for record in records:
                fields = record.get("fields", {})
                dossier_info = {
                    "id": record.get("id"),
                    "numero": fields.get(COL_DOSSIER_NUMBER),
                    "nom": fields.get(COL_NOM),
                    "prenom": fields.get(COL_PRENOM),
                    "etablissement": fields.get(COL_EPLEFPA),
                    "date_depart": fields.get(COL_DATE_DEPART),
                    "fields": fields
                }
                dossiers.append(dossier_info)
            return True, {"multiple": True, "dossiers": dossiers}
        
        # Dossier unique
        record = records[0]
        dossier = record.get("fields", {})
        dossier[COL_ID] = record.get("id")
        
        result = {
            "id": dossier.get(COL_ID),
            "fields": dossier
        }
        
        return True, result
    
    except Exception as e:
        print(f"Exception lors de la recherche du dossier: {str(e)}")
        return False, f"Exception: {str(e)}"

def valider_combinaison_nom_etablissement(nom, etablissement, numero_dossier=None):
    """
    Vérifie si la combinaison nom + établissement existe dans Grist
    et récupère les données pour ERASMIP.
    """
    print(f"Validation de la combinaison nom: {nom}, établissement: {etablissement}, numéro: {numero_dossier or 'Non fourni'}")
    
    # Rechercher le dossier
    success_dossier, result_dossier = rechercher_dossier_par_nom_et_etablissement(nom, etablissement, numero_dossier)
    
    if not success_dossier:
        return False, result_dossier
    
    # Vérifier si plusieurs dossiers ont été trouvés
    if isinstance(result_dossier, dict) and result_dossier.get("multiple", False):
        return True, result_dossier
    
    # Extraire les champs du dossier
    dossier_fields = result_dossier.get("fields", {})
    
    # Ajouter l'établissement aux données mappées
    mapped_data = mapper_donnees_mobilite(dossier_fields)
    mapped_data["etablissement"] = etablissement
    
    return True, mapped_data

def test_grist_connection():
    """
    Teste la connexion à l'API Grist.
    """
    try:
        client = get_grist_client()
        
        print(f"Serveur: {client.server}")
        print(f"Doc ID: {client.doc_id}")
        print(f"Table ID: {client.table_id}")
        
        # Essayer de récupérer 1 enregistrement pour tester
        url = f"{client.base_url}?limit=1"
        response = requests.get(url, headers=client.headers)
        
        if response.status_code == 200:
            return True, "Connexion réussie à Grist."
        else:
            return False, f"Erreur connexion Grist: {response.status_code} - {response.text}"
            
    except Exception as e:
        return False, f"Exception: {str(e)}"

if __name__ == "__main__":
    print("\n=== Test de connexion à Grist ===")
    success, result = test_grist_connection()
    print(f"Résultat: {'Succès' if success else 'échec'} - {result}")
