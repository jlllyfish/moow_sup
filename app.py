"""
Simulateur Démarches Simplifiées avec Streamlit pour ERASMIP.
Cette application permet de générer des liens vers des dossiers pré-remplis
sur Démarches Simplifiées pour la mobilité individuelle apprenant.
"""

import streamlit as st
import os
from dotenv import load_dotenv
import ds_prefiller
import mysql_connector
import re
from datetime import datetime

# Configuration de la page - DOIT ÊTRE LA PREMIÈRE COMMANDE STREAMLIT
st.set_page_config(
    page_title="Moow Sup x DS DGER", 
    page_icon="🐺",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
        height: 22px;
        vertical-align: middle;
        margin: 0 4px;
    }
    
    .cc-icon {
        height: 20px;
        vertical-align: middle;
        margin: 0 4px;
    }
    </style>
    """, unsafe_allow_html=True)

# Validation de l'entrée
def is_valid_name(name):
    """Vérifie si le nom est valide (non vide et composé de lettres)"""
    return bool(name) and all(c.isalpha() or c.isspace() or c == '-' or c == "'" for c in name)

# Fonction pour formatter l'affichage des dates et autres valeurs
def format_display_value(value, is_date=False):
    """
    Formate une valeur pour l'affichage dans l'interface
    
    Args:
        value: Valeur à formater
        is_date: Si True, traite la valeur comme une date
    
    Returns:
        str: Valeur formatée ou texte "Non renseigné" si vide
    """
    if not value or value == "None" or value == "null":
        return "Non renseigné"
    
    if is_date:
        try:
            # Essayer différents formats de date
            date_formats = ["%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S"]
            
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(str(value), fmt)
                    return parsed_date.strftime("%d/%m/%Y")
                except ValueError:
                    continue
                    
            # Si aucun format ne correspond, renvoyer tel quel
            return str(value)
        except Exception:
            return str(value)
    
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

def update_sidebar():
    """
    Met à jour la barre latérale avec l'état des champs
    """
    form_data = st.session_state.form_data
    
    # Liste des champs à vérifier
    fields_to_check = [
        ("Civilité", "civilite"),
        ("Nom", "nom"),
        ("Prénom", "prenom"),
        ("Date de naissance", "date_naissance"),
        ("Type de mobilité", "type_mobilite_val"),
        ("Mobilité hybride", "mobilite_hybride"),
        ("Date de départ", "date_depart"),
        ("Date de retour", "date_retour"),
        ("Pays d'accueil", "pays_accueil"),
        ("Établissement", "etablissement")  # Ajout de l'établissement
    ]
    
    for display_name, field_name in fields_to_check:
        value = form_data.get(field_name, "")
        
        if value and value != "None" and value != "null":
            st.sidebar.markdown(f"""
            <div style="margin-bottom:15px;">
                <span style="display:inline-block; width:20px; height:20px; background-color:#18753c; color:white; border-radius:50%; text-align:center; line-height:20px; margin-right:10px;">✓</span>
                <strong>{display_name}</strong><br/>
                <span style="margin-left:30px;">Renseigné</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.sidebar.markdown(f"""
            <div style="margin-bottom:15px;">
                <span style="display:inline-block; width:20px; height:20px; background-color:#e0e0e0; color:#666; border-radius:50%; text-align:center; line-height:20px; margin-right:10px;">○</span>
                <strong>{display_name}</strong><br/>
                <span style="margin-left:30px;">Non renseigné</span>
            </div>
            """, unsafe_allow_html=True)
    
    # Afficher source des données
    if st.session_state.mysql_data_loaded:
        st.sidebar.markdown(f"""
        <div style="margin-top:30px; background-color:#e3f2fd; padding:10px; border-radius:4px;">
            <strong>🔄 Données chargées depuis MySQL</strong>
        </div>
        """, unsafe_allow_html=True)

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
if 'etablissements' not in st.session_state:
    # Charger la liste des établissements au démarrage
    success, result = mysql_connector.obtenir_liste_etablissements()
    if success:
        st.session_state.etablissements = result
    else:
        st.session_state.etablissements = []

# Appliquer le style
load_css()

# Sidebar (bandeau latéral)
st.sidebar.title("Statut du dossier")

# Section principale
st.title("🐺 Moow Sup x DS DGER")
st.subheader("Recherche par nom apprenant et établissement")

