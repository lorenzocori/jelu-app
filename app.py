
import streamlit as st
import pandas as pd
import asyncio
import os
from estrattore_contatti import main as estrattore_main
from postino import extract_text_from_homepage, generate_email_with_gemini, invia_email

st.set_page_config(layout="wide")
st.title("📬 Automazione JELU: da Excel all'email ✨")

file = st.file_uploader("📎 Carica il file Excel con le aziende", type=["xls"])

if "mittente" not in st.session_state:
    st.session_state["mittente"] = ""
if "password" not in st.session_state:
    st.session_state["password"] = ""
if "df_result" not in st.session_state:
    st.session_state["df_result"] = None
if "email_states" not in st.session_state:
    st.session_state["email_states"] = {}

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
                st.session_state["df_result"] = df_result
                st.rerun()

        df_result = st.session_state["df_result"]

        if df_result is not None and "Azienda" in df_result.columns and "Sito" in df_result.columns and "Email" in df_result.columns:
            st.subheader("📨 Email personalizzabili")
            emails_da_inviare = []

            for i, row in df_result.iterrows():
                azienda = row["Azienda"]
                email = row["Email"]
                sito = row["Sito"]
                if pd.isna(email) or not str(sito).startswith("http"):
                    continue

                if azienda not in st.session_state["email_states"]:
                    st.session_state["email_states"][azienda] = {
                        "subject": "Proposta di collaborazione con JELU Consulting",
                        "body": "",
                        "generated": False,
                        "send": False
                    }

                stato = st.session_state["email_states"][azienda]

                with st.expander(f"📩 {azienda} ({email})"):
                    stato["send"] = st.checkbox(f"✅ Invia a {azienda}", value=stato["send"], key=f"invia_{i}")
                    stato["subject"] = st.text_input("Oggetto", value=stato["subject"], key=f"subject_{i}")

                    if st.button("✨ Genera email con Gemini", key=f"generate_{i}"):
                        text = extract_text_from_homepage(sito)
                        corpo_generato = generate_email_with_gemini(azienda, text) if text else "⚠️ Nessun testo disponibile"
                        stato["body"] = corpo_generato
                        stato["generated"] = True

                    stato["body"] = st.text_area("Corpo dell'email", value=stato["body"], height=200, key=f"body_{i}")

                    if stato["send"]:
                        emails_da_inviare.append({
                            "azienda": azienda,
                            "email": email,
                            "subject": stato["subject"],
                            "body": stato["body"]
                        })

            if emails_da_inviare and st.button("📨 Invia Email Selezionate"):
                mittente = st.session_state["mittente"]
                password = st.session_state["password"]

                for email in emails_da_inviare:
                    success = invia_email(
                        mittente,
                        password,
                        email["email"],
                        email["subject"],
                        email["body"]
                    )
                    if success:
                        st.success(f"✅ Email inviata a {email['azienda']}")
                    else:
                        st.error(f"❌ Errore invio a {email['azienda']}")
    except Exception as e:
        st.error(f"❌ Errore durante la lettura del file: {e}")
else:
    st.info("Carica un file Excel per iniziare.")
