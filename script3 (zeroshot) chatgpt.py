import re
import pytest
from playwright.sync_api import sync_playwright, expect


@pytest.mark.e2e
def test_footer_links_bonjour_ratp():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Étape 1 : Accéder au site
        page.goto("https://www.bonjour-ratp.fr/", timeout=60000)

        # Étape 2 : Accepter les cookies
        if page.locator("#didomi-popup").is_visible():
            page.locator(
                "button",
                has_text=re.compile("accepter", re.I)
            ).click()

        # Étape 3 : Défiler jusqu'au footer
        footer = page.locator("footer")
        footer.scroll_into_view_if_needed()
        footer.wait_for()

        # Étape 4 : Cliquer sur "Violences sexistes ou sexuelles"
        page.locator(
            "a.l185tp5q",
            has_text="Violences sexistes ou sexuelles"
        ).click()

        # Étape 5 : Vérifier la navigation vers la page de contact
        expect(page).to_have_url(re.compile("contact|violences", re.I))

        # Étape 6 : Retour à la page précédente
        page.go_back()

        # S'assurer que le footer est à nouveau visible
        footer.scroll_into_view_if_needed()

        # Étape 7 : Cliquer sur "Mentions légales"
        page.locator(
            "a",
            has_text="Mentions légales"
        ).click()

        # Étape 8 : Vérifier la page des mentions légales
        expect(
            page.locator(
                "h1, h2",
                has_text="Mentions légales"
            )
        ).to_be_visible()

        browser.close()
