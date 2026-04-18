import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

session = requests.Session()
session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Referer": "https://q.mots-croises-solutions.com/",
})

def defToUrl(definition: str) -> str:
    return quote_plus(definition.strip().lower())

def findListWord(definition, taille):
    session.get("https://q.mots-croises-solutions.com/", timeout=10)

    def_url = defToUrl(definition)
    url = f"https://q.mots-croises-solutions.com/croises/{taille}/{def_url}/"

    r = session.get(url, timeout=10)
    r.raise_for_status()
    r.encoding = "utf-8"

    soup = BeautifulSoup(r.text, "html.parser")
    resultats = []

    for tr in soup.select("tr"):
        tds = tr.find_all("td")
        if len(tds) >= 2:
            mot = tds[0].get_text(strip=True)
            longueur = tds[1].get_text(strip=True)
            if mot and longueur.isdigit() and int(longueur) == taille:
                mot = mot.upper()
                if mot not in resultats:
                    resultats.append(mot)

    return resultats

print(findListWord('Bonnes à changer', 6))