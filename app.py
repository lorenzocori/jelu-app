import streamlit as st
import pandas as pd
import asyncio
import os
from io import StringIO
from estrattore_contatti import main as estrattore_main
from postino import process_csv, extract_text_from_homepage, generate_email_with_gemini

st.title("📬 Automazione JELU: da Excel all'email ✨")

# Email mittente e password
st.session_state["mittente"] = st.text_input("📤 Email del mittente", value=st.session_state.get("mittente", ""))
st.session_state["password"] = st.text_input("🔐 Password dell'app", type="password", value=st.session_state.get("password", ""))

# Caricamento Excel
file = st.file_uploader("📎 Carica il file Excel con le aziende", type=["xls"])

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

                # 🔧 Aggiunta colonne mancanti per la personalizzazione
                if "Oggetto Email" not in df_result.columns:
                    df_result["Oggetto Email"] = "Proposta di collaborazione con JELU Consulting"
                if "Corpo Email" not in df_result.columns:
                    df_result["Corpo Email"] = ""
                if "Da Inviare" not in df_result.columns:
                    df_result["Da Inviare"] = True

                st.session_state["df_result"] = df_result
                st.session_state["csv_buffer"] = df_result.to_csv(index=False).encode("utf-8")
                st.success("✅ Estrazione completata.")
            else:
                st.error("❌ File 'risultati.csv' non trovato dopo l'estrazione.")

        # Mostra editor personalizzazione se disponibile
        if "df_result" in st.session_state:
            df_result = st.session_state["df_result"]

            if "Azienda" in df_result.columns and "Sito" in df_result.columns and "Email" in df_result.columns:
                st.subheader("📨 Personalizzazione email")

                updated_rows = []

                for i, row in df_result.iterrows():
                    azienda = row["Azienda"]
                    sito = row["Sito"]
                    email = row["Email"]

                    if pd.notna(sito) and str(sito).startswith("http") and pd.notna(email):
                        key_prefix = f"{azienda}_{i}"

                        with st.expander(f"📩 Email per {azienda} ({email})"):
                            # Testo sito e suggerimento AI (solo se il campo è vuoto)
                            if not row["Corpo Email"]:
                                text = extract_text_from_homepage(sito)
                                corpo_default = generate_email_with_gemini(azienda, text) if text else "TESTO NON DISPONIBILE"
                            else:
                                corpo_default = row["Corpo Email"]

                            oggetto = st.text_input("Oggetto", row["Oggetto Email"], key=f"{key_prefix}_oggetto")
                            corpo = st.text_area("Testo email", corpo_default, height=200, key=f"{key_prefix}_corpo")
                            inviare = st.checkbox("✅ Invia a questa azienda", value=row["Da Inviare"], key=f"{key_prefix}_invio")

                            updated_rows.append({
                                "Azienda": azienda,
                                "Sito": sito,
                                "Email": email,
                                "Oggetto Email": oggetto,
                                "Corpo Email": corpo,
                                "Da Inviare": inviare
                            })

                st.session_state["df_result"] = pd.DataFrame(updated_rows)

    except Exception as e:
        st.error(f"❌ Errore durante la lettura del file: {e}")
else:
    st.info("Carica un file Excel per iniziare.")

# Invio email
if "df_result" in st.session_state and st.button("✉️ Invia Email a tutte le aziende selezionate"):
    mittente = st.session_state.get("mittente", "")
    password = st.session_state.get("password", "")
    df_to_send = st.session_state["df_result"]

    if mittente and password:
        st.info("📤 Invio email in corso...")
        df_to_send.to_csv("risultati.csv", index=False)

        log = st.empty()
        progress_bar = st.progress(0)

        try:
            process_csv(
                "risultati.csv",
                mittente,
                password,
                progress_callback=progress_bar.progress,
                log_callback=log.write
            )
            st.success("✅ Tutte le email sono state inviate.")

            st.download_button(
                "📥 Scarica il file aggiornato",
                df_to_send.to_csv(index=False).encode("utf-8"),
                file_name="email_inviate.csv",
                mime="text/csv"
            )
        except Exception as e:
            st.error(f"❌ Errore durante l'invio: {type(e).__name__} – {e}")
    else:
        st.error("❗ Inserisci sia l'email del mittente che la password dell'app.")
