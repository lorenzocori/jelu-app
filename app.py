
import streamlit as st
import pandas as pd
import asyncio
import os
from io import StringIO
from estrattore_contatti import main as estrattore_main
from postino import process_csv, extract_text_from_homepage, generate_email_with_gemini

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
        df = pd.read_excel(file, sheet_name="Risultati", usecols=["Ragione sociale"])
        aziende = df["Ragione sociale"].dropna().unique().tolist()
        st.success(f"✅ {len(aziende)} aziende caricate correttamente.")

        temp_file = "aziende_temp.csv"
        pd.DataFrame(aziende, columns=["Azienda"]).to_csv(temp_file, index=False)

        if st.button("🚀 Estrai contatti"):
            st.info("⏳ Estrazione in corso...")
            asyncio.run(estrattore_main(csv_path=temp_file))

            if os.path.exists("risultati.csv"):
                df_result = pd.read_csv("risultati.csv")
                st.session_state["df_result"] = df_result
                st.session_state["csv_buffer"] = df_result.to_csv(index=False).encode("utf-8")
                st.success("✅ Estrazione completata e dati caricati in memoria.")
            else:
                st.error("❌ File 'risultati.csv' non trovato dopo l'estrazione.")

        if "df_result" in st.session_state:
            df_result = st.session_state["df_result"]
            if "Azienda" in df_result.columns and "Sito" in df_result.columns and "Email" in df_result.columns:
                st.subheader("📨 Anteprima delle email generate")

                for _, row in df_result.iterrows():
                    azienda = row["Azienda"]
                    sito = row["Sito"]
                    destinatario = row["Email"]

                    with st.expander(f"📩 {azienda} — {destinatario if pd.notna(destinatario) else 'email non trovata'}"):
                        if pd.isna(sito) or not str(sito).startswith("http"):
                            st.warning(f"⚠️ Nessun sito valido trovato per {azienda}")
                            continue

                        try:
                            text = extract_text_from_homepage(sito)
                            if not text or len(text.strip()) < 30:
                                st.warning("⚠️ Nessun testo significativo trovato sulla homepage.")
                                continue

                            st.info("✅ Testo estratto correttamente dal sito.")
                            st.code(text[:500] + "...", language="text")

                            corpo_email = generate_email_with_gemini(azienda, text)

                            if corpo_email and corpo_email.strip():
                                st.success("✅ Email generata con Gemini:")
                                st.markdown("**Oggetto:** Proposta di collaborazione con JELU Consulting")
                                st.write(corpo_email)
                            else:
                                st.warning("⚠️ Gemini non ha restituito testo.")
                        except Exception as e:
                            st.error(f"❌ Errore durante l'elaborazione per {azienda}: {e}")

    except Exception as e:
        st.error(f"❌ Errore durante la lettura del file: {e}")
else:
    st.info("Carica un file Excel per iniziare.")

# Invio email se risultati presenti
# 🔁 Pulsante per inviare email
if "df_result" in st.session_state:

    st.subheader("✉️ Invio Email")

    modifica_email = st.checkbox("✏️ Voglio modificare le email prima dell'invio")

    mittente = st.session_state.get("mittente", "")
    password = st.session_state.get("password", "")

    if mittente and password:

        if modifica_email:
            # Modalità personalizzazione manuale
            df_result = st.session_state["df_result"]
            emails_da_inviare = []

            st.info("Modifica oggetto, corpo e scegli le email da inviare")

            for i, row in df_result.iterrows():
                azienda = row["Azienda"]
                email = row["Email"]
                sito = row["Sito"]

                if pd.isna(email) or email.strip() == "" or not str(sito).startswith("http"):
                    continue

                from postino import extract_text_from_homepage, generate_email_with_gemini
                testo = extract_text_from_homepage(sito)
                corpo_default = generate_email_with_gemini(azienda, testo) if testo else ""

                with st.expander(f"📩 {azienda} ({email})"):
                    invia = st.checkbox(f"✅ Invia a {azienda}", key=f"invia_{i}", value=True)
                    oggetto = st.text_input("Oggetto", value="Proposta di collaborazione con JELU Consulting", key=f"subject_{i}")
                    corpo = st.text_area("Corpo", value=corpo_default, height=200, key=f"body_{i}")

                    if invia:
                        emails_da_inviare.append({
                            "azienda": azienda,
                            "email": email,
                            "subject": oggetto,
                            "body": corpo
                        })

            if st.button("📨 Invia Email Selezionate"):
                from postino import invia_email

                for idx, email in enumerate(emails_da_inviare):
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

        else:
            # Modalità automatica già esistente
            if st.button("📨 Invia Email a tutte le aziende (automatica)"):
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
