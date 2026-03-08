import re
import time
import pytest
from playwright.sync_api import sync_playwright, TimeoutError, Page, BrowserContext

BASE_URL        = "https://www.bonjour-ratp.fr/aeroports/"
DEFAULT_TIMEOUT = 15000
NAV_TIMEOUT     = 30000
SHORT_TIMEOUT   = 5000


@pytest.fixture(scope="session")
def browser_context():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="fr-FR",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        )
        yield context
        context.close()
        browser.close()


@pytest.fixture
def page(browser_context: BrowserContext):
    page = browser_context.new_page()
    page.set_default_timeout(DEFAULT_TIMEOUT)
    page.set_default_navigation_timeout(NAV_TIMEOUT)
    yield page
    if not page.is_closed():
        page.close()


def snap(page: Page, name: str) -> None:
    try:
        page.screenshot(path=f"/tmp/{name}_{int(time.time())}.png", full_page=True)
    except Exception:
        pass


def safe_click(locator, label: str = "", timeout: int = DEFAULT_TIMEOUT) -> bool:
    try:
        locator.scroll_into_view_if_needed(timeout=timeout)
    except Exception:
        pass
    for attempt, kwargs in enumerate([{"timeout": timeout}, {"force": True, "timeout": 3000}], 1):
        try:
            locator.click(**kwargs)
            print(f"[click] ✓ {label} (passe {attempt})")
            return True
        except Exception as e:
            print(f"[click] passe {attempt} échouée pour '{label}': {e}")
    try:
        locator.dispatch_event("click")
        print(f"[click] ✓ {label} (dispatch JS)")
        return True
    except Exception as e:
        print(f"[click] ✗ {label} — toutes les tentatives échouées: {e}")
        return False


def first_visible(page: Page, selectors: list[str], timeout: int = DEFAULT_TIMEOUT):
    deadline = time.time() + timeout / 1000
    while time.time() < deadline:
        for i, sel in enumerate(selectors):
            try:
                loc = page.locator(sel).first
                if loc.is_visible(timeout=500):
                    print(f"[selector] ✓ index {i}: {sel!r}")
                    return loc
            except Exception:
                pass
        page.wait_for_timeout(300)
    raise TimeoutError(f"Aucun sélecteur visible en {timeout}ms: {selectors}")


def accept_cookies(page: Page) -> None:
    print("[cookies] Vérification popup Didomi...")
    try:
        page.wait_for_selector("#didomi-popup", timeout=SHORT_TIMEOUT)
        for btn in [
            page.locator("#didomi-notice-agree-button"),
            page.locator('button[aria-label*="accepter" i]'),
            page.locator('button', has_text=re.compile(r"tout accepter", re.I)),
            page.locator('button', has_text=re.compile(r"accepter", re.I)),
        ]:
            try:
                if btn.first.is_visible(timeout=2000):
                    btn.first.click(timeout=3000)
                    page.wait_for_selector("#didomi-popup", state="detached", timeout=10000)
                    print("[cookies] ✓ Accepté.")
                    return
            except Exception:
                continue
        print("[cookies] ⚠ Bouton introuvable, on continue.")
    except TimeoutError:
        print("[cookies] Pas de popup.")


def test_aeroports_parcours(page: Page):
    print("\n" + "═" * 50)
    print("TEST : test_aeroports_parcours")
    print("═" * 50)

    print("\n[1] Navigation")
    page.goto(BASE_URL, timeout=NAV_TIMEOUT, wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle", timeout=DEFAULT_TIMEOUT)
    print("  ✓ Page chargée")
    snap(page, "01_loaded")

    print("\n[2] Cookies")
    accept_cookies(page)
    snap(page, "02_cookies")

    print("\n[3] Scroll lazy loading")
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(800)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(600)
    snap(page, "03_scroll")

    print("\n[4] Clic ancre Aéroports")
    try:
        aero = first_visible(page, [
            'a[href="#plus"]:has-text("Aéroports")',
            'a[href="#plus"]',
            'a.a1oylayc[href="#plus"]',
            'nav a:has-text("Aéroports")',
            'a:has-text("Aéroports")',
        ], timeout=10000)
    except TimeoutError:
        snap(page, "04_aero_not_found")
        pytest.fail("Lien Aéroports (#plus) introuvable.")
    assert safe_click(aero, label="Aéroports #plus"), "Clic Aéroports échoué."
    page.wait_for_timeout(1000)
    snap(page, "04_aero_clicked")

    print("\n[5] Clic carte Orly")
    orly_selectors = [
        "span.l1vm0fus.lvv0exu:has-text('Aéroport Paris Orly')",
        "span.l1vm0fus:has-text('Aéroport Paris Orly')",
        "[class*='listing'] a:has-text('Aéroport Paris Orly')",
        "a:has-text('Aéroport Paris Orly')",
        "text=Aéroport Paris Orly",
    ]
    try:
        orly = first_visible(page, orly_selectors, timeout=12000)
    except TimeoutError:
        print("  Orly non visible — scroll + retry")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1000)
        page.evaluate("window.scrollTo(0, 0)")
        try:
            orly = first_visible(page, orly_selectors, timeout=8000)
        except TimeoutError:
            snap(page, "05_orly_not_found")
            pytest.fail("Carte Aéroport Paris Orly introuvable.")

    for xpath in ["xpath=ancestor::a[1]", "xpath=ancestor::button[1]"]:
        try:
            anc = orly.locator(xpath)
            if anc.count() > 0:
                orly = anc.first
                break
        except Exception:
            pass

    assert safe_click(orly, label="Aéroport Paris Orly"), "Clic Orly échoué."
    page.wait_for_timeout(1500)
    snap(page, "05_orly_clicked")

    print("\n[6] Vérification page Orly")
    try:
        first_visible(page, [
            "h1:has-text('Orly')",
            "h1:has-text('Aéroport Paris Orly')",
            "[class*='hero'] :has-text('Orly')",
            "text=Aéroport Paris Orly",
        ], timeout=10000)
    except TimeoutError:
        snap(page, "06_orly_verification_failed")
        pytest.fail("Page Orly non confirmée après le clic.")

    url = page.url
    print(f"  URL : {url}")
    assert "orly" in url.lower() or page.locator("text=Orly").first.is_visible(), \
        f"URL inattendue ou contenu Orly absent : {url}"
    snap(page, "06_final")
    print("\n✓ TEST RÉUSSI")
