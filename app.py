import streamlit as st

# Configuration de la page - DOIT ÃŠTRE LA PREMIÃˆRE COMMANDE STREAMLIT
st.set_page_config(
    page_title="Moow Sup x DS DGER", 
    page_icon="🐮",
    layout="wide",
    initial_sidebar_state="collapsed"
)

## Simulateur Démarches Simplifiées avec Streamlit pour ERASMIP.
#Cette application permet de générer des liens vers des dossiers pré-remplis sur Démarches Simplifiées pour la mobilité individuelle apprenant.
# Version 2 : Ajout de la recherche par date de départ et établissement.

import os
from dotenv import load_dotenv
import ds_prefiller
import grist_connector
import re
from datetime import datetime
import pandas as pd

# Charger les variables d'environnement
load_dotenv()

# CSS pour le style conforme au design système de l'État
def load_css():
    st.markdown("""
    <style>
    /* Style général conforme au DSFR */
    .main {
        background-color: #ffffff;
        color: #1e1e1e;
        font-family: Marianne, arial, sans-serif;
    }
    h1, h2, h3 {
        color: #000091;
    }
    .stButton button {
        background-color: #000091;
        color: white;
        border-radius: 4px;
        border: none;
        padding: 8px 16px;
    }
    .stButton button:hover {
        background-color: #1212ff;
    }
    
    /* Style pour les messages de succès */
    .success-message {
        background-color: #e8f5e9;
        color: #1b5e20;
        padding: 15px;
        border-radius: 4px;
        margin: 15px 0;
        text-align: center;
    }
    
    /* Style pour la sidebar */
    section[data-testid="stSidebar"] {
        background-color: #f2f2ff;
    }
    
    /* Style pour l'alerte */
    .custom-alert {
        background-color: #fff4e5;
        color: #b95000;
        padding: 15px;
        border-radius: 4px;
        margin: 15px 0;
        border-left: 4px solid #b95000;
    }
    
    /* Style pour l'info */
    .info-box {
        background-color: #e3f2fd;
        color: #0d47a1;
        padding: 15px;
        border-radius: 4px;
        margin: 15px 0;
        border-left: 4px solid #0d47a1;
    }
    
    /* Style pour le bouton de lien */
    .link-button {
        background-color: #000091;
        color: white !important;
        text-decoration: none;
        padding: 10px 24px;
        border-radius: 4px;
        font-size: 16px;
        display: inline-block;
        border: none;
        cursor: pointer;
        text-align: center;
        margin-bottom: 16px; 
    }
    
    .link-button:hover {
        background-color: #1212ff;
    }
    
    /* Style pour le conteneur de résultat */
    .result-container {
        background-color: #f7f7f7;
        padding: 15px;
        border-radius: 4px;
        margin-top: 15px;
    }
    
    /* Style pour les champs manquants */
    .empty-field {
        color: #b0bec5;
        font-style: italic;
    }
    
    /* Style pour les valeurs par défaut */
    .default-value {
        color: #26a69a;
        font-style: italic;
        font-weight: normal;
    }
    
    /* Style pour les valeurs fixes */
    .fixed-value {
        color: #26a69a;
        font-weight: normal;
    }
    
    /* Style pour la liste de sélection des dossiers */
    .dossier-selection {
        background-color: #f5f5f5;
        padding: 10px;
        border-radius: 4px;
        margin: 10px 0;
        border-left: 4px solid #000091;
    }
    
    /* Style pour les options de la liste de sélection */
    .dossier-option {
        padding: 8px;
        margin: 5px 0;
        border-radius: 4px;
        cursor: pointer;
        transition: background-color 0.3s;
    }
    
    .dossier-option:hover {
        background-color: #e0e0e0;
    }
    
    .dossier-option.selected {
        background-color: #e3f2fd;
        border-left: 4px solid #000091;
    }
    
    /* Style pour le tableau de résultats */
    .dataframe {
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
    }
    
    .dataframe th {
        background-color: #f5f5f5;
        color: #333;
        text-align: left;
        padding: 10px;
        border-bottom: 2px solid #ddd;
    }
    
    /* Style pour les en-tÃªtes des numéros de ligne */
    .dataframe thead tr:first-child th:first-child {
        background-color: #f5f5f5;
        color: #333;
        border-bottom: 2px solid #ddd;
    }
    
    /* Style pour les numéros de ligne */
    .dataframe tbody th {
        background-color: #f5f5f5;
        color: #333;
        font-weight: normal;
        text-align: center;
        padding: 8px;
    }
    
    .dataframe td {
        border: 1px solid #e0e0e0;
        padding: 8px;
    }
    
    .dataframe tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    
    .dataframe tr:hover {
        background-color: #f1f1f1;
    }
    
    /* Style pour les onglets */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #f2f2ff;
        border-radius: 4px 4px 0 0;
        padding: 10px 20px;
        border: 1px solid #e0e0e0;
        border-bottom: none;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #000091;
        color: white;
    }
    
    /* Style pour le pied de page */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #f5f5f5;
        color: #666666;
        text-align: center;
        padding: 10px 0;
        font-size: 14px;
        border-top: 1px solid #e0e0e0;
        z-index: 999;
    }
    
    .footer img {
        height: 24px;
        vertical-align: middle;
        margin-right: 8px;
    }
    
    .cc-icon {
        height: 22px;
        vertical-align: middle;
        margin: 0 4px;
    }
    </style>
    """, unsafe_allow_html=True)


