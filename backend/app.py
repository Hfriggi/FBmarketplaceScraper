import json
import time
import os
import pathlib
from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Caminho do .env e do arquivo de cookies
env_path = pathlib.Path(__file__).parent.parent / '.env'
cookies_file = "facebook_cookies.json"

# Carrega variáveis
load_dotenv(dotenv_path=env_path)
FB_EMAIL = os.getenv("FB_EMAIL")
FB_PASSWORD = os.getenv("FB_PASSWORD")

app = Flask(__name__)
CORS(app)

def save_cookies(driver, path):
    with open(path, 'w') as file:
        json.dump(driver.get_cookies(), file)

def load_cookies(driver, path):
    with open(path, 'r') as file:
        cookies = json.load(file)
        for cookie in cookies:
            if "sameSite" in cookie and cookie["sameSite"] == "None":
                cookie["sameSite"] = "Strict"
            driver.add_cookie(cookie)

def is_logged_in(driver):
    return "login" not in driver.current_url and "checkpoint" not in driver.current_url

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.json
    query = data.get('query', '')
    min_price = data.get('minPrice', '')
    max_price = data.get('maxPrice', '')
    days = data.get('daysSinceListed', '1')
    radius = data.get('radius', '20')  # valor padrão 20km

    # Monta a URL apenas com os filtros necessários
    url = "https://www.facebook.com/marketplace/104032612966151/search?"
    params = []
    if min_price and min_price != 'gratuito':
        params.append(f"minPrice={min_price}")
    if max_price:
        params.append(f"maxPrice={max_price}")
    params.append(f"daysSinceListed={days}")
    params.append(f"query={query}")
    params.append("exact=false")
    url += "&".join(params)

    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    print("Iniciando navegador...")
    driver = webdriver.Chrome(options=options)

    try:
        # Ir direto para a página de login
        print("Acessando página de login do Facebook...")
        driver.get("https://www.facebook.com/login")
        time.sleep(3)

        # Verifica se há cookies salvos
        if os.path.exists(cookies_file):
            print("Carregando cookies salvos...")
            driver.delete_all_cookies()
            load_cookies(driver, cookies_file)
            driver.get("https://www.facebook.com")
            time.sleep(5)

        # Se ainda não estiver logado, preenche login e espera CAPTCHA manual
        if not is_logged_in(driver):
            print("Preenchendo login...")
            try:
                email_input = driver.find_element(By.ID, "email")
                pass_input = driver.find_element(By.ID, "pass")
                email_input.clear()
                pass_input.clear()
                email_input.send_keys(FB_EMAIL)
                pass_input.send_keys(FB_PASSWORD)
                pass_input.submit()
                print("⚠️ CAPTCHA ou verificação pode ser necessária agora.")
            except Exception as e:
                print("Erro ao localizar campos de login:", e)
            
            input("🛑 Após resolver CAPTCHA e estar logado, pressione ENTER aqui no terminal...")

            if not is_logged_in(driver):
                print("⚠️ Login não concluído.")
                driver.quit()
                return jsonify({"erro": "Login não concluído. Verifique o CAPTCHA ou as credenciais."}), 401

            print("✅ Login bem-sucedido! Salvando cookies...")
            save_cookies(driver, cookies_file)

        # Acessa o Marketplace
        print("Acessando Marketplace...")
        driver.get(url)
        time.sleep(5)

        # Seleciona localização e raio
        print("Abrindo filtro de localização...")
        try:
            # Clica no botão de localização
            location_button = driver.find_element(By.XPATH, "//span[contains(text(),'Localização')]/ancestor::div[@role='button']")
            location_button.click()
            time.sleep(2)

            # Preenche o campo de localização com "Indaial"
            location_input = driver.find_element(By.XPATH, "//input[@placeholder='Pesquise por cidade, bairro ou código postal.']")
            location_input.clear()
            location_input.send_keys("Indaial")
            time.sleep(2)
            location_input.send_keys(u'\ue007')  # Pressiona Enter
            time.sleep(2)

            # Seleciona o raio desejado
            print(f"Selecionando raio: {radius} km")
            radius_dropdown = driver.find_element(By.XPATH, "//select[contains(@aria-label, 'Raio')]")
            radius_dropdown.click()
            time.sleep(1)
            from selenium.webdriver.support.ui import Select
            select = Select(radius_dropdown)
            select.select_by_visible_text(f"{radius} quilômetro" if radius == "1" else f"{radius} quilômetros")
            time.sleep(1)

            # Clica no botão "Aplicar"
            apply_button = driver.find_element(By.XPATH, "//div[@aria-label='Aplicar']")
            apply_button.click()
            time.sleep(5)
        except Exception as e:
            print(f"Erro ao selecionar localização/raio: {e}")

        # Role a página para baixo para carregar mais anúncios (agora 10 vezes)
        for _ in range(10):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

        anuncios = []
        print("Coletando anúncios com Selenium...")

        # Espera o carregamento completo dos elementos (até 20s)
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import TimeoutException

        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, '//a[contains(@href, "/marketplace/item/")]'))
            )
        except TimeoutException:
            print("⚠️ Timeout: Anúncios não carregaram.")
            driver.quit()
            return jsonify({"resultados": []})

        cards = driver.find_elements(By.XPATH, '//a[contains(@href, "/marketplace/item/")]')

        for card in cards:
            try:
                link = card.get_attribute("href")
                texto = card.text.split("\n")

                # Corrigido: titulo e preco
                preco = texto[0] if len(texto) > 0 else "Sem preço"
                titulo = texto[1] if len(texto) > 1 else "Sem título"
                local = texto[2] if len(texto) > 2 else "Localização não informada"

                # Tenta pegar imagem de fundo (estilo background-image)
                imagem = ""
                try:
                    img_container = card.find_element(By.XPATH, './/img')
                    imagem = img_container.get_attribute("src")
                except Exception as e:
                    print("Imagem não encontrada:", e)

                anuncios.append({
                    "titulo": titulo,
                    "preco": preco,
                    "link": link,
                    "imagem": imagem,
                    "localizacao": local
                })

            except Exception as e:
                print(f"Erro ao extrair dados de um anúncio: {e}")
                continue

        driver.quit()

        return jsonify({"resultados": anuncios})

    except Exception as e:
        print(f"Erro: {e}")
        driver.quit()
        return jsonify({"erro": "Erro inesperado ao acessar o Facebook ou Marketplace."}), 500

if __name__ == "__main__":
    app.run(debug=True)
