import streamlit as st
import os
import pandas as pd
import time
from app.email_sender import check_smtp_connection, send_email_message
from app.utils import load_contacts_file, save_uploaded_places, create_distribution_mapping, save_distribution_csv

def run_app():
    # Configuration de la page avec un thème plus épuré
    st.set_page_config(
        page_title="PARISII - Distribution des places", 
        layout="centered",
        initial_sidebar_state="expanded"
    )
    
    # CSS personnalisé avec les couleurs du club (noir, rouge, bleu)
    st.markdown("""
    <style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3 {
        margin-bottom: 1.5rem;
    }
    h3 {
        display: flex;
        align-items: center;
        gap: 15px; /* Plus d'espace entre l'icône et le texte */
    }
    .stButton button {
        width: 100%;
        background-color: #1c4b82; /* Bleu du club */
        color: white;
    }
    .stButton button:hover {
        background-color: #1c4b82; /* Rouge du club au survol */
    }
    .step-container {
        background-color: #1c4b82;
        padding: .3rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        border: 1px solid #e9ecef;
    }
    .sidebar .stButton button {
        background-color: #000000; /* Noir pour les boutons de la sidebar */
    }
    /* Couleurs personnalisées pour les alerts */
    .stSuccess {
        background-color: #e6f7e6;
        border-left-color: #1c4b82 !important; /* Bleu du club */
    }
    .stError {
        background-color: #ffe6e6;
        border-left-color: #E20613 !important; /* Rouge du club */
    }
    .stInfo {
        border-left-color: #000000 !important; /* Noir du club */
    }
    /* Style pour les labels des champs de saisie */
    label.css-qrbaxs {
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        color: #1c4b82 !important;
    }
    /* Style pour le conteneur d'aide Gmail */
    .gmail-help {
        background-color: #f0f8ff;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
        border-left: 4px solid #1c4b82;
    }
    .gmail-help ol {
        margin-left: 20px;
    }
    /* Style pour les expanders */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: #1c4b82;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Titre principal avec les couleurs du club
    st.markdown("""<h1 style='text-align: center; color: #1c4b82;'>PARISII - Distribution des Places ⚫️🔴🔵</h1>""", unsafe_allow_html=True)
    
    # ------------------------------
    # Configuration SMTP (Sidebar)
    # ------------------------------
    st.sidebar.header("⚙️ Configuration SMTP")
    with st.sidebar.expander("Configuration du serveur", expanded=False):
        smtp_server = st.text_input("SMTP Server", value="smtp.gmail.com")
        smtp_port = st.number_input("SMTP Port", value=587)
    
    with st.sidebar.expander("Identifiants de connexion", expanded=True):
        username = st.text_input("Adresse email", value="", help="Votre adresse email Gmail")
        password = st.text_input("Mot de passe", type="password", help="Mot de passe d'application Gmail")
    
    # Informations utiles dans la sidebar
    with st.sidebar.expander("Aide", expanded=True):
        st.markdown("""
        **Comment obtenir un mot de passe d'application Gmail:**
        1. Activer l'authentification à deux facteurs
        2. Aller dans votre compte Google > Sécurité
        3. Dans "Connexion à Google", sélectionnez "Mots de passe d'application"
        4. Générez un nouveau mot de passe
        """)

    # Initialisation des variables de session
    if "contacts_df" not in st.session_state:
        st.session_state.contacts_df = None
    if "email_column" not in st.session_state:
        st.session_state.email_column = None
    if "distribution_mapping" not in st.session_state:
        st.session_state.distribution_mapping = None
    if "places_paths" not in st.session_state:
        st.session_state.places_paths = []
    if "progress" not in st.session_state:
        st.session_state.progress = 0
    
    # ------------------------------
    # Étape 1 : Vérification de la connexion SMTP
    # ------------------------------
    with st.container():
        st.markdown("<div class='step-container'>", unsafe_allow_html=True)
        st.markdown("### 📡 &nbsp;&nbsp; Étape 1: Vérification de la connexion SMTP", unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("Vérifiez la connexion au serveur SMTP avant de continuer.")
        with col2:
            verify_btn = st.button("Vérifier", help="Tester les paramètres SMTP")
        
        if verify_btn:
            with st.spinner("Tentative de connexion au serveur SMTP..."):
                connection_ok, message = check_smtp_connection(smtp_server, smtp_port, username, password)
                if connection_ok:
                    st.success("✅ Connexion réussie!")
                else:
                    st.error(f"❌ Erreur de connexion: {message}")
        st.markdown("</div>", unsafe_allow_html=True)

    # ------------------------------
    # Étape 2 : Chargement des fichiers (contacts + places)
    # ------------------------------
    with st.container():
        st.markdown("<div class='step-container'>", unsafe_allow_html=True)
        st.markdown("### 📁 &nbsp;&nbsp; Étape 2: Chargement des fichiers", unsafe_allow_html=True)
        
        # Colonnes pour un affichage plus propre
        col1, col2 = st.columns(2)
        
        with col1:
            contacts_file = st.file_uploader("Fichier de contacts (CSV/Excel)", type=["csv", "xlsx"])
            if contacts_file is not None:
                try:
                    df = load_contacts_file(contacts_file)
                    st.session_state.contacts_df = df
                    st.success(f"✅ {len(df)} contacts chargés")
                except Exception as e:
                    st.error(f"❌ Erreur: {e}")
        
        with col2:
            places_files = st.file_uploader("Fichiers de places (PDF)", type=["pdf"], accept_multiple_files=True)
            if places_files:
                st.success(f"✅ {len(places_files)} fichiers PDF chargés")
        
        # Sélection de la colonne email (uniquement après chargement du fichier contacts)
        if st.session_state.contacts_df is not None:
            st.session_state.email_column = st.selectbox(
                "Sélectionne la colonne contenant les adresses email", 
                options=st.session_state.contacts_df.columns.tolist()
            )
            
        validate_files = st.button("Valider les fichiers", help="Générer la distribution")
        
        if validate_files:
            if st.session_state.contacts_df is None or not places_files or st.session_state.email_column is None:
                st.error("❌ Veille à charger tous les fichiers nécessaires et sélectionner la colonne email.")
            else:
                with st.spinner("Préparation de la distribution..."):
                    try:
                        # Créer le dossier de destination s'il n'existe pas
                        upload_folder = "uploaded_places"
                        if not os.path.exists(upload_folder):
                            os.makedirs(upload_folder)
                        
                        # Sauvegarder les fichiers
                        st.session_state.places_paths = save_uploaded_places(places_files, upload_folder)
                        
                        # Créer la distribution
                        contacts_df = st.session_state.contacts_df[[st.session_state.email_column]].copy()
                        contacts_df.rename(columns={st.session_state.email_column: "email"}, inplace=True)
                        
                        # Tri des fichiers de places par nom
                        sorted_places = sorted(st.session_state.places_paths)
                        st.session_state.distribution_mapping = create_distribution_mapping(contacts_df, sorted_places)
                        st.success("✅ Distribution générée avec succès!")
                    except Exception as e:
                        st.error(f"❌ Erreur lors du traitement: {e}")
        st.markdown("</div>", unsafe_allow_html=True)

    # ------------------------------
    # Étape 3 : Aperçu et téléchargement de la distribution
    # ------------------------------
    with st.container():
        st.markdown("<div class='step-container'>", unsafe_allow_html=True)
        st.markdown("### 🔍 &nbsp;&nbsp; Étape 3: Aperçu de la distribution", unsafe_allow_html=True)
        
        if st.session_state.distribution_mapping is not None:
            # Affichage plus élégant du dataframe
            st.dataframe(
                st.session_state.distribution_mapping,
                use_container_width=True,
                hide_index=True
            )
            
            csv_download = save_distribution_csv(st.session_state.distribution_mapping)
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.download_button(
                    label="📥 Télécharger le récapitulatif CSV",
                    data=csv_download,
                    file_name="distribution.csv",
                    mime="text/csv"
                )
        else:
            st.info("ℹ️ La distribution n'a pas encore été générée. Veuillez valider les fichiers à l'étape 2.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ------------------------------
    # Étape 4 : Rédaction de l'email
    # ------------------------------
    with st.container():
        st.markdown("<div class='step-container'>", unsafe_allow_html=True)
        st.markdown("### ✉️ &nbsp;&nbsp; Étape 4: Rédaction de l'email", unsafe_allow_html=True)
        
        subject = st.text_input("Objet de l'email", value="🎟️ Ta place pour PARIS BASKETBALL - XXX")
        
        # Section d'aide pour récupérer le code HTML de Gmail, maintenant dans un expander
        with st.expander("💡 Aide : Comment récupérer le code HTML d'un brouillon Gmail   ↓↓↓"):
            st.markdown("""
            <div class="gmail-help">
                <p><strong>Procédure étape par étape :</strong></p>
                <ol>
                    <li>Rédige ton email brouillon dans Gmail avec toute la mise en forme souhaitée</li>
                    <li>Fais un clic droit avec ta souris sur la zone de rédaction et sélectionne "Inspecter"</li>
                    <li>Sélectionne la petite flèche tout en haut à gauche de la barre qui s'est ouverte</li>
                    <li>Survole ton message avec ton curseur et clique une fois que tout le texte est en surbrillance</li>
                    <li>Copie le code associé (commençant par div...) qui est en surbrillance sur la barre de droite</li>
                    <li>Colle-le dans la zone de saisie ci-dessous</li>
                </ol>
                <p><em>Astuce : Ne t'inquiète pas des balises div, les destinataires verront uniquement la mise en forme finale.</em></p>
            </div>
            """, unsafe_allow_html=True)
        
        # Format de l'email uniquement en HTML
        default_html = """
            <div dir="ltr">Hello !
            <div>
            <br>
            </div>
            <div>C'est le moment d'accueillir&nbsp;à la maison une équipe qu'il faudra&nbsp;
                <b>
                    <span zeum4c1="PR_5_0" data-ddnwab="PR_5_0" aria-invalid="grammar" class="Lm ng">BATTRE</span>&nbsp;
                </b>à n'importe quel prix !!!&nbsp;
                <img data-emoji="🔥" class="an1" alt="🔥" aria-label="🔥" draggable="false" src="https://fonts.gstatic.com/s/e/notoemoji/16.0/1f525/72.png" loading="lazy">
                </div>
                <div>
                    <br>
                    </div>
                    <div>
                        <b>Voici&nbsp;ta&nbsp;place&nbsp;pour le match contre XXX.&nbsp;
                            <img data-emoji="🎟️" class="an1" alt="🎟️" aria-label="🎟️" draggable="false" src="https://fonts.gstatic.com/s/e/notoemoji/16.0/1f39f_fe0f/72.png" loading="lazy">
                            </b>
                        </div>
                        <div>
                            <b>
                                <br>
                                </b>
                            </div>
                            <div>
                                <img data-emoji="⚠️" class="an1" alt="⚠️" aria-label="⚠️" draggable="false" src="https://fonts.gstatic.com/s/e/notoemoji/16.0/26a0_fe0f/72.png" loading="lazy">&nbsp;Si tu ne peux assister à cette rencontre et que tu souhaites redistribuer ta place n'hésite pas à nous le préciser en répondant à ce mail ou à nous envoyer ta place sur WhatsApp.&nbsp;
                                    <img data-emoji="🙏" class="an1" alt="🙏" aria-label="🙏" draggable="false" src="https://fonts.gstatic.com/s/e/notoemoji/16.0/1f64f/72.png" loading="lazy">
                                    </div>
                                    <div>
                                        <br>
                                        </div>
                                        <div>Il va falloir&nbsp;
                                            <b>RÉPONDRE PRÉSENT&nbsp;</b>en tribune et donner tout ce que tu as pour pousser nos joueurs à gagner ce match.&nbsp;
                                            <img data-emoji="🌋" class="an1" alt="🌋" aria-label="🌋" draggable="false" src="https://fonts.gstatic.com/s/e/notoemoji/16.0/1f30b/72.png" loading="lazy">&nbsp;
                                                <img data-emoji="🗣️" class="an1" alt="🗣️" aria-label="🗣️" draggable="false" src="https://fonts.gstatic.com/s/e/notoemoji/16.0/1f5e3_fe0f/72.png" loading="lazy">
                                                    <img data-emoji="🥁" class="an1" alt="🥁" aria-label="🥁" draggable="false" src="https://fonts.gstatic.com/s/e/notoemoji/16.0/1f941/72.png" loading="lazy">
                                                    </div>
                                                    <div>
                                                        <br>
                                                        </div>
                                                        <div>
                                                            <br>
                                                            </div>
                                                            <div>
                                                                <b>
                                                                    <font color="#ff0000">
                                                                        <img data-emoji="⌚" class="an1" alt="⌚" aria-label="⌚" draggable="false" src="https://fonts.gstatic.com/s/e/notoemoji/16.0/231a/72.png" loading="lazy">&nbsp;RDV HH:MM en tribune
                                                                        </font>
                                                                    </b>
                                                                </div>
                                                                <div>
                                                                    <p>
                                                                        <b>DRESSCODE : T-SHIRT&nbsp;PARISII&nbsp;OU NOIR&nbsp;
                                                                            <img data-emoji="⚫" class="an1" alt="⚫" aria-label="⚫" draggable="false" src="https://fonts.gstatic.com/s/e/notoemoji/16.0/26ab/72.png" loading="lazy">
                                                                            </b>️
                                                                        </p>
                                                                        <p>MERCI ET ON COMPTE SUR TOI !!!&nbsp;
                                                                            <img data-emoji="🖤" class="an1" alt="🖤" aria-label="🖤" draggable="false" src="https://fonts.gstatic.com/s/e/notoemoji/16.0/1f5a4/72.png" loading="lazy">
                                                                                <img data-emoji="❤️" class="an1" alt="❤️" aria-label="❤️" draggable="false" src="https://fonts.gstatic.com/s/e/notoemoji/16.0/2764_fe0f/72.png" loading="lazy">
                                                                                    <img data-emoji="💙" class="an1" alt="💙" aria-label="💙" draggable="false" src="https://fonts.gstatic.com/s/e/notoemoji/16.0/1f499/72.png" loading="lazy">
                                                                                    </p>
                                                                                    <p>Le Bureau du&nbsp;KOP&nbsp;Parisii</p>
                                                                                </div>
                                                                            </div>
        """.strip()

        correct_emojis_style = """
        <style>
            img {
                height: 1em !important;
                width: 1em !important;
            }
        </style>
        """

        body = st.text_area("Contenu HTML de l'email", value=default_html, height=300)
        is_html = True
            
        # Aperçu HTML
        with st.expander("Aperçu de l'email", expanded=True):
            st.markdown(body + correct_emojis_style, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ------------------------------
    # Étape 5 : Envoi des emails
    # ------------------------------
    with st.container():
        st.markdown("<div class='step-container'>", unsafe_allow_html=True)
        st.markdown("### 🚀 &nbsp;&nbsp; Étape 5: Envoi des emails", unsafe_allow_html=True)
        
        if st.session_state.distribution_mapping is not None:
            total_emails = len(st.session_state.distribution_mapping)
            email_to_send = st.session_state.distribution_mapping[st.session_state.distribution_mapping["email"] != "Non attribué"]
            nb_emails_to_send = len(email_to_send)
            
            st.info(f"ℹ️ {nb_emails_to_send} emails seront envoyés sur un total de {total_emails} enregistrements.")
            
            send_button = st.button("🚀 Envoyer les emails", help="Envoyer les emails aux destinataires")
            
            if send_button:
                statuses = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                current_email = st.empty()
                
                for index, row in st.session_state.distribution_mapping.iterrows():
                    email_addr = row["email"]
                    attachment_file = row["file"]  # Ce champ contient uniquement le nom du fichier
                    
                    # Calcul de la progression
                    progress = min(100, int(100 * (index + 1) / nb_emails_to_send))
                    progress_bar.progress(progress)
                    st.session_state.progress = progress
                    
                    # On tente d'envoyer l'email uniquement si une place a été attribuée
                    if email_addr == "Non attribué":
                        status_text.text(f"Traitement: {index+1}/{nb_emails_to_send} - Place non attribuée")
                        statuses.append({"email": email_addr, "fichier": attachment_file, "statut": "Aucun envoi (place non attribuée)"})
                        continue
                    
                    # Affichage de l'email en cours d'envoi
                    current_email.markdown(f"**Envoi en cours**: {email_addr}")
                    status_text.text(f"Traitement: {index+1}/{nb_emails_to_send}")
                    
                    attachment_path = os.path.join("uploaded_places", attachment_file)
                    success, msg = send_email_message(
                        smtp_server, smtp_port, username, password,
                        email_addr, subject, body, attachment_path, is_html=is_html
                    )
                    status_msg = "Succès" if success else f"Erreur: {msg}"
                    statuses.append({"email": email_addr, "fichier": attachment_file, "statut": status_msg})
                    
                    # Pause pour permettre de voir l'avancement
                    time.sleep(0.5)
                
                current_email.empty()
                status_text.text("Envoi terminé!")
                st.session_state.send_statuses = statuses
                st.success("✅ Tous les emails ont été traités!")
        else:
            st.warning("⚠️ Veuillez d'abord générer la distribution à l'étape 2.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ------------------------------
    # Étape 6 : Récapitulatif des envois
    # ------------------------------
    with st.container():
        st.markdown("<div class='step-container'>", unsafe_allow_html=True)
        st.markdown("### 📊 &nbsp;&nbsp; Étape 6: Récapitulatif des envois", unsafe_allow_html=True)
        
        if "send_statuses" in st.session_state:
            statuses_df = pd.DataFrame(st.session_state.send_statuses)
            
            # Comptage des succès et échecs
            success_count = sum(1 for status in st.session_state.send_statuses if "Succès" in status["statut"])
            error_count = sum(1 for status in st.session_state.send_statuses if "Erreur" in status["statut"])
            skipped_count = sum(1 for status in st.session_state.send_statuses if "Aucun envoi" in status["statut"])
            
            # Affichage des statistiques dans des métriques
            col1, col2, col3 = st.columns(3)
            col1.metric("Envois réussis", success_count)
            col2.metric("Envois en échec", error_count)
            col3.metric("Places restantes", skipped_count)
            
            # Tableau récapitulatif
            st.dataframe(
                statuses_df,
                use_container_width=True,
                hide_index=True
            )
            
            # Téléchargement du rapport
            csv_report = statuses_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Télécharger le rapport d'envoi", 
                data=csv_report,
                file_name="rapport_envoi.csv",
                mime="text/csv"
            )
        else:
            st.info("ℹ️ Aucun envoi n'a encore été effectué.")
        st.markdown("</div>", unsafe_allow_html=True)