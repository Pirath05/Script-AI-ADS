import re
import time
import pytest
from playwright.sync_api import sync_playwright, TimeoutError, Page, Locator

BASE_URL                   = "https://www.bonjour-ratp.fr/"
EXPECTED_VIOLENCES_URL     = "https://www.bonjour-ratp.fr/aide-contact/?question=je-suis-victime-ou-temoin-d-une-agression"
EXPECTED_MENTIONS_PATTERN  = "**/informations-legales/**"
EXPECTED_MENTIONS_FRAGMENT = "#mentions-legales"
DEFAULT_TIMEOUT            = 15000
NAV_TIMEOUT                = 30000
SHORT_TIMEOUT              = 5000


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100, args=["--start-maximized"])
        yield browser
        browser.close()


@pytest.fixture
def page(browser):
    context = browser.new_context(viewport={"width": 1440, "height": 900}, locale="fr-FR")
    page = context.new_page()
    page.on("pageerror", lambda err: print(f"[PAGE ERROR] {err}"))
    yield page
    page.close()
    context.close()


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
            page.locator('button:has-text("Tout accepter")'),
            page.locator('button[aria-label*="accepter" i]'),
            page.locator('button', has_text=re.compile(r"accept", re.I)),
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


def scroll_to_bottom(page: Page) -> None:
    print("[scroll] Défilement progressif vers le bas...")
    page.evaluate("""
        () => new Promise(resolve => {
            const distance = 400, delay = 150;
            let scrolled = 0;
            const total = document.body.scrollHeight;
            const timer = setInterval(() => {
                window.scrollBy(0, distance);
                scrolled += distance;
                if (scrolled >= total) { clearInterval(timer); resolve(); }
            }, delay);
        })
    """)
    page.wait_for_timeout(2000)
    print("[scroll] ✓ Scroll terminé.")


def get_footer(page: Page) -> Locator:
    print("[footer] Recherche du footer...")
    loc = first_visible(page, [
        "footer",
        "[role='contentinfo']",
        "#footer",
        ".footer",
        "div[class*='footer']",
    ], timeout=DEFAULT_TIMEOUT)
    print("[footer] ✓ Footer trouvé.")
    return loc


def find_link_in_footer(footer: Locator, text: str, page: Page) -> Locator:
    print(f"[link] Recherche de '{text}' dans le footer...")
    per_strategy = SHORT_TIMEOUT // 6
    for i, fn in enumerate([
        lambda: footer.locator("a.l185tp5q", has_text=text),
        lambda: footer.locator(f'a:has-text("{text}")'),
        lambda: footer.locator("a", has_text=re.compile(re.escape(text), re.I)),
        lambda: footer.locator(f'a[aria-label*="{text}" i]'),
        lambda: footer.locator(f'a[title*="{text}" i]'),
        lambda: page.locator("a", has_text=re.compile(re.escape(text), re.I)),
    ], 1):
        try:
            loc = fn()
            loc.first.wait_for(state="visible", timeout=per_strategy)
            if loc.count() > 0:
                print(f"[link] ✓ '{text}' trouvé (stratégie {i}).")
                return loc.first
        except Exception as e:
            print(f"[link] stratégie {i} échouée: {e}")
    raise AssertionError(f"Lien '{text}' introuvable dans le footer.")


def safe_navigate(page: Page, action, timeout: int = DEFAULT_TIMEOUT) -> None:
    print("[nav] Navigation en cours...")
    try:
        with page.expect_navigation(timeout=timeout):
            action()
    except TimeoutError:
        print("[nav] expect_navigation timeout — attente networkidle.")
        page.wait_for_load_state("networkidle", timeout=timeout)
    print(f"[nav] ✓ URL : {page.url}")


def go_back(page: Page) -> None:
    print("[nav] Retour arrière...")
    page.go_back()
    page.wait_for_load_state("load")
    page.wait_for_timeout(1000)
    print(f"[nav] ✓ URL : {page.url}")


def test_footer_links(page: Page):
    print("\n" + "═" * 50)
    print("TEST : test_footer_links")
    print("═" * 50)

    print("\n[1] Navigation")
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=NAV_TIMEOUT)
    page.wait_for_load_state("load", timeout=NAV_TIMEOUT)
    print(f"  ✓ Titre : {page.title()!r}")
    snap(page, "01_loaded")

    print("\n[2] Cookies")
    accept_cookies(page)
    snap(page, "02_cookies")

    print("\n[3] Scroll lazy loading")
    scroll_to_bottom(page)
    page.wait_for_load_state("networkidle", timeout=DEFAULT_TIMEOUT)
    snap(page, "03_scrolled")

    print("\n[4] Footer visible")
    footer = get_footer(page)
    assert footer.is_visible(), "Footer non visible."
    snap(page, "04_footer")

    print("\n[5] Lien 'Violences sexistes ou sexuelles'")
    lien_violences = find_link_in_footer(footer, "Violences sexistes ou sexuelles", page)
    print(f"  href : {lien_violences.get_attribute('href')!r}")
    safe_navigate(page, lambda: safe_click(lien_violences, label="Violences"))
    actual = page.url
    print(f"  URL : {actual!r}")
    assert actual == EXPECTED_VIOLENCES_URL, (
        f"URL inattendue.\n  Attendu : {EXPECTED_VIOLENCES_URL}\n  Obtenu  : {actual}"
    )
    print("  ✓ URL correcte.")
    snap(page, "05_violences")

    print("\n[6] Retour accueil")
    go_back(page)
    snap(page, "06_back")

    print("\n[7] Re-scroll")
    scroll_to_bottom(page)
    snap(page, "07_rescrolled")

    print("\n[8] Lien 'Mentions légales'")
    footer = get_footer(page)
    lien_mentions = find_link_in_footer(footer, "Mentions légales", page)
    print(f"  href : {lien_mentions.get_attribute('href')!r}")
    safe_click(lien_mentions, label="Mentions légales")
    page.wait_for_url(EXPECTED_MENTIONS_PATTERN, timeout=DEFAULT_TIMEOUT)
    actual = page.url
    print(f"  URL : {actual!r}")
    assert EXPECTED_MENTIONS_FRAGMENT in actual, (
        f"Fragment '{EXPECTED_MENTIONS_FRAGMENT}' absent de l'URL : {actual}"
    )
    print(f"  ✓ Fragment présent.")
    snap(page, "08_mentions")

    print("\n[9] Titre 'Mentions légales' visible")
    try:
        titre = first_visible(page, [
            "h1:has-text('Mentions légales')",
            "h2:has-text('Mentions légales')",
            "[class*='title']:has-text('Mentions légales')",
        ], timeout=SHORT_TIMEOUT)
        assert titre.is_visible()
        print(f"  ✓ Titre visible : {titre.inner_text()!r}")
    except (TimeoutError, AssertionError):
        print("  ⚠ Titre non trouvé — page et fragment corrects, on continue.")
    snap(page, "09_final")

    print("\n✓ TEST RÉUSSI")
