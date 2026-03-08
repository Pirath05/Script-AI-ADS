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

def test_parcours_planification_itineraire():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Accéder à l'URL
        page.goto("https://www.bonjour-ratp.fr")

        # Accepter les cookies
        page.click("#didomi-popup button", has_text=re.compile("accepter", re.I))

        # Remplir les champs de départ et d'arrivée
        page.fill("input#departure", "Gare de Lyon")
        page.click("#departure-suggestions li")
        page.fill("input#arrival", "Château de Vincennes")
        page.click("#arrival-suggestions li")

        # Effectuer une double inversion des champs
        page.click("button[aria-label='Inverser départ et arrivée']")
        page.click("button[aria-label='Inverser départ et arrivée']")

        # Vérifier l'affichage de l'itinéraire
        page.click("#main > section.i119okux.bu9trog > div > div.idw1uie > div.i11clvn1 > div:nth-child(2) > div.b12h0ode.i8ngrdz > button")

        # Ouvrir les stations intermédiaires
        page.click("button[aria-controls='stations-list-expanded-content'][aria-expanded='false']")

        # Retourner à la vue principale
        page.click("div.r1ox9p09, button[aria-label='Retour à votre trajet'], span.a1gdnitw")

        # Inverser les champs de départ et d'arrivée
        page.click("button[aria-label='Inverser départ et arrivée']")

        # Appliquer des filtres pour ne garder que le métro
        page.click("button[aria-label='Accéder aux options de filtre']")
        page.click("button:has(span:has-text('Mode de transport'))")

        # Désélectionner tous les modes de transport sauf le métro
        page.click("label[for='RER']")
        page.click("label[for='TRANSILIEN']")
        page.click("label[for='BUS']")
        page.click("label[for='TRAM']")
        page.click("label[for='CABLE']")
        page.click("label[for='SELF_SERVICE_VEHICLE']")
        page.click("label[for='BICYCLE']")

        # Valider les filtres
        page.click("button, has_text=re.compile('Voir les résultats', re.I), button[type='submit']")

        # Fermer le navigateur
        browser.close()

# Exécuter les tests
if __name__ == "__main__":
    pytest.main([__file__])
