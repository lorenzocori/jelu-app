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
    genai.configure(api_key="AIzaSyC3qCzwKd3eFnWrWQzXIpxutyomwXQ92V0")
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

            <!-- Logo condensato -->
            <div style="text-align:center; margin-bottom:40px;">
              <img src="https://raw.githubusercontent.com/lorenzocori/jelu-app/refs/heads/main/NEW_logo%20condensato%20bianco.png" alt="JELU Condensato" style="height:80px;">
            </div>

            <!-- Titolo -->
            <div style="text-align:left; max-width:700px; margin:auto; margin-bottom:20px;">
              <h2 style="color:#FDDD37;">Proposta di collaborazione con JELU Consulting</h2>
            </div>

            <!-- Corpo email -->
            <div style="max-width:700px; margin:auto; font-size:16px; line-height:1.6; color:white;">
              {corpo_html}
            </div>

            <!-- Firma -->
            <table cellpadding="0" cellspacing="0" style="font-family:Arial, sans-serif; font-size:15px; line-height:1.5; color:#ffffff; max-width:700px; margin:40px auto 0 auto;">
              <tr>
                <!-- Logo -->
                <td style="padding-right:20px; border-right:4px solid #FDDD37;">
                  <img src="https://raw.githubusercontent.com/lorenzocori/jelu-app/refs/heads/main/NEW_logo%20bianco.png" alt="JELU Consulting" style="height:100px;">
                  <br><br>
                  <a href="https://www.instagram.com/jeluconsulting" target="_blank" style="margin-right:8px;"><img src="https://upload.wikimedia.org/wikipedia/commons/a/a5/Instagram_icon.png" alt="Instagram" width="20"></a>
                  <a href="https://www.linkedin.com/company/jelu-consulting" target="_blank" style="margin-right:8px;"><img src="https://upload.wikimedia.org/wikipedia/commons/c/ca/LinkedIn_logo_initials.png" alt="LinkedIn" width="20"></a>
                  <a href="https://www.facebook.com/jeluconsulting" target="_blank"><img src="https://upload.wikimedia.org/wikipedia/commons/5/51/Facebook_f_logo_%282019%29.svg" alt="Facebook" width="20"></a>
                </td>

                <!-- Testo -->
                <td style="padding-left:20px;">
                  <p style="margin:0;"><strong style="font-size:17px;">Filippo Paglialonga</strong> / Responsabile Sales</p>
                  <p style="margin:5px 0;">Mobile: <strong>+39 348 824 4062</strong><br>
                  E-mail: <a href="mailto:ufficiostampa@jelu.it" style="color:#FDDD37;">ufficiostampa@jelu.it</a></p>

                  <p style="margin-top:20px;"><strong>JELU Consulting</strong><br>
                  Viale Romania 32, 00197 Roma<br>
                  <a href="https://jelu.it" style="color:#FDDD37;">jelu.it</a></p>

                  <p style="margin-top:10px; font-size:9pt; font-family:Georgia, serif; color:rgb(0,128,0); line-height:1.2;">
                    <img src="https://lh7-rt.googleusercontent.com/docsz/AD_4nXdopXHwK7kWbjCvwTGeZ5QShlXY4RgXV0vJ3EYtxdSrmxYK5b9qYvhatXCtpIzpgrmHQ-UF5RsZHmpSNc9xkB9HztcpM66K8K2NvXv_hFPF-MTo1kfxX5BJgaJNfa0JhJRKVOTa4qFaO6_R7FTH?key=0wII50Vk6syeoMkIOkI7kJMl" width="32" height="32" style="vertical-align:middle; margin-right:8px;">
                    Think before you print
                  </p>
                </td>
              </tr>

              <!-- Footer disclaimer -->
              <tr>
                <td colspan="2" style="padding-top:20px; font-size:12px; color:#cccccc;">
                  <p style="margin-bottom:5px;">
                    <strong>IT</strong> / Questo messaggio, ed eventuali allegati, è diretto all’esclusiva attenzione del destinatario...
                  </p>
                  <p style="margin-top:5px;">
                    <strong>EN</strong> / This email and any attached files are only for the attention of the intended recipient...
                  </p>
                </td>
              </tr>
            </table>
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
        import traceback
        traceback.print_exc()
        print(f"❌ Errore dettagliato nell'invio a {destinatario}: {type(e).__name__} - {e}")
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
