import re
import pytest
from playwright.sync_api import sync_playwright, TimeoutError

# ─────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────

@pytest.fixture(scope="session")
def browser_context():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        yield context
        context.close()
        browser.close()

@pytest.fixture
def page(browser_context):
    page = browser_context.new_page()
    yield page
    if not page.is_closed():
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
        print("Pas de popup cookies.")

def safe_click(locator, page, timeout=10000):
    """Clic robuste avec scroll + fallbacks."""
    try:
        locator.scroll_into_view_if_needed(timeout=timeout)
    except Exception:
        pass
    try:
        locator.click(timeout=timeout)
        return True
    except Exception:
        try:
            locator.click(force=True, timeout=2000)
            return True
        except Exception:
            return False

def get_clickable(locator):
    """Remonte au premier ancêtre <a> si disponible."""
    try:
        ancestor = locator.locator("xpath=ancestor::a[1]")
        return ancestor.first if ancestor.count() > 0 else locator
    except Exception:
        return locator

# ─────────────────────────────────────────
# TEST
# ─────────────────────────────────────────

def test_aeroports_parcours(page):
    page.goto("https://www.bonjour-ratp.fr/aeroports/", timeout=20000)
    page.wait_for_load_state("networkidle", timeout=15000)

    # 1. Cookies
    accept_cookies(page)

    # 2. Scroll bas → haut pour déclencher le lazy loading
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(800)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(500)

    # 3. Cliquer sur l'ancre "Aéroports" (#plus)
    aero_anchor = page.locator('a[href="#plus"]', has_text="Aéroports").first
    try:
        aero_anchor.wait_for(state="visible", timeout=8000)
    except TimeoutError:
        aero_anchor = page.locator('a.a1oylayc[href="#plus"]').first

    assert safe_click(aero_anchor, page), "Impossible de cliquer sur le lien 'Aéroports'."
    page.wait_for_timeout(800)

    # 4. Cliquer sur "Aéroport Paris Orly"
    orly = page.locator("span.l1vm0fus.lvv0exu >> text=Aéroport Paris Orly").first
    try:
        orly.wait_for(state="visible", timeout=10000)
    except TimeoutError:
        orly = page.locator("text=Aéroport Paris Orly").first

    clickable = get_clickable(orly)
    assert safe_click(clickable, page), "Échec du clic sur 'Aéroport Paris Orly'."
    page.wait_for_timeout(1200)

    # 5. Vérification finale
    assert page.locator("text=Aéroport Paris Orly").first.is_visible(), \
        "'Aéroport Paris Orly' non visible après le clic."

    print("Scénario Aéroports terminé avec succès.")
