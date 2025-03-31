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
mittente = st.text_input("📤 Email del mittente (es. jelu@gmail.com)")
password = st.text_input("🔐 Password dell'app (Gmail, non la password normale)", type="password")

if file:
    try:
        # Estrai ragioni sociali dal foglio "Risultati"
        df = pd.read_excel(file, sheet_name="Risultati", usecols=["Ragione Sociale"])
        aziende = df["Ragione Sociale"].dropna().unique().tolist()
        st.success(f"✅ {len(aziende)} aziende caricate correttamente.")

        # Salva in CSV temporaneo per usarlo nello script async
        temp_file = "aziende_temp.csv"
        pd.DataFrame(aziende, columns=["Azienda"]).to_csv(temp_file, index=False)

        # Estrazione contatti
        if st.button("🚀 Estrai contatti"):
            st.info("⏳ Estrazione in corso...")
            asyncio.run(estrattore_main(csv_path=temp_file))
            st.success("✅ Estrazione completata. File generato: risultati.csv")

        # Invio email solo se esiste il file risultati
        if os.path.exists("risultati.csv"):
            st.write("📄 File con email generato. Pronto per l'invio!")

            if st.button("✉️ Invia Email a tutte le aziende"):
                if mittente and password:
                    st.info("📤 Invio email in corso...")
                    process_csv("risultati.csv", mittente, password)
                    st.success("✅ Tutte le email sono state inviate.")

                    with open("risultati.csv", "rb") as f:
                        st.download_button("📥 Scarica il file aggiornato", f, file_name="email_inviate.csv")
                else:
                    st.error("❗ Inserisci sia l'email del mittente che la password dell'app.")
    except Exception as e:
        st.error(f"❌ Errore durante la lettura del file: {e}")
else:
    st.info("Carica un file Excel per iniziare.")
