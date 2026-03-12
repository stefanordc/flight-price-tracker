from playwright.sync_api import sync_playwright
import re

url = "https://www.google.com/travel/flights/search?tfs=CBwQAhoeEgoyMDI2LTA1LTA0agcIARIDQ05GcgcIARIDR1JVGh4SCjIwMjYtMDUtMDVqBwgBEgNHUlVyBwgBEgNDTkZAAUgBcAGCAQsI____________AZgBAQ&tfu=EgoIAhAAGAAgAigB"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(url)

    # Espera a página carregar
    page.wait_for_timeout(10000)

    try:
        # 1️⃣ Clica no botão de ordenação
        page.click('button[aria-label^="Ordenados por"]')
        page.wait_for_timeout(2000)  # espera o menu abrir

        # 2️⃣ Seleciona a opção "Preço"
        page.click('li[aria-checked="true"] >> text=Preço')
        page.wait_for_timeout(5000)  # espera a lista atualizar

        # 3️⃣ Extrai todo o texto e busca preços
        texto = page.inner_text("body")
        precos = re.findall(r'R\$\s?([\d\.]+)', texto)
        precos = [int(p.replace(".", "")) for p in precos]

        if precos:
            menor_preco = min(precos)
            print("Menor preço encontrado:", menor_preco)
        else:
            print("Não encontrou preços.")

    except Exception as e:
        print("Erro ao ordenar por preço:", e)

    browser.close()