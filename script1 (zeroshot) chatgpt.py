import re
import pytest
from playwright.sync_api import sync_playwright, expect


@pytest.mark.e2e
def test_planification_itineraire_metro_uniquement():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Étape 1 : Accès au site
        page.goto("https://www.bonjour-ratp.fr/", timeout=60000)

        # Étape 2 : Acceptation des cookies
        if page.locator("#didomi-popup").is_visible():
            page.locator(
                "button",
                has_text=re.compile("accepter", re.I)
            ).click()

        # Étape 3 : Renseigner le départ
        page.locator("input#departure").fill("Châtelet")
        page.locator("#departure-suggestions li").first.click()

        # Étape 4 : Renseigner l'arrivée
        page.locator("input#arrival").fill("Gare de Lyon")
        page.locator("#arrival-suggestions li").first.click()

        # Étape 5 : Double inversion départ / arrivée
        invert_button = page.locator(
            'button[aria-label="Inverser départ et arrivée"]'
        )
        invert_button.click()
        page.wait_for_timeout(500)
        invert_button.click()

        # Étape 6 : Vérifier l'affichage de l'itinéraire
        page.locator(
            "#main > section.i119okux.bu9trog > div > div.idw1uie > div.i11clvn1 > div:nth-child(2) > div.b12h0ode.i8ngrdz > button"
        ).wait_for()

        # Étape 7 : Ouvrir les stations intermédiaires
        page.locator(
            'button[aria-controls="stations-list-expanded-content"][aria-expanded="false"]'
        ).click()

        # Étape 8 : Retour à la vue principale
        page.locator(
            'button[aria-label="Retour à votre trajet"]'
        ).click()

        # Étape 9 : Nouvelle inversion départ / arrivée
        invert_button.click()

        # Étape 10 : Accéder aux options de filtre
        page.locator(
            'button[aria-label="Accéder aux options de filtre"]'
        ).click()

        page.locator(
            'button:has(span:has-text("Mode de transport"))'
        ).click()

        # Étape 11 : Désactiver tous les modes sauf Métro
        modes_a_desactiver = [
            "RER",
            "TRANSILIEN",
            "BUS",
            "TRAM",
            "CABLE",
            "SELF_SERVICE_VEHICLE",
            "BICYCLE"
        ]

        for mode in modes_a_desactiver:
            checkbox = page.locator(f"input#{mode}")
            if checkbox.is_checked():
                page.locator(f"label[for='{mode}']").click()

        # Vérifier que le métro est bien sélectionné
        if not page.locator("input#METRO").is_checked():
            page.locator("label[for='METRO']").click()

        # Étape 12 : Valider les filtres
        page.locator(
            "button",
            has_text=re.compile("Voir les résultats", re.I)
        ).click()

        # Vérification finale : résultats affichés
        expect(
            page.locator("div.r1ox9p09")
        ).to_be_visible()

        browser.close()
