from playwright.sync_api import sync_playwright
import re
import pandas as pd
from datetime import datetime

# --- Dicionário de destinos e URLs ---
destinos = {
    "São Paulo": "https://www.google.com/travel/flights/search?tfs=CBwQAhoeEgoyMDI2LTA1LTA0agcIARIDQ05GcgcIARIDR1JVGh4SCjIwMjYtMDUtMDVqBwgBEgNHUlVyBwgBEgNDTkZAAUgBcAGCAQsI____________AZgBAQ&tfu=EgoIAhAAGAAgAigB",
    "Rio de Janeiro": "https://www.google.com/travel/flights/search?tfs=CBwQAhoeEgoyMDI2LTA1LTA0agcIARIDQ05GcgcIARIDR0lHGh4SCjIwMjYtMDUtMDVqBwgBEgNHSUdyBwgBEgNDTkZAAUgBcAGCAQsI____________AZgBAQ&tfu=EgoIAhAAGAAgAigB",
    "Buenos Aires": "https://www.google.com/travel/flights/search?tfs=CBwQAhokEgoyMDI2LTA1LTA0agcIARIDQ05Gcg0IAxIJL20vMDFseTVtGiQSCjIwMjYtMDUtMDVqDQgDEgkvbS8wMWx5NW1yBwgBEgNDTkZAAUgBcAGCAQsI____________AZgBAQ&tfu=EgoIAhAAGAAgAigB",
    "Miami": "https://www.google.com/travel/flights/search?tfs=CBwQAhoeEgoyMDI2LTA1LTA0agcIARIDQ05GcgcIARIDTUlBGh4SCjIwMjYtMDUtMDVqBwgBEgNNSUFyBwgBEgNDTkZAAUgBcAGCAQsI____________AZgBAQ&tfu=EgoIAhAAGAAgAigB",
    "Paris": "https://www.google.com/travel/flights/search?tfs=CBwQAhoeEgoyMDI2LTA1LTA0agcIARIDQ05GcgcIARIDQ0RHGh4SCjIwMjYtMDUtMDVqBwgBEgNDREdyBwgBEgNDTkZAAUgBcAGCAQsI____________AZgBAQ&tfu=EgoIAhAAGAAgAigB"
}

# --- Mapeamento dos aeroportos para cidades ---
map_cidades = {
    "CNF": "Belo Horizonte",
    "GRU": "São Paulo",
    "GIG": "Rio de Janeiro",
    "EZE": "Buenos Aires",
    "MIA": "Miami",
    "CDG": "Paris"
}

# Aeroporto de origem fixo
aeroporto_origem = "CNF"
cidade_origem = map_cidades[aeroporto_origem]

# Lista para armazenar resultados
resultados = []

# --- Função para rodar o scraper e retornar o menor preço ---
def rodar_scraper(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_timeout(10000)  # espera carregar

        try:
            # Clica no botão de ordenação
            page.click('button[aria-label^="Ordenados por"]')
            page.wait_for_timeout(2000)

            # Seleciona a opção "Preço"
            page.click('li[aria-checked="true"] >> text=Preço')
            page.wait_for_timeout(5000)

            # Extrai todo o texto
            texto = page.inner_text("body")
            precos = re.findall(r'R\$\s?([\d\.]+)', texto)
            precos = [int(p.replace(".", "")) for p in precos]

            if precos:
                return min(precos)
            else:
                return None
        except Exception as e:
            print("Erro ao ordenar por preço:", e)
            return None
        finally:
            browser.close()

# --- Loop para cada destino ---
for cidade_destino, url in destinos.items():
    menor_preco = rodar_scraper(url)
    aeroporto_destino = list(map_cidades.keys())[list(map_cidades.values()).index(cidade_destino)] \
        if cidade_destino in map_cidades.values() else cidade_destino[:3].upper()

    resultados.append({
        "coleta": datetime.now().strftime("%Y-%m-%d"),
        "hora": datetime.now().strftime("%H:%M"),
        "aeroporto_origem": aeroporto_origem,
        "cidade_origem": cidade_origem,
        "aeroporto_destino": aeroporto_destino,
        "cidade_destino": cidade_destino,
        "preço": menor_preco
    })

# --- Cria o DataFrame final ---
df = pd.DataFrame(resultados)
print(df)