def is_valid_name(name):
    """Vérifie si un nom est valide (lettres uniquement)"""
    import re
    return bool(re.match(r'^[a-zA-ZÀ-ÿ\s\-]+$', name))

def format_display_value(value, is_date=False):
    """
    Formate une valeur pour l'affichage.
    """
    if not value or value == "None" or value == "null":
        return '<span class="empty-field">Non renseigné</span>'
    
    if is_date:
        from datetime import datetime
        import re
        try:
            if isinstance(value, str):
                # Format ISO avec timezone (ex: 2025-04-05T19:56:27+02:00)
                if "T" in value:
                    # Supprimer la timezone avec regex
                    date_str = re.sub(r'[+-]\d{2}:\d{2}$', '', value)
                    # Parser avec ou sans secondes
                    if '.' in date_str:
                        date_obj = datetime.strptime(date_str.split('.')[0], "%Y-%m-%dT%H:%M:%S")
                    else:
                        date_obj = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")
                    return date_obj.strftime("%d/%m/%Y")
                else:
                    # Format YYYY-MM-DD
                    date_obj = datetime.strptime(value, "%Y-%m-%d")
                    return date_obj.strftime("%d/%m/%Y")
        except Exception as e:
            print(f"Erreur format date {value}: {e}")
            pass
    
    return str(value)

def verifier_champs_obligatoires():
    """
    Vérifie les champs obligatoires pour le formulaire ERASMIP
    """
    form_data = st.session_state.form_data
    champs_manquants = []
    
    # Seuls nom et prénom sont vraiment obligatoires
    champs_obligatoires = [
        ("nom", "Nom"),
        ("prenom", "Prénom")
    ]
    
    # Vérifier chaque champ obligatoire
    for field_name, display_name in champs_obligatoires:
        if field_name not in form_data or not form_data.get(field_name, ""):
            champs_manquants.append(display_name)
    
    return champs_manquants

# Générer les URL de pré-remplissage pour chaque apprenant
def generer_liens_pre_remplissage(apprenants):
    """
    Génère des liens de pré-remplissage pour une liste d'apprenants.
    
    Args:
        apprenants (list): Liste des dictionnaires de données des apprenants
        
    Returns:
        list: Liste des dictionnaires avec les données et les liens générés
    """
    resultats = []
    
    with st.spinner("Génération des liens en cours..."):
        for apprenant in apprenants:
            # Générer l'URL courte pour chaque apprenant
            success, url = ds_prefiller.generate_short_url(apprenant)
            
            # Conserver uniquement les données nécessaires pour le tableau
            resultat = {
                "Numéro dossier Moow Pro": apprenant.get("dossier_number", ""),
                "Nom": apprenant.get("nom", ""),
                "Prénom": apprenant.get("prenom", ""),
                "Date de départ": format_display_value(apprenant.get("date_depart"), is_date=True),
                "Date de retour": format_display_value(apprenant.get("date_retour"), is_date=True),
                "Pays d'accueil": apprenant.get("pays_accueil", "Non renseigné"),
                "Établissement": apprenant.get("etablissement", "Non renseigné"),
                "Type de mobilité": apprenant.get("type_mobilite_val", "Stage"),
                "Lien pré-remplissage": url if success else "Erreur de génération"
            }
            
            resultats.append(resultat)
    
    return resultats

