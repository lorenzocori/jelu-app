import streamlit as st
import pandas as pd
import asyncio
import os
from estrattore_contatti import main as estrattore_main
from postino import process_csv

st.title("📬 Automazione JELU: da Excel all'email ✨")

# Caricamento file Excel
file = st.file_uploader("📎 Carica il file Excel con le aziende", type=["xls"])

# Inserimento email mittente e password app
if "mittente" not in st.session_state:
    st.session_state["mittente"] = ""
if "password" not in st.session_state:
    st.session_state["password"] = ""

st.session_state["mittente"] = st.text_input("📤 Email del mittente", st.session_state["mittente"])
st.session_state["password"] = st.text_input("🔐 Password dell'app", type="password", value=st.session_state["password"])


if file:
    try:
        if os.path.exists("risultati.csv"):
            os.remove("risultati.csv")

        df = pd.read_excel(file, sheet_name="Risultati", usecols=["Ragione sociale"])
        aziende = df["Ragione sociale"].dropna().unique().tolist()
        st.success(f"✅ {len(aziende)} aziende caricate correttamente.")

        temp_file = "aziende_temp.csv"
        pd.DataFrame(aziende, columns=["Azienda"]).to_csv(temp_file, index=False)

        if st.button("🚀 Estrai contatti"):
            st.info("⏳ Estrazione in corso...")
            asyncio.run(estrattore_main(csv_path=temp_file))
            st.success("✅ Estrazione completata. File generato: risultati.csv")

        if os.path.exists("risultati.csv"):
            df_result = pd.read_csv("risultati.csv")
            st.session_state["df_result"] = df_result  # 🔒 SALVA STATO

            if "Azienda" in df_result.columns and "Sito" in df_result.columns and "Email" in df_result.columns:
                st.subheader("📨 Anteprima delle email generate")
                from postino import extract_text_from_homepage, generate_email_with_gemini

                for _, row in df_result.iterrows():
                    azienda = row["Azienda"]
                    sito = row["Sito"]
                    destinatario = row["Email"]

                    if pd.notna(sito) and str(sito).startswith("http") and pd.notna(destinatario):
                        text = extract_text_from_homepage(sito)
                        if text:
                            corpo_email = generate_email_with_gemini(azienda, text)
                            with st.expander(f"📩 Email per {azienda} ({destinatario})"):
                                st.markdown("**Oggetto:** Proposta di collaborazione con JELU Consulting")
                                st.write(corpo_email)
    except Exception as e:
        st.error(f"❌ Errore durante la lettura del file: {e}")
else:
    st.info("Carica un file Excel per iniziare.")

# 🔁 Pulsante sempre attivo se abbiamo dati
if "df_result" in st.session_state and st.button("✉️ Invia Email a tutte le aziende"):
    mittente = st.session_state.get("mittente", "")
    password = st.session_state.get("password", "")

    if mittente and password:
        st.info("📤 Invio email in corso...")

        log = st.empty()
        progress_bar = st.progress(0)

        process_csv(
            "risultati.csv",
            mittente,
            password,
            progress_callback=progress_bar.progress,
            log_callback=log.write
        )

        st.success("✅ Tutte le email sono state inviate.")
        with open("risultati.csv", "rb") as f:
            st.download_button("📥 Scarica il file aggiornato", f, file_name="email_inviate.csv")
    else:
        st.error("❗ Inserisci sia l'email del mittente che la password dell'app.")

