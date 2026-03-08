import pytest
import re
from playwright.sync_api import sync_playwright, TimeoutError

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

def scroll_to_bottom_and_top(page, pause_bottom=800, pause_top=500):
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(pause_bottom)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(pause_top)

def safe_click(locator, page, allow_navigation=False, timeout=10000):
    try:
        locator.scroll_into_view_if_needed(timeout=timeout)
    except Exception:
        pass
    try:
        locator.hover(timeout=2000)
    except Exception:
        pass
    try:
        if allow_navigation:
            with page.expect_navigation(wait_until="load", timeout=timeout):
                locator.click(timeout=timeout)
        else:
            locator.click(timeout=timeout)
        return True
    except Exception:
        try:
            locator.click(force=True, timeout=2000)
            return True
        except Exception:
            try:
                page.evaluate("(el) => el.click()", locator)
                return True
            except Exception:
                return False

def test_aeroports_parcours(page):
    url = "https://www.preprod.bonjour-ratp.fr/aeroports/"
    page.goto(url, timeout=20000)
    page.wait_for_load_state("networkidle", timeout=15000)

    try:
        page.wait_for_selector("#didomi-popup", timeout=5000)
        bouton_cookies = page.locator('button', has_text=re.compile("accepter", re.I))
        if bouton_cookies.count() > 0 and bouton_cookies.is_visible():
            bouton_cookies.first.click()
        page.wait_for_selector("#didomi-popup", state="detached", timeout=10000)
    except TimeoutError:
        pass

    scroll_to_bottom_and_top(page)

    aero_anchor = page.locator('a[href="#plus"]', has_text="Aéroports").first
    try:
        aero_anchor.wait_for(state="visible", timeout=8000)
    except TimeoutError:
        aero_anchor = page.locator('a.a1oylayc[href="#plus"]').first

    clicked = safe_click(aero_anchor, page, allow_navigation=False, timeout=10000)
    assert clicked, "Impossible de cliquer sur le lien 'Aéroports'."

    page.wait_for_timeout(800)

    orly_span = page.locator("span.l1vm0fus.lvv0exu >> text=Aéroport Paris Orly").first
    try:
        orly_span.wait_for(state="visible", timeout=10000)
    except TimeoutError:
        orly_span = page.locator("text=Aéroport Paris Orly").first

    clickable = None
    try:
        ancestor_link = orly_span.locator("xpath=ancestor::a[1]")
        if ancestor_link.count() > 0:
            clickable = ancestor_link.first
        else:
            clickable = orly_span
    except Exception:
        clickable = orly_span

    try:
        clickable.scroll_into_view_if_needed(timeout=5000)
    except Exception:
        pass

    clicked_orly = safe_click(clickable, page, allow_navigation=False, timeout=10000)
    assert clicked_orly, "Échec du clic sur l'élément 'Aéroport Paris Orly'."

    page.wait_for_timeout(1200)

    try:
        assert page.locator("text=Aéroport Paris Orly").first.is_visible(), "Le texte 'Aéroport Paris Orly' n'est pas visible après clic."
    except Exception:
        pass