# Initialisation des variables de session
if 'generate_success' not in st.session_state:
    st.session_state.generate_success = False
if 'dossier_url' not in st.session_state:
    st.session_state.dossier_url = ""
if 'form_data' not in st.session_state:
    st.session_state.form_data = {}
if 'mysql_data_loaded' not in st.session_state:
    st.session_state.mysql_data_loaded = False
if 'dossiers_multiples' not in st.session_state:
    st.session_state.dossiers_multiples = False
if 'liste_dossiers' not in st.session_state:
    st.session_state.liste_dossiers = []
if 'etablissements_filtres' not in st.session_state:
    st.session_state.etablissements_filtres = []
if 'nom_precedent' not in st.session_state:
    st.session_state.nom_precedent = ""
if 'resultats_recherche_date' not in st.session_state:
    st.session_state.resultats_recherche_date = []
if 'etablissements' not in st.session_state:
    # Charger la liste des établissements au démarrage
    success, result = grist_connector.obtenir_liste_etablissements()
    if success:
        st.session_state.etablissements = result
    else:
        st.session_state.etablissements = []

# Appliquer le style
load_css()

# Titre principal
st.title("🐮 Moow Sup x DS DGER")

# Créer des onglets pour les différentes fonctionnalités
tab1, tab2 = st.tabs(["Recherche par nom apprenant", "Recherche par date et établissement"])

