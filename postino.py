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
    genai.configure(api_key="INSERT_YOUR_API_KEY")
    model = genai.GenerativeModel("gemini-1.5-flash-latest")

    prompt = f"""
    Scrivi un'email formale e personalizzata indirizzata a {company_name}, da parte di JELU Consulting.
    (Testo sito web):\n{text}
    Firma: JELU Consulting, Email: ufficiostampa@jelu.it, jelu.it
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
                <img src="https://static.wixstatic.com/media/d61b9f_43cd02c06bdf456dba086be862a4b4bc~mv2.png" style="width: 150px; height: auto; margin-bottom: 30px;">
            </div>
            <div style="max-width:700px; margin:auto; font-size:16px; line-height:1.6;">
              {corpo_html}
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
        if not os.path.exists(file_path):
            print(f"❌ File non trovato: {file_path}")
            return

        df = pd.read_csv(file_path)

        required = ["Sito", "Azienda", "Email", "Oggetto Email", "Corpo Email", "Da Inviare"]
        for col in required:
            if col not in df.columns:
                print(f"❌ Colonna mancante nel CSV: {col}")
                return

        for index, row in df.iterrows():
            if not row["Da Inviare"]:
                print(f"❌ Email NON inviata a {row['Azienda']} (utente ha deselezionato)")
                df.at[index, "Stato Invio"] = "Saltato"
                continue

            email = row["Email"]
            sito = row["Sito"]
            azienda = row["Azienda"]
            oggetto = row["Oggetto Email"]
            corpo = row["Corpo Email"]

            success = invia_email(mittente, password, email, oggetto, corpo)
            df.at[index, "Stato Invio"] = "OK" if success else "Errore"

            if log_callback:
                log_callback(f"{azienda}: {'✅ Inviata' if success else '❌ Errore'}")

            if progress_callback:
                progress_callback((index + 1) / len(df))

            time.sleep(3)

        df.to_csv(file_path, index=False)
        print("✅ Invii completati e salvati nel CSV.")

    except Exception as e:
        print(f"❌ Errore generale in process_csv: {type(e).__name__} - {e}")

if __name__ == "__main__":
    FILE_PATH = "risultati.csv"
    EMAIL = input("Email mittente: ")
    PASS = input("Password app: ")
    process_csv(FILE_PATH, EMAIL, PASS)
