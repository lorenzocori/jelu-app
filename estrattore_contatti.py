import os
import time
import re
import pandas as pd
from bs4 import BeautifulSoup
import requests
from requests.exceptions import RequestException, Timeout, HTTPError, SSLError
from duckduckgo_search import DDGS  # ✅ DuckDuckGo
import random
import asyncio
import aiohttp

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"
}


# Estrai email
def estrai_email(text):
    pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    return re.findall(pattern, text)

# Estrai telefono
def estrai_telefono(text):
    pattern = r'(\+39\s*\d{2,4}[\s\-\.]?\d{3,4}[\s\-\.]?\d{3,4})'
    numeri = re.findall(pattern, text)
    return [re.sub(r'[\s\-\.]', '', num) for num in numeri]

async def fetch(session, url):
    try:
        async with session.get(url, headers=headers, timeout=15) as response:
            response.raise_for_status()
            return await response.text()
    except Exception as e:
        print(f"❌ Errore fetch {url}: {e}")
        return None

# Trova il sito ufficiale con DuckDuckGo
def trova_sito_duckduckgo(azienda):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(f"{azienda} sito ufficiale", max_results=5))

        for result in results:
            url = result["href"]
            if not any(s in url for s in ['facebook.com', 'linkedin.com', 'instagram.com', 'ufficiocamerale.it']):
                return url

        return None
    except Exception as e:
        print(f"❌ Errore nella ricerca DuckDuckGo per {azienda}: {e}")
        return None

# Cerca e trova la pagina "Contatti"
async def trova_pagina_contatti(session, base_url):
    try:
        if not base_url.startswith("http"):
            return None

        await asyncio.sleep(random.uniform(2.5, 5.5))  # ⏳
        async with session.get(base_url, headers=headers, timeout=15) as response:
            response.raise_for_status()
            content = await response.read()
            html = content.decode("utf-8", errors="ignore")


        soup = BeautifulSoup(html, 'html.parser')

        for link in soup.find_all('a', href=True):
            if 'contatt' in link.text.lower() or 'contact' in link.text.lower():
                href = link['href']
                if href.startswith('http'):
                    return href
                elif href.startswith('/'):
                    return base_url.rstrip('/') + href
        return base_url
    except Exception as e:
        print(f"❌ Errore su {base_url}: {e}")
        return base_url
    except HTTPError as http_err:
        print(f"❌ HTTP Error ({response.status_code}) per {base_url}: {http_err}")
    except Timeout:
        print(f"⏳ Timeout per {base_url}. Il sito è troppo lento.")
    except SSLError:
        print(f"❌ Errore SSL per {base_url}. Il certificato potrebbe essere scaduto.")
    except RequestException as err:
        print(f"❌ Errore generico per {base_url}: {err}")
    return base_url

semaforo = asyncio.Semaphore(5) #RED LIGHTTTTT

# Processa un'azienda
async def processa_azienda_async(index, azienda, session):
    async with semaforo:
        await asyncio.sleep(random.uniform(5, 10))
        loop = asyncio.get_running_loop()
        sito = await loop.run_in_executor(None, trova_sito_duckduckgo, azienda)

        if not sito:
            return index, azienda, "", "", "", "FALLITO"

        contatti_url = await trova_pagina_contatti(session, sito)
        await asyncio.sleep(random.uniform(2.5, 5.5))

        try:
            async with session.get(contatti_url, headers=headers, timeout=15) as response:
                response.raise_for_status()
                html = await response.text()
        except Exception as e:
            print(f"❌ Errore su {contatti_url}: {e}")
            return index, azienda, sito, "", "", "FALLITO"

        soup = BeautifulSoup(html, 'html.parser')
        testo = soup.get_text(separator=' ')
        emails = set(estrai_email(testo))
        telefoni = set(estrai_telefono(testo))

        for link in soup.find_all('a', href=True):
            href = link['href']
            if 'mailto:' in href:
                emails.add(href.replace('mailto:', '').split('?')[0])
            elif 'tel:' in href:
                telefoni.add(href.replace('tel:', '').split('?')[0])

        stato = "OK" if emails or telefoni else "FALLITO"

        return index, azienda, sito, ", ".join(emails), ", ".join(telefoni), stato

async def main(csv_path="aziende.csv"):
    try:
        df_aziende = pd.read_csv(csv_path, usecols=[0], names=["Azienda"], header=0, on_bad_lines='skip')
        aziende_da_analizzare = df_aziende["Azienda"].dropna().unique().tolist()
        print(f"\n📌 {len(aziende_da_analizzare)} aziende verranno analizzate...\n")
    except Exception as e:
        print(f"❌ Errore nella lettura delle aziende: {e}")
        return

    if not os.path.exists("risultati.csv"):
        pd.DataFrame(columns=["Azienda", "Sito", "Email", "Telefono", "Stato"]).to_csv("risultati.csv", index=False)

    async with aiohttp.ClientSession() as session:
        tasks = []
        for index, azienda in enumerate(aziende_da_analizzare):
            tasks.append(processa_azienda_async(index, azienda, session))

        successi = 0
        for future in asyncio.as_completed(tasks):
            index, azienda, sito, emails, telefoni, stato = await future
            if stato == "OK":
                successi += 1

            print(f"📂 Dati aggiornati per {azienda}")

            with open("risultati.csv", "a", encoding="utf-8", newline='') as f:
                row_df = pd.DataFrame([{
                    "Azienda": azienda,
                    "Sito": sito,
                    "Email": emails,
                    "Telefono": telefoni,
                    "Stato": stato
                }])
                row_df.to_csv(f, header=False, index=False)

        print(f"\n✅ Completati con successo: {successi} / {len(aziende_da_analizzare)}")
        print("\n✅ Estrazione completata.")

# Non chiamare direttamente asyncio.run(main()) se lo usi in Streamlit
#if __name__ == "__main__":
#    asyncio.run(main())
