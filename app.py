import streamlit as st
import pandas as pd

# 1. Configuration Globale [cite: 45]
st.set_page_config(page_title="Finsight AI", layout="wide", initial_sidebar_state="expanded")

# Initialisation des variables d'état [cite: 46, 48, 64]
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'first_login' not in st.session_state:
    st.session_state['first_login'] = True
if 'user_profile' not in st.session_state:
    st.session_state['user_profile'] = "Non défini"

# --- PARTIE 1 : LOGIN "BIDON" [cite: 47, 50] ---
if not st.session_state['authenticated']:
    st.title("🚀 Bienvenue sur Finsight AI")
    
    tab1, tab2 = st.tabs(["Connexion", "Inscription"])
    
    with tab1:
        st.text_input("Email", key="login_email") # [cite: 52]
        st.text_input("Mot de passe", type="password", key="login_pwd") # [cite: 53]
        if st.button("Se connecter"): # [cite: 54]
            # Simulation de validation [cite: 55]
            st.session_state['authenticated'] = True
            st.rerun()
            
    with tab2:
        st.text_input("Nom complet") # [cite: 57]
        st.text_input("Email professionnel/personnel") # [cite: 58]
        if st.button("Créer un compte"): # [cite: 61]
            st.session_state['authenticated'] = True
            st.session_state['first_login'] = True
            st.rerun()

# --- PARTIE 2 : ONBOARDING (Profilage & Portefeuille) [cite: 63] ---
elif st.session_state['first_login']:
    st.header("🎯 Personnalisez votre expérience")
    st.write("Répondez à ces questions pour que notre IA calibre ses analyses.") # [cite: 12]

    # Section A: Définition du Profil [cite: 65, 68]
    with st.form("profiling_form"):
        age = st.number_input("Âge", min_value=18, max_value=100) # [cite: 69]
        horizon = st.selectbox("Horizon d'investissement", 
                              options=["Court terme (< 1 an)", "Moyen terme (1-5 ans)", "Long terme (> 5 ans)"]) # [cite: 70]
        perte = st.slider("Réaction face à une perte de 10%", 0, 10, help="0: Vente panique, 10: Achat de renfort") # [cite: 71]
        experience = st.radio("Expérience en trading", options=["Aucune", "Occasionnelle", "Régulière/Expert"]) # [cite: 72]
        
        # Section B: Portefeuille [cite: 74, 78]
        # Note: Dans un cas réel, chargez le CSV depuis l'URL GitHub fournie [cite: 14]
        assets = st.multiselect("Sélectionnez les actifs à suivre", 
                               options=["AAPL", "TSLA", "BTC", "GOLD", "CAC40", "MSFT"])
        
        submitted = st.form_submit_button("Finaliser mon profil")
        
        if submitted:
            # Logique de calcul de profil simplifiée [cite: 7, 73]
            if experience == "Aucune":
                st.session_state['user_profile'] = "Débutant" # [cite: 9]
            elif experience == "Occasionnelle":
                st.session_state['user_profile'] = "Intermédiaire" # [cite: 10]
            else:
                st.session_state['user_profile'] = "Confirmé" # [cite: 11]
            
            st.session_state['first_login'] = False
            st.success({"Profil déterminé": st.session_state['user_profile']})
            st.rerun()

# --- PARTIE 3 : ACCÈS AU DASHBOARD (Une fois onboardé) ---
else:
    # Sidebar persistante [cite: 118, 119]
    with st.sidebar:
        st.title("📊 Finsight AI") # [cite: 121]
        st.write(f"Utilisateur : Utilisateur Démo") # [cite: 123]
        st.caption(f"Profil : **{st.session_state['user_profile']}**") # [cite: 124]
        
        menu = st.radio("Menu", ["Tableau de Bord", "Mon Compte", "Déconnexion"]) # [cite: 125, 126]
        
        if menu == "Déconnexion":
            st.session_state['authenticated'] = False
            st.rerun()

    st.title("Tableau de Bord")
    st.info(f"Bienvenue ! En tant que **{st.session_state['user_profile']}**, l'interface s'adaptera à votre niveau.") # [cite: 22]