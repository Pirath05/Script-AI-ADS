import re
import pytest
from playwright.sync_api import sync_playwright, TimeoutError

# ─────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────

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

# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def accept_cookies(page):
    try:
        page.wait_for_selector("#didomi-popup", timeout=5000)
        page.locator('button', has_text=re.compile("accepter", re.I)).first.click()
        page.wait_for_selector("#didomi-popup", state="detached", timeout=10000)
        print("Cookies acceptés.")
    except TimeoutError:
        pass

def scroll_to_bottom(page):
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(2000)

def get_footer(page):
    footer = page.locator("footer")
    footer.wait_for(state="visible", timeout=10000)
    return footer

# ─────────────────────────────────────────
# TEST
# ─────────────────────────────────────────

def test_footer_links(page):
    page.goto("https://www.bonjour-ratp.fr/")

    # 1. Cookies
    accept_cookies(page)

    # 2. Scroll bas pour déclencher le lazy loading
    scroll_to_bottom(page)
    page.wait_for_load_state("load")

    # 3. Vérifier le footer
    footer = get_footer(page)
    assert footer.is_visible(), "Footer non visible"

    # 4. Lien "Violences sexistes ou sexuelles"
    lien_violences = footer.locator("a.l185tp5q", has_text="Violences sexistes ou sexuelles")
    lien_violences.wait_for(state="visible", timeout=5000)
    assert lien_violences.count() > 0, "Lien 'Violences sexistes ou sexuelles' non trouvé."

    with page.expect_navigation():
        lien_violences.click()

    assert page.url == "https://www.bonjour-ratp.fr/aide-contact/?question=je-suis-victime-ou-temoin-d-une-agression", \
        f"URL inattendue : {page.url}"
    print(f"Navigation réussie : {page.url}")

    # 5. Retour + lien "Mentions légales"
    page.go_back()
    page.wait_for_load_state("load")

    footer = get_footer(page)

    lien_mentions = footer.locator("a", has_text="Mentions légales")
    lien_mentions.wait_for(state="visible", timeout=10000)
    assert lien_mentions.count() > 0, "Lien 'Mentions légales' non trouvé."

    lien_mentions.click()
    page.wait_for_url("**/informations-legales/#mentions-legales", timeout=10000)
    assert "#mentions-legales" in page.url, f"Fragment #mentions-legales absent : {page.url}"

    titre = page.locator("h1, h2", has_text="Mentions légales")
    titre.wait_for(state="visible", timeout=5000)
    assert titre.is_visible(), "Titre 'Mentions légales' non visible."

    print(f"Navigation réussie : {page.url}")
    print("Toutes les étapes sont bonnes.")
