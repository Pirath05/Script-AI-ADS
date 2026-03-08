import re
import pytest
from playwright.sync_api import sync_playwright, expect


@pytest.mark.e2e
def test_parcours_aeroports_bonjour_ratp():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Étape 1 : Accéder au site
        page.goto("https://www.bonjour-ratp.fr/", timeout=60000)

        # Étape 2 : Accepter les cookies
        cookie_popup = page.locator("#didomi-popup")
        if cookie_popup.is_visible():
            page.locator(
                "button",
                has_text=re.compile("accepter", re.I)
            ).click()

        # Étape 3 : Défiler jusqu'en bas de la page
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1000)

        # Étape 4 : Cliquer sur le lien "Aéroports"
        page.locator(
            'a[href="#plus"]',
            has_text="Aéroports"
        ).click()

        # Sélecteur alternatif fourni
        page.locator('a.a1oylayc[href="#plus"]').wait_for()

        # Étape 5 : Cliquer sur "Aéroport Paris Orly"
        aeroport_orly = page.locator(
            'span.l1vm0fus.lvv0exu >> text=Aéroport Paris Orly'
        )
        aeroport_orly.wait_for()

        aeroport_orly.locator(
            'xpath=ancestor::a[1]'
        ).click()

        # Étape 6 : Vérifier la navigation vers la page de l'aéroport
        expect(page).to_have_url(re.compile("orly", re.I))
        expect(
            page.locator("text=Aéroport Paris Orly")
        ).to_be_visible()

        browser.close()
