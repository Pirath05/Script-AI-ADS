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
# Test Footer
# ─────────────────────────────

def test_footer_links_simple(page):

    # 1️⃣ Ouvrir la page
    page.goto("https://www.bonjour-ratp.fr/")
    page.wait_for_load_state("networkidle")

    # 2️⃣ Cookies
    try:
        page.locator("button", has_text=re.compile("accepter", re.I)).click(timeout=5000)
        print("✅ Cookies acceptés")
    except TimeoutError:
        print("ℹ️ Pas de popup cookies")

    # 3️⃣ Scroll direct en bas de page
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(1500)

    footer = page.locator("footer")
    footer.wait_for(state="visible", timeout=10000)

    # ─────────────────────────
    # Violences sexistes ou sexuelles
    # ─────────────────────────

    lien_violences = footer.locator("a", has_text="Violences sexistes ou sexuelles")
    lien_violences.wait_for(state="visible", timeout=5000)

    with page.expect_navigation():
        lien_violences.first.click()

    assert "je-suis-victime-ou-temoin-d-une-agression" in page.url
    print("✅ Lien 'Violences sexistes ou sexuelles' OK")

    # Retour home
    page.go_back()
    page.wait_for_load_state("networkidle")

    # ─────────────────────────
    # Mentions légales
    # ─────────────────────────

    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(1000)

    lien_mentions = page.locator("footer a", has_text="Mentions légales")
    lien_mentions.wait_for(state="visible", timeout=5000)

    lien_mentions.first.click()
    page.wait_for_url("**/informations-legales/**")

    assert "mentions-legales" in page.url
    page.locator("h1, h2", has_text="Mentions légales").wait_for(state="visible")

    print("✅ Lien 'Mentions légales' OK")

    print("🎉 Test footer terminé avec succès")
