import requests
from bs4 import BeautifulSoup
import re
import csv
import time
import pdfplumber
from io import BytesIO

BASE_URL = "https://www.guarulhos.sp.leg.br"
LISTA_URL = BASE_URL + "/documentos/tipo:leis-municipais-3/subtipo:portaria-8"

def extrair_matricula(texto):
    m = re.search(r'c[oó]d\.?\s*(\d+)', texto, re.IGNORECASE)
    return m.group(1) if m else ""

def identificar_tipo(texto):
    texto = texto.upper()
    if "LICENÇA" in texto:
        return "Licença"
    if "CONCEDE" in texto:
        return "Concessão"
    if "EXONERA" in texto:
        return "Exoneração"
    if "NOMEIA" in texto:
        return "Nomeação"
    if "DESIGNA" in texto:
        return "Designação"
    return "Outro"

def extrair_texto_pdf(url):
    pdf_bytes = requests.get(url).content
    texto = ""
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for pagina in pdf.pages:
            texto += pagina.extract_text() or ""
    return texto

def main():
    response = requests.get(LISTA_URL)
    soup = BeautifulSoup(response.text, "html.parser")

    registros = []

    artigos = soup.find_all("article")

    for art in artigos:
        h2 = art.find("h2")
        if not h2:
            continue

        link = h2.find("a")
        if not link:
            continue

        portaria = link.text.strip()
        pagina_url = link["href"]

        texto_artigo = art.get_text(" ", strip=True)
        data_match = re.search(r"Data Portaria:\s*(\d{2}/\d{2}/\d{4})", texto_artigo)
        data = data_match.group(1) if data_match else ""

        pagina_html = requests.get(pagina_url).text
        pagina_soup = BeautifulSoup(pagina_html, "html.parser")

        pdf_link = pagina_soup.find("a", href=re.compile(r"\.pdf"))
        if not pdf_link:
            continue

        texto_pdf = extrair_texto_pdf(pdf_link["href"])

        matricula = extrair_matricula(texto_pdf)
        tipo = identificar_tipo(texto_pdf)
        assunto = texto_pdf.split(".")[0].strip()

        registros.append([
            portaria,
            matricula,
            tipo,
            data,
            assunto
        ])

        time.sleep(1)

    with open("portarias_garulhos.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["Portaria", "Matricula", "Tipo", "Data", "Assunto"])
        writer.writerows(registros)

if __name__ == "__main__":
    main()
