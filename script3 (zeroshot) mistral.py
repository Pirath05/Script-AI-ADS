import re
import pytest
from playwright.sync_api import sync_playwright

@pytest.fixture(scope="module")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {
            "width": 1920,
            "height": 1080,
        },
        "ignore_https_errors": True,
    }

def test_liens_footer():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Accéder à l'URL
        page.goto("https://www.bonjour-ratp.fr")

        # Accepter les cookies
        page.click("#didomi-popup button", has_text=re.compile("accepter", re.I))

        # Défiler jusqu'en bas de la page
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

        # Cliquer sur le lien "Violences sexistes ou sexuelles"
        page.click("footer a.l185tp5q", has_text="Violences sexistes ou sexuelles")

        # Vérifier la navigation vers la page de contact
        page.wait_for_selector("h1, h2", has_text="Mentions légales")

        # Retourner à la page précédente
        page.go_back()

        # Cliquer sur le lien "Mentions légales"
        page.click("footer a", has_text="Mentions légales")

        # Vérifier la navigation vers la page des mentions légales
        page.wait_for_selector("h1, h2", has_text="Mentions légales")

        # Fermer le navigateur
        browser.close()

# Exécuter les tests
if __name__ == "__main__":
    pytest.main([__file__])