#########################################
# ONGLET 1: RECHERCHE PAR NOM APPRENANT #
#########################################
with tab1:
    st.subheader("Recherche par nom apprenant et établissement")

    # Formulaire de recherche
    col1, col2 = st.columns(2)
    with col1:
        nom_recherche = st.text_input("Nom apprenant (en Majuscule)", help="Nom de famille associé au dossier", key="nom_recherche")
        
        # Vérifier si le nom a changé et est valide
        if nom_recherche and is_valid_name(nom_recherche):
            if 'nom_precedent' not in st.session_state or nom_recherche != st.session_state.nom_precedent:
                with st.spinner("Recherche des établissements..."):
                    success, result = grist_connector.obtenir_etablissements_par_nom(nom_recherche)
                    if success:
                        st.session_state.etablissements_filtres = result
                        st.session_state.nom_precedent = nom_recherche
                    else:
                        st.session_state.etablissements_filtres = []
                        st.info(f"Aucun établissement trouvé pour {nom_recherche}. Vous pouvez sélectionner n'importe quel établissement dans la liste complète.")
        
        # Afficher la liste des établissements filtrée ou complète
        if nom_recherche and 'etablissements_filtres' in st.session_state and st.session_state.etablissements_filtres:
            # Utiliser la liste filtrée si disponible
            etablissement_recherche = st.selectbox(
                "Établissement", 
                options=[""] + st.session_state.etablissements_filtres,
                index=0,
                help="Établissements associés à ce nom d'apprenant",
                key="etablissement_recherche"
            )
            st.success(f"{len(st.session_state.etablissements_filtres)} établissement(s) trouvé(s) pour {nom_recherche}")
        else:
            # Sinon, utiliser la liste complète
            if 'etablissements' in st.session_state and st.session_state.etablissements:
                etablissement_recherche = st.selectbox(
                    "Établissement", 
                    options=[""] + st.session_state.etablissements,
                    index=0,
                    help="Établissement de l'apprenant (EPLEFPA)",
                    key="etablissement_recherche"
                )
            else:
                etablissement_recherche = st.text_input(
                    "Établissement", 
                    help="Établissement de l'apprenant (EPLEFPA)",
                    key="etablissement_recherche_text"
                )

    with col2:
        numero_dossier_recherche = st.text_input(
            "Numéro de dossier (optionnel)", 
            help="Numéro de référence du dossier (facultatif pour affiner la recherche)", 
            key="numero_dossier_recherche"
        )

    # Bouton de recherche
    if st.button("Rechercher", key="btn_recherche"):
        # Validation : soit (nom + établissement) soit numéro de dossier
        if numero_dossier_recherche:
            # Recherche par numéro uniquement
            st.session_state.dossiers_multiples = False
            st.session_state.liste_dossiers = []
            
            with st.spinner("Recherche en cours..."):
                success, result = grist_connector.rechercher_dossier_par_numero(numero_dossier_recherche)
            
            if success:
                if isinstance(result, dict) and result.get("multiple", False):
                    st.session_state.dossiers_multiples = True
                    st.session_state.liste_dossiers = result.get("dossiers", [])
                    st.markdown(f"""
                    <div class="info-box">
                        <strong>Plusieurs dossiers trouvés ({len(st.session_state.liste_dossiers)})</strong><br/>
                        Veuillez sélectionner un dossier dans la liste ci-dessous.
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Mapper les données
                    dossier_fields = result.get("fields", {})
                    mapped_data = grist_connector.mapper_donnees_mobilite(dossier_fields)
                    st.session_state.form_data = mapped_data
                    st.session_state.mysql_data_loaded = True
                    st.markdown("""
                    <div class="success-message">
                        <span>✓ Données récupérées avec succès!</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="custom-alert">
                    <strong>Erreur: {result}</strong>
                </div>
                """, unsafe_allow_html=True)
        
        elif not nom_recherche or not etablissement_recherche:
            st.markdown("""
            <div class="custom-alert">
                <strong>Veuillez remplir soit le numéro de dossier, soit (nom + établissement)</strong>
            </div>
            """, unsafe_allow_html=True)
        elif not is_valid_name(nom_recherche):
            st.markdown("""
            <div class="custom-alert">
                <strong>Format de nom invalide (utilisez seulement des lettres)</strong>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Réinitialiser l'état des dossiers multiples
            st.session_state.dossiers_multiples = False
            st.session_state.liste_dossiers = []
            
            # Effectuer la recherche nom + établissement
            with st.spinner("Recherche en cours..."):
                success, result = grist_connector.valider_combinaison_nom_etablissement(
                    nom_recherche,
                    etablissement_recherche,
                    numero_dossier_recherche if numero_dossier_recherche else None
                )
            
            if success:
                # Vérifier si plusieurs dossiers ont été trouvés
                if isinstance(result, dict) and result.get("multiple", False):
                    st.session_state.dossiers_multiples = True
                    st.session_state.liste_dossiers = result.get("dossiers", [])
                    
                    # Afficher un message d'information
                    st.markdown(f"""
                    <div class="info-box">
                        <strong>Plusieurs dossiers trouvés ({len(st.session_state.liste_dossiers)})</strong><br/>
                        Veuillez sélectionner un dossier dans la liste ci-dessous.
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Stocker les données récupérées
                    st.session_state.form_data = result
                    st.session_state.mysql_data_loaded = True
                    
                    # Afficher un message de succès
                    st.markdown("""
                    <div class="success-message">
                        <span>Données récupérées avec succès!</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Afficher les données trouvées
                    st.markdown("""
                    <div class="info-box">
                        <strong>Données récupérées (Grist)</strong><br/>
                        Les champs du formulaire vont être remplis automatiquement.
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="custom-alert">
                    <strong>Erreur lors de la recherche: {result}</strong>
                </div>
                """, unsafe_allow_html=True)

    # Afficher la liste des dossiers si plusieurs ont été trouvés
    if st.session_state.dossiers_multiples and st.session_state.liste_dossiers:
        st.markdown("### Sélection du dossier")
        
        # Créer une liste de sélection des dossiers
        for i, dossier in enumerate(st.session_state.liste_dossiers):
            dossier_id = dossier.get("id", "")
            dossier_numero = dossier.get("numero", "")
            dossier_nom = dossier.get("nom", "")
            dossier_prenom = dossier.get("prenom", "")
            dossier_etablissement = dossier.get("etablissement", "")
            
            # La date est dans dossier["fields"], pas directement dans dossier
            fields = dossier.get("fields", {})
            date_depart_brute = fields.get("date_depart")
            date_depart_iso = grist_connector.transformer_date(date_depart_brute)
            dossier_date_depart = format_display_value(date_depart_iso, is_date=True)
            
            # Créer un conteneur pour chaque dossier
            dossier_container = st.container()
            
            with dossier_container:
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.markdown(f"""
                    <div class="dossier-option" id="dossier-{i}">
                        <strong>{dossier_nom} {dossier_prenom}</strong><br/>
                        <span>Numéro: {dossier_numero}</span><br/>
                        <span>Établissement: {dossier_etablissement}</span><br/>
                        <span>Date de départ: {dossier_date_depart}</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    if st.button(f"Sélectionner", key=f"select_dossier_{i}"):
                        # Récupérer les données du dossier sélectionné
                        selected_fields = dossier.get("fields", {})
                        
                        # Mapper les données pour l'API
                        mapped_data = grist_connector.mapper_donnees_mobilite(selected_fields)
                        
                        # Stocker les données et mettre à jour l'interface
                        st.session_state.form_data = mapped_data
                        st.session_state.mysql_data_loaded = True
                        st.session_state.dossiers_multiples = False
                        st.session_state.liste_dossiers = []
                        
                        st.rerun()

# Si des données ont été chargées, afficher un récapitulatif
    if st.session_state.mysql_data_loaded:
        # Préparation des valeurs pour l'affichage
        nom = st.session_state.form_data.get("nom", "")
        prenom = st.session_state.form_data.get("prenom", "")
        civilite = st.session_state.form_data.get("civilite", "")
        if not civilite or civilite == "None":
            civilite_display = '<span class="empty-field">Non renseignée</span>'
        else:
            civilite_display = civilite
            
        date_naissance = format_display_value(
            st.session_state.form_data.get("date_naissance"), 
            is_date=True
        )
        
        mobilite_format = st.session_state.form_data.get("format_mobilite", "")
        mobilite_hybride = "Oui" if mobilite_format == "Mobilité hybride" else "Non"
        
        date_depart = format_display_value(
            st.session_state.form_data.get("date_depart"), 
            is_date=True
        )
        
        date_retour = format_display_value(
            st.session_state.form_data.get("date_retour"), 
            is_date=True
        )
        
        pays_accueil = st.session_state.form_data.get("pays_accueil", "")
        if not pays_accueil or pays_accueil == "None":
            pays_accueil_display = '<span class="empty-field">Non renseigné</span>'
        else:
            pays_accueil_display = pays_accueil
            
        etablissement = st.session_state.form_data.get("etablissement", "")
        if not etablissement or etablissement == "None":
            etablissement_display = '<span class="empty-field">Non renseigné</span>'
        else:
            etablissement_display = etablissement
            
        mobilite_apprenant = st.session_state.form_data.get("mobilite_apprenant", "")
        if mobilite_apprenant == "Mobilité d'apprentissage de courte durée":
            type_mobilite_apprenant = "Stage"
        elif mobilite_apprenant == "Concours de compétence":
            type_mobilite_apprenant = "Concours de compétence"
        else:
            type_mobilite_apprenant = "Stage"  # Valeur par défaut
            
        statut_participant = st.session_state.form_data.get("statut_participant", "")
        est_apprenti = "Oui" if statut_participant and statut_participant.lower() == "apprenti" else "Non"
        statut_apprenant = "Apprenti" if est_apprenti == "Oui" else "Élève"
        
        # Affichage du récapitulatif des données
        st.markdown("### Récapitulatif des données")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**Région:** <span class='fixed-value'>Occitanie</span>", unsafe_allow_html=True)
            st.markdown(f"**Civilité:** {civilite_display}", unsafe_allow_html=True)
            st.markdown(f"**Nom:** {nom}")
            st.markdown(f"**Prénom:** {prenom}")
            st.markdown(f"**Date de naissance:** {date_naissance}")
            st.markdown(f"**Type de mobilité:** <span class='fixed-value'>Stage</span>", unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"**Mobilité hybride:** {mobilite_hybride}")
            st.markdown(f"**Date de départ:** {date_depart}")
            st.markdown(f"**Date de retour:** {date_retour}")
            st.markdown(f"**Pays d'accueil:** {pays_accueil_display}", unsafe_allow_html=True)
            st.markdown(f"**Zone destination:** <span class='fixed-value'>Pays membre de l'Union Européenne</span>", unsafe_allow_html=True)
            st.markdown(f"**Mobilité dans le cadre d'un projet Erasmus+ ?** <span class='fixed-value'>Oui</span>", unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"**Mobilité dans le cadre d'un consortium Erasmus+ ?** <span class='fixed-value'>Oui</span>", unsafe_allow_html=True)
            st.markdown(f"**Statut:** {statut_apprenant}")
            st.markdown(f"**Est apprenti:** {est_apprenti}")
            st.markdown(f"**Type de mobilité apprenant:** {type_mobilite_apprenant}")
            st.markdown(f"**Établissement:** {etablissement_display}", unsafe_allow_html=True)
        
        # Ajouter un bouton pour générer le lien
        st.markdown("### Génération du lien")
        
        # Vérifier les champs obligatoires
        champs_manquants = verifier_champs_obligatoires()
        
        if champs_manquants:
            champs_str = ", ".join(champs_manquants)
            st.markdown(f"""
            <div class="custom-alert">
                <strong>Champs obligatoires manquants : {champs_str}</strong>
            </div>
            """, unsafe_allow_html=True)
        
        # Bouton pour générer le lien - ne pas désactiver mÃªme s'il manque des champs
        if st.button("Générer le lien vers le dossier pré-rempli"):
            # Préparer les données du formulaire
            form_data = st.session_state.form_data
            
            # Appeler le module de pré-remplissage avec génération d'URL courte
            with st.spinner("Génération du lien en cours..."):
                success, result = ds_prefiller.generate_short_url(form_data)
            
            # Enregistrer le résultat dans les variables de session
            if success:
                st.session_state.generate_success = True
                st.session_state.dossier_url = result
                st.rerun()
            else:
                st.error(f" Erreur: {result}")

    # Interface de résultat si le lien a été généré
    if st.session_state.generate_success:
        # Afficher le message de succès
        st.markdown("""
        <div class="success-message">
            <span>Traitement terminé avec succès!</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Bouton d'accès au dossier - lien direct
        st.markdown(f"""
        <a href="{st.session_state.dossier_url}" target="_blank" class="link-button">
            Accéder au dossier pré-rempli
        </a>
        """, unsafe_allow_html=True)
        
        # Message informatif juste après le premier bouton
        st.markdown(f"""
        <div class="result-container">
            <p>Votre dossier de mobilité individuelle apprenant a été pré-rempli. Cliquez sur le bouton pour y accéder.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Bouton pour générer un nouveau lien - séparé et placé en dernier
        if st.button("Générer un nouveau lien", key="new_link"):
            st.session_state.generate_success = False
            st.session_state.dossier_url = ""
            st.rerun()

#################################################
# ONGLET 2: RECHERCHE PAR DATE ET ÉTABLISSEMENT #
#################################################
with tab2:
    st.subheader("Recherche par date de départ et établissement")
    
    # Formulaire de recherche
    col1, col2 = st.columns(2)
    
    with col1:
        # Sélecteur de date
        date_depart = st.date_input(
            "Date de départ", 
            value=None,
            help="Date de départ des apprenants à rechercher",
            format="DD-MM-YYYY",
            key="date_depart_recherche"
        )
        
        # Filtrer les établissements par date si une date est saisie
        if date_depart:
            date_str = date_depart.strftime("%Y-%m-%d")
            # Vérifier si la date a changé
            if 'date_precedente' not in st.session_state or date_str != st.session_state.date_precedente:
                with st.spinner("Recherche des établissements pour cette date..."):
                    # Récupérer tous les enregistrements pour cette date
                    success, result = grist_connector.rechercher_apprenants_par_date_et_etablissement(
                        date_str,
                        None  # On veut tous les établissements pour cette date
                    )
                    if success and result:
                        # Extraire la liste unique des établissements
                        etablissements_date = sorted(list(set([app.get("etablissement") for app in result if app.get("etablissement")])))
                        st.session_state.etablissements_filtres_date = etablissements_date
                        st.session_state.date_precedente = date_str
                    else:
                        st.session_state.etablissements_filtres_date = []
    
    with col2:
        # Sélecteur d'établissement
        if date_depart and 'etablissements_filtres_date' in st.session_state and st.session_state.etablissements_filtres_date:
            # Utiliser la liste filtrée par date
            etablissement_date = st.selectbox(
                "Établissement", 
                options=[""] + st.session_state.etablissements_filtres_date,
                index=0,
                help=f"Établissements ayant des départs le {date_depart.strftime('%d/%m/%Y')}",
                key="etablissement_date_recherche"
            )
            if st.session_state.etablissements_filtres_date:
                st.success(f"{len(st.session_state.etablissements_filtres_date)} établissement(s) avec départs à cette date")
        elif 'etablissements' in st.session_state and st.session_state.etablissements:
            # Utiliser la liste complète
            etablissement_date = st.selectbox(
                "Établissement", 
                options=[""] + st.session_state.etablissements,
                index=0,
                help="Établissement des apprenants à rechercher",
                key="etablissement_date_recherche_full"
            )
        else:
            etablissement_date = st.text_input(
                "Établissement", 
                help="Établissement des apprenants à rechercher",
                key="etablissement_date_recherche_text"
            )
    
    # Bouton de recherche
    if st.button("Rechercher les apprenants", key="btn_recherche_date"):
        if not date_depart or not etablissement_date:
            st.markdown("""
            <div class="custom-alert">
                <strong>Veuillez sélectionner une date de départ et un établissement pour effectuer la recherche</strong>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Convertir la date en chaîne au format YYYY-MM-DD
            date_str = date_depart.strftime("%Y-%m-%d")
            
            # Effectuer la recherche
            with st.spinner("Recherche des apprenants en cours..."):
                success, result = grist_connector.rechercher_apprenants_par_date_et_etablissement(
                    date_str,
                    etablissement_date
                )
            
            if success:
                # Générer les liens de pré-remplissage pour chaque apprenant
                st.session_state.resultats_recherche_date = generer_liens_pre_remplissage(result)
                
                # Afficher un message de succès
                st.markdown(f"""
                <div class="success-message">
                    <span>{len(result)} apprenant(s) trouvé(s) et {len(st.session_state.resultats_recherche_date)} lien(s) généré(s)</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="custom-alert">
                    <strong>{result}</strong>
                </div>
                """, unsafe_allow_html=True)
    
    # Afficher les résultats si disponibles
    if st.session_state.resultats_recherche_date:
        st.markdown("### Tableau des apprenants avec liens de pré-remplissage")
        
        # Création du DataFrame pour affichage
        df = pd.DataFrame(st.session_state.resultats_recherche_date)
        
        # Vérifier que toutes les colonnes existent avant de réorganiser
        colonnes_ordre = []
        # Vérifier et ajouter chaque colonne si elle existe
        if "Numéro dossier Moow Pro" in df.columns:
            colonnes_ordre.append("Numéro dossier Moow Pro")
        colonnes_ordre.extend([
            "Nom", "Prénom", "Date de départ", "Date de retour", 
            "Pays d'accueil", "Établissement", "Type de mobilité", 
            "Lien pré-remplissage"
        ])
        
        # Filtrer les colonnes qui existent réellement dans le DataFrame
        colonnes_disponibles = [col for col in colonnes_ordre if col in df.columns]
        df = df[colonnes_disponibles]
        
        # Convertir les liens en liens cliquables
        def make_clickable(val):
            if val and isinstance(val, str) and val.startswith("http"):
                return f'<a href="{val}" target="_blank">Ouvrir le lien</a>'
            return val
        
        # Appliquer la fonction aux liens
        df_display = df.copy()
        df_display["Lien pré-remplissage"] = df_display["Lien pré-remplissage"].apply(make_clickable)
        
        # Afficher le tableau avec les liens cliquables
        st.write(df_display.to_html(escape=False), unsafe_allow_html=True)
        
        # Bouton pour effacer les résultats
        if st.button("Effacer les résultats", key="clear_results"):
            st.session_state.resultats_recherche_date = []
            st.rerun()

# Pied de page avec copyright
st.markdown("""
<div class="footer">
    (c) 2025 Creative Commons Attribution (CC BY) 
    <img src="https://mirrors.creativecommons.org/presskit/icons/cc.svg" class="cc-icon" alt="CC">
    <img src="https://mirrors.creativecommons.org/presskit/icons/by.svg" class="cc-icon" alt="BY">
    DRAAF Occitanie x ENSFEA - Tous droits réservés
</div>
""", unsafe_allow_html=True)
