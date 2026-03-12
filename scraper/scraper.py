from playwright.sync_api import sync_playwright
import re
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

SUPABASE_URL = "https://zceaqvoiiegksktegiik.supabase.co"
SUPABASE_KEY = "sb_secret_5ctv6B9ENNxX7-wGGxOm7Q_Lv7IAnyv"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

destinos = {
    "São Paulo": "https://www.google.com/travel/flights/search?tfs=CBwQAhoeEgoyMDI2LTA1LTA0agcIARIDQ05GcgcIARIDR1JVGh4SCjIwMjYtMDUtMDVqBwgBEgNHUlVyBwgBEgNDTkZAAUgBcAGCAQsI____________AZgBAQ&tfu=EgoIAhAAGAAgAigB",
    "Rio de Janeiro": "https://www.google.com/travel/flights/search?tfs=CBwQAhoeEgoyMDI2LTA1LTA0agcIARIDQ05GcgcIARIDR0lHGh4SCjIwMjYtMDUtMDVqBwgBEgNHSUdyBwgBEgNDTkZAAUgBcAGCAQsI____________AZgBAQ&tfu=EgoIAhAAGAAgAigB",
    "Buenos Aires": "https://www.google.com/travel/flights/search?tfs=CBwQAhokEgoyMDI2LTA1LTA0agcIARIDQ05Gcg0IAxIJL20vMDFseTVtGiQSCjIwMjYtMDUtMDVqDQgDEgkvbS8wMWx5NW1yBwgBEgNDTkZAAUgBcAGCAQsI____________AZgBAQ&tfu=EgoIAhAAGAAgAigB",
    "Miami": "https://www.google.com/travel/flights/search?tfs=CBwQAhoeEgoyMDI2LTA1LTA0agcIARIDQ05GcgcIARIDTUlBGh4SCjIwMjYtMDUtMDVqBwgBEgNNSUFyBwgBEgNDTkZAAUgBcAGCAQsI____________AZgBAQ&tfu=EgoIAhAAGAAgAigB",
    "Paris": "https://www.google.com/travel/flights/search?tfs=CBwQAhoeEgoyMDI2LTA1LTA0agcIARIDQ05GcgcIARIDQ0RHGh4SCjIwMjYtMDUtMDVqBwgBEgNDREdyBwgBEgNDTkZAAUgBcAGCAQsI____________AZgBAQ&tfu=EgoIAhAAGAAgAigB"
}

map_cidades = {
    "CNF": "Belo Horizonte",
    "GRU": "São Paulo",
    "GIG": "Rio de Janeiro",
    "EZE": "Buenos Aires",
    "MIA": "Miami",
    "CDG": "Paris"
}

aeroporto_origem = "CNF"
cidade_origem = map_cidades[aeroporto_origem]
data_ida = "2026-05-04"
data_volta = "2026-05-05"
resultados = []

def rodar_scraper(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        # Simula navegador real em português do Brasil
        context = browser.new_context(
            locale="pt-BR",
            timezone_id="America/Sao_Paulo",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            page.goto(url, timeout=60000, wait_until="networkidle")
            page.wait_for_timeout(3000)

            # Tenta seletor em português e inglês
            seletor = 'button[aria-label^="Ordenados por"], button[aria-label^="Sort by"]'
            page.wait_for_selector(seletor, timeout=60000)
            page.click(seletor)
            page.wait_for_timeout(2000)

            # Clica em "Preço" ou "Price"
            try:
                page.click('li >> text=Preço')
            except:
                page.click('li >> text=Price')
            page.wait_for_timeout(5000)

            texto = page.inner_text("body")
            precos = re.findall(r'R\$\s?([\d\.]+)', texto)
            precos = [int(p.replace(".", "")) for p in precos if len(p) >= 3]

            if precos:
                return min(precos)
            else:
                return None

        except Exception as e:
            print("Erro ao coletar preço:", e)
            return None
        finally:
            browser.close()

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
        "preco": menor_preco,  # sem acento para evitar problemas
        "data_ida": data_ida,
        "data_volta": data_volta
    })

df = pd.DataFrame(resultados)
print(df)

for _, row in df.iterrows():
    # Corrige o NaN → None antes de inserir
    preco_valor = None if pd.isna(row["preco"]) else int(row["preco"])

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

print("Dados enviados para o Supabase.")