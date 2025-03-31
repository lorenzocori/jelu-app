import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import pandas as pd
import os
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def extract_text_from_homepage(url):
    """Effettua il web scraping per estrarre il testo principale dalla homepage."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Errore durante la richiesta a {url}: {e}")
        return None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Rimuove elementi non utili (script, stile, header, footer, nav)
    for tag in ['script', 'style', 'header', 'footer', 'nav', 'aside']:
        for element in soup.find_all(tag):
            element.extract()
    
    text = ' '.join(soup.stripped_strings)
    return text[:4000]  # Limite di 4000 caratteri per evitare problemi con l'API

def generate_email_with_gemini(company_name, text):
    """Invia il testo estratto a Gemini Pro 1.5 per generare un'email personalizzata."""
    genai.configure(api_key="AIzaSyDmPoXzsDWtKfg0pLkZKfA_vdPHrIpfVPI")
    model = genai.GenerativeModel("gemini-1.5-flash-latest")
    
    prompt = (
        f"""
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
    )
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Errore nella generazione dell'email per {company_name}: {e}")
        return None

def process_csv(file_path, mittente, password):
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

        if pd.isna(url) or not str(url).startswith("http") or pd.isna(email_destinatario):
            print(f"Dati mancanti per {company_name}, saltato.")
            df.at[index, "Stato Invio"] = "Saltato"
            continue

        print(f"Processing: {company_name} ({url})")
        text = extract_text_from_homepage(url)

        if text:
            corpo_email = generate_email_with_gemini(company_name, text)
            oggetto = f"Proposta di collaborazione con JELU Consulting"
            
            df.at[index, "Oggetto Email"] = oggetto

            success = invia_email(mittente, password, email_destinatario, oggetto, corpo_email)
            df.at[index, "Stato Invio"] = "OK" if success else "Errore"
        else:
            print(f"Nessun testo trovato per {company_name}")
            df.at[index, "Stato Invio"] = "Errore"

        time.sleep(3)

    df.to_csv(file_path, index=False)
    time.sleep(3)



def invia_email(mittente, password, destinatario, oggetto, corpo):
    try:
        msg = MIMEMultipart()
        msg["From"] = mittente
        msg["To"] = destinatario
        msg["Subject"] = oggetto

        msg.attach(MIMEText(corpo, "plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(mittente, password)
            server.sendmail(mittente, destinatario, msg.as_string())

        print(f"✅ Email inviata a {destinatario}")
        return True
    except Exception as e:
        print(f"❌ Errore nell'invio a {destinatario}: {e}")
        return False


if __name__ == "__main__":
    API_KEY = "..."
    FILE_PATH = "..."

    EMAIL_MITTENTE = input("Inserisci l'email del mittente: ")
    PASSWORD_EMAIL = input("Inserisci la password dell'app: ")

    process_csv(FILE_PATH, EMAIL_MITTENTE, PASSWORD_EMAIL)

