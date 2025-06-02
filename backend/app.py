from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

app = Flask(__name__)
CORS(app)

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.json
    query = data.get('query', '')
    min_price = data.get('minPrice', '')
    max_price = data.get('maxPrice', '')
    days = data.get('daysSinceListed', '')

    url = f"https://www.facebook.com/marketplace/104032612966151/search?minPrice={min_price}&maxPrice={max_price}&daysSinceListed={days}&query={query}&exact=false"

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument("--log-level=3")
    driver = webdriver.Chrome(options=options)

    driver.get(url)
    time.sleep(10)  # espera carregar a página

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()

    anuncios = []
    for div in soup.find_all("div", {"role": "article"}):
        texto = div.get_text()
        link_tag = div.find("a", href=True)
        link = "https://www.facebook.com" + link_tag["href"] if link_tag else "#"
        if query.lower() in texto.lower():
            anuncios.append({
                "titulo": texto[:100],
                "preco": "Ver no site",
                "link": link
            })

    return jsonify({"resultados": anuncios})
