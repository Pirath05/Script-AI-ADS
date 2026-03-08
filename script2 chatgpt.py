import pytest
import re
from playwright.sync_api import sync_playwright, TimeoutError

# ─────────────────────────────
# Fixtures
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
# Test Aéroports (simple)
# ─────────────────────────────

def test_aeroports_simple(page):

    # 1️⃣ Ouvrir la page
    page.goto("https://www.bonjour-ratp.fr/aeroports/")
    page.wait_for_load_state("networkidle")

    # 2️⃣ Cookies
    try:
        page.locator("button", has_text=re.compile("accepter", re.I)).click(timeout=5000)
        print("✅ Cookies acceptés")
    except TimeoutError:
        print("ℹ️ Pas de popup cookies")

    # 3️⃣ Scroll pour déclencher le lazy-load
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(800)
    page.evaluate("window.scrollTo(0, 0)")

    # 4️⃣ Cliquer sur l’ancre "Aéroports"
    page.locator('a[href="#plus"]', has_text="Aéroports").first.click()
    print("✅ Section Aéroports ouverte")

    page.wait_for_timeout(800)

    # 5️⃣ Cliquer sur "Aéroport Paris Orly"
    page.locator("text=Aéroport Paris Orly").first.click()
    print("✅ Aéroport Paris Orly cliqué")

    # 6️⃣ Vérification simple
    assert page.locator("text=Aéroport Paris Orly").first.is_visible()
    print("🎉 Scénario Aéroports terminé avec succès")
