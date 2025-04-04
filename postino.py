import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import pandas as pd
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def extract_text_from_homepage(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Errore durante la richiesta a {url}: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    for tag in ['script', 'style', 'header', 'footer', 'nav', 'aside']:
        for element in soup.find_all(tag):
            element.extract()

    text = ' '.join(soup.stripped_strings)
    return text[:4000]

def generate_email_with_gemini(company_name, text):
    genai.configure(api_key="AIzaSyBwVUUPRA8TNfZ4M6mEOMaBeudjFwok30Y")
    model = genai.GenerativeModel("gemini-1.5-flash-latest")

    prompt = f"""
    Scrivi un'email formale e personalizzata indirizzata a **{company_name}**, da parte di JELU Consulting.

    JELU Consulting è una realtà nata nella LUISS Guido Carli, che si occupa di consulenza aziendale e innovazione strategica. 
    Aiutiamo le aziende a crescere offrendo soluzioni personalizzate, con oltre 90 associati, 250 alumni e più di 20 partnership attive.

    Di seguito trovi informazioni sull’azienda {company_name}, estratte dal suo sito web:

    {text}

    Usa queste informazioni per rendere l’email davvero rilevante e mirata. Evita segnaposto come [Nome del destinatario] o [Nome dell'azienda del destinatario]. 
    Inserisci direttamente il nome dell'azienda nel testo. 
    Non scrivere l'oggetto. Scrivi solo il corpo dell'email.

    Firma l’email così:

    Cordiali saluti,  
    JELU Consulting  
    Email: ufficiostampa@jelu.it  
    Sito web: jelu.it
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Errore nella generazione dell'email per {company_name}: {e}")
        return None

def invia_email(mittente, password, destinatario, oggetto, corpo):
    try:
        corpo_html = corpo.replace("\n", "<br>")
        html_template = f"""
        <html>
          <body style="background-color:#003153; color:white; font-family:Arial, sans-serif; padding:30px;">
            <div style="text-align:center;">
                <img src="https://static.wixstatic.com/media/d61b9f_43cd02c06bdf456dba086be862a4b4bc~mv2.png" alt="JELU Consulting" style="width: 150px; height: auto; margin-bottom: 30px;">
            </div>

            <div style="max-width:700px; margin:auto; font-size:16px; line-height:1.6;">
              {corpo_html}
            </div>

            <div style="text-align:center; margin-top:40px;">
                <img src="https://static.wixstatic.com/media/d61b9f_43cd02c06bdf456dba086be862a4b4bc~mv2.png" alt="JELU Consulting" style="width: 150px; height: auto; margin-bottom: 30px;">
            </div>
          </body>
        </html>
        """

        msg = MIMEMultipart("alternative")
        msg["From"] = mittente
        msg["To"] = destinatario
        msg["Subject"] = oggetto

        msg.attach(MIMEText(corpo, "plain"))
        msg.attach(MIMEText(html_template, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(mittente, password)
            server.sendmail(mittente, [destinatario], msg.as_string())

        print(f"✅ Email inviata a {destinatario}")
        return True
    except Exception as e:
        print(f"❌ Errore nell'invio a {destinatario}: {e}")
        return False

def process_csv(file_path, mittente, password, progress_callback=None, log_callback=None):
    try:
        print("📂 Directory corrente:", os.getcwd())
        if not os.path.exists(file_path):
            print(f"❌ File non trovato: {file_path}")
            return

        df = pd.read_csv(file_path)

        if "Sito" not in df.columns or "Azienda" not in df.columns or "Email" not in df.columns:
            print("Errore: Il file CSV deve contenere le colonne 'Sito', 'Azienda' e 'Email'")
            return

        if "Stato Invio" not in df.columns:
            df["Stato Invio"] = None

        if "Oggetto Email" not in df.columns:
            df["Oggetto Email"] = None

        for index, row in df.iterrows():
            url = row.get("Sito")
            company_name = row.get("Azienda")
            email_destinatario = row.get("Email")
            success = False

            if pd.isna(url) or not str(url).startswith("http") or pd.isna(email_destinatario):
                print(f"Dati mancanti per {company_name}, saltato.")
                df.at[index, "Stato Invio"] = "Saltato"
                continue

            print(f"\n📨 Generazione email per: {company_name} ({url})")
            text = extract_text_from_homepage(url)

            if text:
                corpo_email = generate_email_with_gemini(company_name, text)
                if corpo_email:
                    oggetto = f"Proposta di collaborazione con JELU Consulting"
                    df.at[index, "Oggetto Email"] = oggetto
                    print("✉️ Invio email a:", email_destinatario)
                    success = invia_email(mittente, password, email_destinatario, oggetto, corpo_email)
                else:
                    print(f"❌ Email non generata per {company_name}")
            else:
                print(f"❌ Nessun testo trovato per {company_name}")

            df.at[index, "Stato Invio"] = "OK" if success else "Errore"

            if log_callback:
                log_callback(f"📨 Email per {company_name}: {'✅ Inviata' if success else '❌ Errore'}")

            if progress_callback:
                progress_callback((index + 1) / len(df))

            time.sleep(3)

        df.to_csv(file_path, index=False)
        print("\n✅ Tutte le email processate e salvate nel file.")

    except Exception as e:
        print(f"❌ Errore fatale in process_csv: {type(e).__name__} - {e}")

if __name__ == "__main__":
    try:
        FILE_PATH = "risultati.csv"
        print("🛠️ Directory corrente:", os.getcwd())
        EMAIL_MITTENTE = input("Inserisci l'email del mittente: ")
        PASSWORD_EMAIL = input("Inserisci la password dell'app: ")
        process_csv(FILE_PATH, EMAIL_MITTENTE, PASSWORD_EMAIL)
    except Exception as e:
        print(f"❌ Errore fatale: {type(e).__name__} - {e}")
