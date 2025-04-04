if "df_result" in st.session_state and st.button("✉️ Invia Email a tutte le aziende"):
    mittente = st.session_state.get("mittente", "")
    password = st.session_state.get("password", "")

    if mittente and password:
        st.info("📤 Invio email in corso...")

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

            if os.path.exists("risultati.csv"):
                with open("risultati.csv", "rb") as f:
                    st.download_button("📥 Scarica il file aggiornato", f, file_name="email_inviate.csv")
            else:
                st.warning("⚠️ File 'risultati.csv' non trovato. Nessun file da scaricare.")

        except Exception as e:
            st.error(f"❌ Errore durante l'invio: {type(e).__name__} – {e}")
    else:
        st.error("❗ Inserisci sia l'email del mittente che la password dell'app.")
