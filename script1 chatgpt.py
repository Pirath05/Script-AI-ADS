import re
import pytest
from playwright.sync_api import sync_playwright, TimeoutError

# ─────────────────────────────
# Fixtures Playwright
# ─────────────────────────────

@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        yield browser
        browser.close()

@pytest.fixture
def page(browser):
    page = browser.new_page()
    yield page
    page.close()

# ─────────────────────────────
# Test principal
# ─────────────────────────────

def test_itineraire_simple(page):

    # 1️⃣ Ouvrir le site
    page.goto("https://www.bonjour-ratp.fr/")

    # 2️⃣ Cookies (si présents)
    try:
        page.locator("button", has_text=re.compile("accepter", re.I)).click(timeout=5000)
        print("✅ Cookies acceptés")
    except TimeoutError:
        print("ℹ️ Pas de popup cookies")

    # 3️⃣ Remplir départ
    page.fill("#departure", "République")
    page.locator("#departure-suggestions li").first.click()
    print("✅ Départ sélectionné")

    # 4️⃣ Remplir arrivée
    page.fill("#arrival", "Gare de Lyon")
    page.locator("#arrival-suggestions li").first.click()
    print("✅ Arrivée sélectionnée")

    # 5️⃣ Cliquer sur le premier itinéraire proposé
    try:
        page.locator("button:has-text('Voir')").first.click(timeout=15000)
        print("✅ Itinéraire ouvert")
    except TimeoutError:
        assert False, "❌ Aucun itinéraire trouvé"

    # 6️⃣ Ouvrir les filtres
    page.locator('button[aria-label="Accéder aux options de filtre"]').click()
    print("✅ Filtres ouverts")

    # 7️⃣ Mode de transport
    page.locator("button:has-text('Mode de transport')").click()
    print("✅ Mode de transport ouvert")

    # 8️⃣ Désactiver tout sauf METRO
    transports = ["RER", "BUS", "TRAM", "CABLE", "BICYCLE", "SELF_SERVICE_VEHICLE"]

    for t in transports:
        checkbox = page.locator(f"input#{t}")
        if checkbox.count() and checkbox.is_checked():
            page.locator(f"label[for='{t}']").click()
            print(f"⛔ {t} désactivé")

    print("✅ Métro uniquement conservé")

    # 9️⃣ Valider les filtres
    page.locator("button", has_text=re.compile("résultats|valider", re.I)).click()
    print("✅ Filtres validés")

    # 🔟 Capture écran
    page.wait_for_timeout(3000)
    page.screenshot(path="itineraire_simple.png", full_page=True)
    print("📸 Capture enregistrée")

    print("🎉 Test terminé avec succès")
