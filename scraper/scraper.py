from playwright.sync_api import sync_playwright


def test_browser():

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=False)

        page = browser.new_page()

        page.goto("https://www.google.com")

        print(page.title())

        browser.close()


if __name__ == "__main__":
    test_browser()