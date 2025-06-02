print("Iniciando o servidor Flask...")

from flask import Flask, request, jsonify, abort
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import time
import os
from dotenv import load_dotenv
import pathlib

# Carrega variáveis do .env na raiz do projeto
env_path = pathlib.Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

FB_EMAIL = os.getenv("FB_EMAIL")
FB_PASSWORD = os.getenv("FB_PASSWORD")

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
    # Remova o modo headless para depuração visual
    # options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument("--log-level=3")
    options.add_argument("--window-size=1920,1080")
    print("Iniciando o navegador Chrome...")
    driver = webdriver.Chrome(options=options)

    try:
        # Login no Facebook
        print("Acessando a página de login do Facebook...")
        driver.get("https://www.facebook.com/login")
        time.sleep(2)
        print("Preenchendo o e-mail...")
        email_input = driver.find_element(By.ID, "email")
        print("Preenchendo a senha...")
        pass_input = driver.find_element(By.ID, "pass")
        email_input.send_keys(FB_EMAIL)
        pass_input.send_keys(FB_PASSWORD)
        print("Enviando formulário de login...")
        pass_input.send_keys(Keys.RETURN)
        time.sleep(5)  # Aguarda login

        # Verifica se o login falhou
        if "login" in driver.current_url or "checkpoint" in driver.current_url:
            print("Erro: Falha no login do Facebook. Verifique suas credenciais.")
            driver.quit()
            return jsonify({"erro": "Falha no login do Facebook. Verifique suas credenciais."}), 401

        print("Login realizado, acessando o Marketplace...")

        # Vai para o Marketplace
        driver.get(url)
        print("Aguardando carregamento da página do Marketplace...")
        time.sleep(5)  # espera carregar a página

        # Role a página para baixo para carregar mais anúncios
        print("Rolando a página para carregar mais anúncios...")
        for i in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

        print("Realizando scraping dos anúncios...")
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

    except Exception as e:
        print(f"Erro inesperado: {e}")
        driver.quit()
        return jsonify({"erro": "Erro inesperado ao tentar logar ou acessar o Facebook."}), 500


if __name__ == "__main__":
    app.run(debug=True)  # Adicione debug=True