# Formulaire de recherche
col1, col2 = st.columns(2)
with col1:
    nom_recherche = st.text_input("Nom apprenant", help="Nom de famille associé au dossier", key="nom_recherche")
    
    # Vérifier si le nom a changé et est valide
    if nom_recherche and is_valid_name(nom_recherche):
        if 'nom_precedent' not in st.session_state or nom_recherche != st.session_state.nom_precedent:
            with st.spinner("Recherche des établissements..."):
                success, result = mysql_connector.obtenir_etablissements_par_nom(nom_recherche.upper())
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
    if not nom_recherche or not etablissement_recherche:
        st.markdown("""
        <div class="custom-alert">
            <strong>⚠️ Veuillez remplir le nom de l'apprenant et sélectionner un établissement pour effectuer la recherche</strong>
        </div>
        """, unsafe_allow_html=True)
    elif not is_valid_name(nom_recherche):
        st.markdown("""
        <div class="custom-alert">
            <strong>⚠️ Format de nom invalide (utilisez seulement des lettres)</strong>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Réinitialiser l'état des dossiers multiples
        st.session_state.dossiers_multiples = False
        st.session_state.liste_dossiers = []
        
        # Effectuer la recherche
        with st.spinner("Recherche en cours..."):
            success, result = mysql_connector.valider_combinaison_nom_etablissement(
                nom_recherche.upper(),  # Convertir en majuscules pour correspondre au format de la BD
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
                    <strong>📋 Plusieurs dossiers trouvés ({len(st.session_state.liste_dossiers)})</strong><br/>
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
                    <span>✓ Données récupérées avec succès!</span>
                </div>
                """, unsafe_allow_html=True)
                
                # Afficher les données trouvées
                st.markdown("""
                <div class="info-box">
                    <strong>Données trouvées dans MySQL</strong><br/>
                    Les champs du formulaire vont être remplis automatiquement.
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="custom-alert">
                <strong>⚠️ Erreur lors de la recherche: {result}</strong>
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
        dossier_date_depot = format_display_value(dossier.get("date_depot"), is_date=True)
        
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
                    <span>Date de dépôt: {dossier_date_depot}</span>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if st.button(f"Sélectionner", key=f"select_dossier_{i}"):
                    # Récupérer les données du dossier sélectionné
                    selected_fields = dossier.get("fields", {})
                    
                    # Mapper les données pour l'API
                    mapped_data = mysql_connector.mapper_donnees_mobilite(selected_fields)
                    mapped_data["etablissement"] = dossier_etablissement
                    
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
        st.markdown(f"**Soumis à la Charte Erasmus+ ?** <span class='fixed-value'>Oui</span>", unsafe_allow_html=True)
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
            <strong>⚠️ Champs obligatoires manquants : {champs_str}</strong>
        </div>
        """, unsafe_allow_html=True)
    
    # Bouton pour générer le lien - ne pas désactiver même s'il manque des champs
    if st.button("Générer le lien vers le dossier pré-rempli"):
        # Préparer les données du formulaire
        form_data = st.session_state.form_data
        
        # Appeler le module de pré-remplissage
        with st.spinner("Génération du lien en cours..."):
            success, result = ds_prefiller.generate_prefilled_url(form_data)
        
        # Enregistrer le résultat dans les variables de session
        if success:
            st.session_state.generate_success = True
            st.session_state.dossier_url = result
            st.rerun()
        else:
            st.error(f"❌ Erreur: {result}")

# Interface de résultat si le lien a été généré
if st.session_state.generate_success:
    # Afficher le message de succès
    st.markdown("""
    <div class="success-message">
        <span>✓ Traitement terminé avec succès!</span>
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

# Mise à jour des informations dans la sidebar
update_sidebar()

# Pied de page avec copyright Creative Commons
st.markdown("""
<div class="footer">
    © 2025 Creative Commons Attribution (CC BY) 
    <img src="https://mirrors.creativecommons.org/presskit/icons/cc.svg" class="cc-icon" alt="CC">
    <img src="https://mirrors.creativecommons.org/presskit/icons/by.svg" class="cc-icon" alt="BY">
    DRAAF Occitanie × ENSFEA - Tous droits réservés
</div>
""", unsafe_allow_html=True)