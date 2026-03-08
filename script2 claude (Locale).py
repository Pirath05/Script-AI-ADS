import re
import time
import pytest
from playwright.sync_api import sync_playwright, TimeoutError, Page, BrowserContext

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────
BASE_URL = "https://www.bonjour-ratp.fr/aeroports/"
DEFAULT_TIMEOUT = 15000
NAV_TIMEOUT     = 30000
SHORT_TIMEOUT   = 5000


# ─────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────
@pytest.fixture(scope="session")
def browser_context():
    print("\n[SETUP] Lancement du navigateur Chromium...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="fr-FR",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        print("[SETUP] Contexte navigateur créé (1280×900, locale fr-FR).")
        yield context
        print("\n[TEARDOWN] Fermeture du navigateur.")
        context.close()
        browser.close()


@pytest.fixture
def page(browser_context: BrowserContext):
    page = browser_context.new_page()
    page.set_default_timeout(DEFAULT_TIMEOUT)
    page.set_default_navigation_timeout(NAV_TIMEOUT)
    print(f"[FIXTURE] Nouvelle page ouverte (timeout défaut : {DEFAULT_TIMEOUT} ms).")
    yield page
    if not page.is_closed():
        page.close()
        print("[FIXTURE] Page fermée.")


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────
def accept_cookies(page: Page) -> None:
    """Accepte la bannière Didomi si elle apparaît."""
    print("  [cookies] Attente de la popup Didomi...")
    try:
        page.wait_for_selector("#didomi-popup", timeout=SHORT_TIMEOUT)
        print("  [cookies] Popup détectée — recherche du bouton Accepter.")

        # Sélecteurs par ordre de priorité
        candidates = [
            page.locator("#didomi-notice-agree-button"),
            page.locator('button[aria-label*="accepter" i]'),
            page.locator('button', has_text=re.compile(r"tout accepter", re.I)),
            page.locator('button', has_text=re.compile(r"accepter", re.I)),
        ]
        clicked = False
        for btn in candidates:
            try:
                if btn.first.is_visible(timeout=2000):
                    btn.first.click(timeout=3000)
                    clicked = True
                    print("  [cookies] Bouton Accepter cliqué.")
                    break
            except Exception:
                continue

        if not clicked:
            print("  [cookies] AVERTISSEMENT : aucun bouton Accepter trouvé — on continue.")
            return

        page.wait_for_selector("#didomi-popup", state="detached", timeout=10000)
        print("  [cookies] Popup fermée avec succès.")

    except TimeoutError:
        print("  [cookies] Pas de popup cookies (ou déjà acceptée).")


def safe_click(locator, page: Page, label: str = "élément", timeout: int = DEFAULT_TIMEOUT) -> bool:
    """
    Clic robuste en plusieurs passes :
    1. Scroll into view
    2. Clic standard Playwright
    3. Clic forcé (contourne overlays)
    4. dispatch('click') via JS en dernier recours
    """
    print(f"  [click] Tentative de clic sur : {label}")
    try:
        locator.scroll_into_view_if_needed(timeout=timeout)
        print(f"  [click] Scroll OK pour : {label}")
    except Exception as e:
        print(f"  [click] Scroll échoué ({e}) — on continue.")

    # Passe 1 : clic normal
    try:
        locator.click(timeout=timeout)
        print(f"  [click] ✓ Clic standard réussi : {label}")
        return True
    except Exception as e:
        print(f"  [click] Clic standard échoué : {e}")

    # Passe 2 : clic forcé
    try:
        locator.click(force=True, timeout=3000)
        print(f"  [click] ✓ Clic forcé réussi : {label}")
        return True
    except Exception as e:
        print(f"  [click] Clic forcé échoué : {e}")

    # Passe 3 : dispatch JS
    try:
        locator.dispatch_event("click")
        print(f"  [click] ✓ dispatch('click') JS réussi : {label}")
        return True
    except Exception as e:
        print(f"  [click] dispatch JS échoué : {e}")

    print(f"  [click] ✗ Toutes les tentatives ont échoué pour : {label}")
    return False


def get_clickable(locator, page: Page):
    """
    Remonte au premier ancêtre <a> ou <button> cliquable si disponible.
    Utile quand le texte est dans un <span> enfant.
    """
    for xpath in [
        "xpath=ancestor::a[1]",
        "xpath=ancestor::button[1]",
    ]:
        try:
            ancestor = locator.locator(xpath)
            if ancestor.count() > 0:
                print(f"  [click] Remontée vers ancêtre ({xpath}).")
                return ancestor.first
        except Exception:
            pass
    return locator


def wait_for_any(page: Page, selectors: list[str], timeout: int = DEFAULT_TIMEOUT):
    """
    Attend que l'un des sélecteurs de la liste soit visible.
    Retourne (index, locator) du premier trouvé, lève TimeoutError sinon.
    """
    deadline = time.time() + timeout / 1000
    while time.time() < deadline:
        for i, sel in enumerate(selectors):
            try:
                loc = page.locator(sel).first
                if loc.is_visible(timeout=500):
                    print(f"  [wait] Sélecteur trouvé (index {i}) : {sel!r}")
                    return i, loc
            except Exception:
                pass
        page.wait_for_timeout(300)
    raise TimeoutError(f"Aucun des sélecteurs n'est apparu dans {timeout} ms : {selectors}")


def scroll_page(page: Page, direction: str = "down") -> None:
    """Scroll vers le bas ou le haut pour déclencher le lazy loading."""
    if direction == "down":
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        print("  [scroll] Scroll bas effectué.")
    else:
        page.evaluate("window.scrollTo(0, 0)")
        print("  [scroll] Scroll haut effectué.")
    page.wait_for_timeout(700)


def take_screenshot(page: Page, name: str) -> None:
    """Capture d'écran de débogage (ignorée si echec)."""
    try:
        path = f"/tmp/screenshot_{name}_{int(time.time())}.png"
        page.screenshot(path=path)
        print(f"  [screenshot] Sauvegardé : {path}")
    except Exception as e:
        print(f"  [screenshot] Echec capture : {e}")


# ─────────────────────────────────────────
# TEST PRINCIPAL
# ─────────────────────────────────────────
def test_aeroports_parcours(page: Page):
    print("\n" + "═" * 55)
    print("DÉBUT DU TEST : test_aeroports_parcours")
    print("═" * 55)

    # ── Étape 1 : Navigation ──────────────────────────────
    print(f"\n[ÉTAPE 1] Navigation vers {BASE_URL}")
    page.goto(BASE_URL, timeout=NAV_TIMEOUT, wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle", timeout=DEFAULT_TIMEOUT)
    print("  ✓ Page chargée (networkidle).")
    take_screenshot(page, "01_page_loaded")

    # ── Étape 2 : Cookies ────────────────────────────────
    print("\n[ÉTAPE 2] Gestion des cookies")
    accept_cookies(page)
    take_screenshot(page, "02_cookies_accepted")

    # ── Étape 3 : Lazy loading ───────────────────────────
    print("\n[ÉTAPE 3] Déclenchement du lazy loading (scroll bas → haut)")
    scroll_page(page, "down")
    scroll_page(page, "up")
    take_screenshot(page, "03_after_scroll")

    # ── Étape 4 : Clic sur l'ancre "Aéroports" (#plus) ──
    print('\n[ÉTAPE 4] Recherche du lien "Aéroports" (#plus)')

    aero_selectors = [
        'a[href="#plus"]:has-text("Aéroports")',
        'a[href="#plus"]',
        'a.a1oylayc[href="#plus"]',
        'nav a:has-text("Aéroports")',
        'a:has-text("Aéroports")',
    ]
    try:
        idx, aero_anchor = wait_for_any(page, aero_selectors, timeout=10000)
        print(f"  ✓ Ancre Aéroports trouvée avec sélecteur index {idx}.")
    except TimeoutError:
        take_screenshot(page, "04_aero_anchor_not_found")
        pytest.fail("Impossible de trouver le lien 'Aéroports' (#plus) avec tous les sélecteurs.")

    assert safe_click(aero_anchor, page, label="Lien Aéroports (#plus)"), \
        "Impossible de cliquer sur le lien 'Aéroports'."
    page.wait_for_timeout(1000)
    take_screenshot(page, "04_after_aero_click")

    # ── Étape 5 : Clic sur "Aéroport Paris Orly" ────────
    print('\n[ÉTAPE 5] Recherche de la carte "Aéroport Paris Orly"')

    orly_selectors = [
        "span.l1vm0fus.lvv0exu:has-text('Aéroport Paris Orly')",
        "span.l1vm0fus:has-text('Aéroport Paris Orly')",
        "[class*='listing'] a:has-text('Aéroport Paris Orly')",
        "a:has-text('Aéroport Paris Orly')",
        "text=Aéroport Paris Orly",
    ]
    try:
        idx, orly = wait_for_any(page, orly_selectors, timeout=12000)
        print(f"  ✓ Carte Orly trouvée avec sélecteur index {idx}.")
    except TimeoutError:
        # Dernier recours : scroll + retry
        print("  [ÉTAPE 5] Carte non visible — nouveau scroll et retry...")
        scroll_page(page, "down")
        page.wait_for_timeout(1000)
        scroll_page(page, "up")
        try:
            idx, orly = wait_for_any(page, orly_selectors, timeout=8000)
            print(f"  ✓ Carte Orly trouvée après scroll (index {idx}).")
        except TimeoutError:
            take_screenshot(page, "05_orly_not_found")
            pytest.fail("Impossible de trouver 'Aéroport Paris Orly' avec tous les sélecteurs.")

    clickable_orly = get_clickable(orly, page)
    assert safe_click(clickable_orly, page, label="Aéroport Paris Orly"), \
        "Échec du clic sur 'Aéroport Paris Orly'."
    page.wait_for_timeout(1500)
    take_screenshot(page, "05_after_orly_click")

    # ── Étape 6 : Vérification de la page Orly ──────────
    print("\n[ÉTAPE 6] Vérification de l'arrivée sur la page Orly")

    verification_selectors = [
        "h1:has-text('Orly')",
        "h1:has-text('Aéroport Paris Orly')",
        "[class*='hero'] :has-text('Orly')",
        "text=Aéroport Paris Orly",
        "text=Orly",
    ]
    try:
        _, found = wait_for_any(page, verification_selectors, timeout=10000)
        print(f"  ✓ Contenu 'Orly' visible sur la page de destination.")
    except TimeoutError:
        take_screenshot(page, "06_orly_page_not_confirmed")
        pytest.fail("La page 'Aéroport Paris Orly' ne semble pas s'être chargée correctement.")

    current_url = page.url
    print(f"  URL courante : {current_url}")
    assert "orly" in current_url.lower() or page.locator("text=Orly").first.is_visible(), \
        f"URL inattendue ou contenu Orly absent : {current_url}"

    take_screenshot(page, "06_final_orly_page")
    print("\n" + "═" * 55)
    print("✓ TEST RÉUSSI : Scénario Aéroports terminé avec succès.")
    print("═" * 55)
