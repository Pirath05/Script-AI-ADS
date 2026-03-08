
import re
import pytest
from playwright.sync_api import sync_playwright, expect


def test_airport_paris_orly_navigation():
    """
    Teste le parcours complet :
    1. Accès à la page d'accueil
    2. Acceptation des cookies (popup Didomi)
    3. Défilement jusqu'en bas de la page
    4. Clic sur le lien "Aéroports"
    5. Clic sur le lien "Aéroport Paris Orly"
    6. Vérification de la navigation vers la page de l'aéroport
    """

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.set_default_timeout(10_000)

        # ----------------------------------------------------------
        # ÉTAPE 1 : Navigation vers la page d'accueil
        # ----------------------------------------------------------
        page.goto("https://www.bonjour-ratp.fr/")
        expect(page).to_have_url(re.compile(r"bonjour-ratp\.fr"))

        # ----------------------------------------------------------
        # ÉTAPE 2 : Acceptation des cookies (popup Didomi)
        # ----------------------------------------------------------
        page.locator("#didomi-popup").wait_for(state="visible")

        page.locator(
            "#didomi-popup button",
            has_text=re.compile("accepter", re.I),
        ).click()

        page.locator("#didomi-popup").wait_for(state="hidden")

        # ----------------------------------------------------------
        # ÉTAPE 3 : Défilement jusqu'en bas de la page
        # ----------------------------------------------------------
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1_000)

        # ----------------------------------------------------------
        # ÉTAPE 4 : Clic sur le lien "Aéroports"
        # ----------------------------------------------------------
        airports_link = page.locator('a[href="#plus"]', has_text="Aéroports")

        if not airports_link.is_visible():
            airports_link = page.locator("a.a1oylayc[href='#plus']")

        airports_link.scroll_into_view_if_needed()
        airports_link.click()
        page.wait_for_timeout(1_000)

        # ----------------------------------------------------------
        # ÉTAPE 5 : Clic sur le lien "Aéroport Paris Orly"
        # ----------------------------------------------------------
        orly_span = page.locator(
            "span.l1vm0fus.lvv0exu",
            has_text="Aéroport Paris Orly",
        )

        orly_link = orly_span.locator("xpath=ancestor::a[1]")

        if not orly_span.is_visible():
            orly_link = page.locator("text=Aéroport Paris Orly")

        orly_link.scroll_into_view_if_needed()
        orly_link.click()

        # ----------------------------------------------------------
        # ÉTAPE 6 : Vérification de la navigation
        # ----------------------------------------------------------
        page.wait_for_load_state("networkidle")

        expect(page).to_have_url(re.compile(r"orly", re.I))
        expect(page).to_have_title(re.compile(r"orly", re.I))

        browser.close()
