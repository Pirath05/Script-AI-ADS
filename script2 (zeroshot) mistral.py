import re
import pytest
from playwright.sync_api import sync_playwright

def test_aeroport_paris_orly_navigation():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Naviguer vers la page d'accueil
        page.goto("https://www.bonjour-ratp.fr/")

        # Accepter les cookies
        page.click("#didomi-popup")
        page.click("button", has_text=re.compile("accepter", re.I))

        # Défilement jusqu'en bas de la page
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

        # Cliquer sur le lien "Aéroports"
        page.click('a[href="#plus"]', has_text="Aéroports")

        # Cliquer sur le lien "Aéroport Paris Orly"
        page.click('a.a1oylayc[href="#plus"]')
        page.click('span.l1vm0fus.lvv0exu >> text=Aéroport Paris Orly')

        # Vérifier la navigation vers la page de l'aéroport
        expected_url = "https://www.bonjour-ratp.fr/aeroport-paris-orly"
        assert page.url == expected_url

        browser.close()

# Exécuter le test avec pytest
if __name__ == "__main__":
    pytest.main([__file__])
