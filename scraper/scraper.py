from playwright.sync_api import sync_playwright
import re
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# -----------------------------
# Credenciais Supabase
# -----------------------------
SUPABASE_URL = "https://zceaqvoiiegksktegiik.supabase.co"
SUPABASE_KEY = "sb_secret_5ctv6B9ENNxX7-wGGxOm7Q_Lv7IAnyv"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------
# Dicionário de destinos e URLs
# -----------------------------
destinos = {
    "São Paulo": "https://www.google.com/travel/flights/search?tfs=CBwQAhoeEgoyMDI2LTA1LTA0agcIARIDQ05GcgcIARIDR1JVGh4SCjIwMjYtMDUtMDVqBwgBEgNHUlVyBwgBEgNDTkZAAUgBcAGCAQsI____________AZgBAQ&tfu=EgoIAhAAGAAgAigB",
    "Rio de Janeiro": "https://www.google.com/travel/flights/search?tfs=CBwQAhoeEgoyMDI2LTA1LTA0agcIARIDQ05GcgcIARIDR0lHGh4SCjIwMjYtMDUtMDVqBwgBEgNHSUdyBwgBEgNDTkZAAUgBcAGCAQsI____________AZgBAQ&tfu=EgoIAhAAGAAgAigB",
    "Buenos Aires": "https://www.google.com/travel/flights/search?tfs=CBwQAhokEgoyMDI2LTA1LTA0agcIARIDQ05Gcg0IAxIJL20vMDFseTVtGiQSCjIwMjYtMDUtMDVqDQgDEgkvbS8wMWx5NW1yBwgBEgNDTkZAAUgBcAGCAQsI____________AZgBAQ&tfu=EgoIAhAAGAAgAigB",
    "Miami": "https://www.google.com/travel/flights/search?tfs=CBwQAhoeEgoyMDI2LTA1LTA0agcIARIDQ05GcgcIARIDTUlBGh4SCjIwMjYtMDUtMDVqBwgBEgNNSUFyBwgBEgNDTkZAAUgBcAGCAQsI____________AZgBAQ&tfu=EgoIAhAAGAAgAigB",
    "Paris": "https://www.google.com/travel/flights/search?tfs=CBwQAhoeEgoyMDI2LTA1LTA0agcIARIDQ05GcgcIARIDQ0RHGh4SCjIwMjYtMDUtMDVqBwgBEgNDREdyBwgBEgNDTkZAAUgBcAGCAQsI____________AZgBAQ&tfu=EgoIAhAAGAAgAigB"
}

# -----------------------------
# Mapeamento aeroportos -> cidades
# -----------------------------
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

resultados = []

# -----------------------------
# Datas de ida e volta fixas
# -----------------------------
data_ida = "2026-05-04"
data_volta = "2026-05-05"

# -----------------------------
# Função scraper
# -----------------------------
def rodar_scraper(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,  # OBRIGATÓRIO no GitHub Actions
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        page = browser.new_page()

        try:
            page.goto(url, timeout=60000)
            page.wait_for_selector('button[aria-label^="Ordenados por"]', timeout=60000)
            page.click('button[aria-label^="Ordenados por"]')
            page.wait_for_timeout(2000)

            page.click('li[aria-checked="true"] >> text=Preço')
            page.wait_for_timeout(5000)

            texto = page.inner_text("body")
            precos = re.findall(r'R\$\s?([\d\.]+)', texto)
            precos = [int(p.replace(".", "")) for p in precos]

            if precos:
                return min(precos)
            else:
                return None

        except Exception as e:
            print("Erro ao coletar preço:", e)
            return None
        finally:
            browser.close()

# -----------------------------
# Loop destinos
# -----------------------------
for cidade_destino, url in destinos.items():
    print("Coletando:", cidade_destino)
    menor_preco = rodar_scraper(url)

    if menor_preco is None:
        print(f"Atenção: não foi encontrado preço para {cidade_destino}")

    aeroporto_destino = list(map_cidades.keys())[list(map_cidades.values()).index(cidade_destino)]

    resultados.append({
        "coleta": datetime.now().strftime("%Y-%m-%d"),
        "hora": datetime.now().strftime("%H:%M"),
        "aeroporto_origem": aeroporto_origem,
        "cidade_origem": cidade_origem,
        "aeroporto_destino": aeroporto_destino,
        "cidade_destino": cidade_destino,
        "preço": menor_preco,
        "data_ida": data_ida,
        "data_volta": data_volta
    })

# -----------------------------
# Criar DataFrame
# -----------------------------
df = pd.DataFrame(resultados)
print(df)

# -----------------------------
# Inserir no Supabase
# -----------------------------
for _, row in df.iterrows():
    preco_valor = int(row["preço"]) if row["preço"] is not None else None

    supabase.table("voos").insert({
        "coleta": row["coleta"],
        "hora": row["hora"],
        "aeroporto_origem": row["aeroporto_origem"],
        "cidade_origem": row["cidade_origem"],
        "aeroporto_destino": row["aeroporto_destino"],
        "cidade_destino": row["cidade_destino"],
        "preco": preco_valor,
        "data_ida": row["data_ida"],
        "data_volta": row["data_volta"]
    }).execute()

print("Dados enviados para o Supabase com datas de ida e volta.")