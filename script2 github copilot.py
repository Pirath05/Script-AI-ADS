import pytest
import re
from playwright.sync_api import sync_playwright, TimeoutError

# ---------------------------------------------------------
# FIXTURES PLAYWRIGHT
# ---------------------------------------------------------

@pytest.fixture(scope="session")
def browser_context():
    print("\n[INFO] Lancement du navigateur…")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        yield context
        print("[INFO] Fermeture du navigateur…")
        context.close()
        browser.close()

@pytest.fixture
def page(browser_context):
    print("[INFO] Ouverture d'un nouvel onglet…")
    page = browser_context.new_page()
    yield page
    if not page.is_closed():
        print("[INFO] Fermeture de l'onglet…")
        page.close()

# ---------------------------------------------------------
# FONCTIONS UTILITAIRES
# ---------------------------------------------------------

def scroll_to_bottom_and_top(page, pause_bottom=800, pause_top=500):
    print("[STEP] Scroll bas → haut…")
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(pause_bottom)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(pause_top)

def safe_click(locator, page, allow_navigation=False, timeout=10000):
    """
    Clic robuste avec fallback :
    - scroll into view
    - hover
    - clic normal
    - clic forcé
    - clic JS
    """
    print("[ACTION] Tentative de clic sécurisé…")

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
        print("[INFO] Clic réussi (normal).")
        return True
    except Exception:
        print("[WARN] Clic normal échoué → tentative force=True…")

    try:
        locator.click(force=True, timeout=2000)
        print("[INFO] Clic réussi (force=True).")
        return True
    except Exception:
        print("[WARN] Clic force=True échoué → tentative JS…")

    try:
        page.evaluate("(el) => el.click()", locator)
        print("[INFO] Clic réussi (JS).")
        return True
    except Exception:
        print("[ERROR] Toutes les tentatives de clic ont échoué.")
        return False

# ---------------------------------------------------------
# TEST PRINCIPAL
# ---------------------------------------------------------

def test_aeroports_parcours(page):
    print("\n===== DÉBUT DU TEST AÉROPORTS =====")

    url = "https://www.bonjour-ratp.fr/aeroports/"
    print(f"[STEP] Navigation vers {url}…")
    page.goto(url, timeout=20000)
    page.wait_for_load_state("networkidle", timeout=15000)

    # ------------------------------
    # Cookies
    # ------------------------------
    print("[STEP] Vérification du popup cookies…")
    try:
        page.wait_for_selector("#didomi-popup", timeout=5000)
        print("[ACTION] Popup détecté → clic sur 'Accepter'")
        page.get_by_role("button", name=re.compile("accepter", re.I)).click()
        page.wait_for_selector("#didomi-popup", state="detached", timeout=10000)
    except TimeoutError:
        print("[INFO] Aucun popup cookies détecté.")

    # ------------------------------
    # Scroll
    # ------------------------------
    scroll_to_bottom_and_top(page)

    # ------------------------------
    # Clic sur l’ancre "Aéroports"
    # ------------------------------
    print("[STEP] Recherche du lien 'Aéroports'…")
    aero_anchor = page.get_by_role("link", name=re.compile("Aéroports", re.I))

    try:
        aero_anchor.wait_for(state="visible", timeout=8000)
    except TimeoutError:
        print("[WARN] Sélecteur principal introuvable → fallback…")
        aero_anchor = page.locator('a[href="#plus"]', has_text="Aéroports").first

    print("[ACTION] Clic sur 'Aéroports'.")
    clicked = safe_click(aero_anchor, page)
    assert clicked, "Impossible de cliquer sur le lien 'Aéroports'."

    page.wait_for_timeout(800)

    # ------------------------------
    # Clic sur "Aéroport Paris Orly"
    # ------------------------------
    print("[STEP] Recherche de 'Aéroport Paris Orly'…")
    orly_span = page.get_by_text("Aéroport Paris Orly").first

    try:
        orly_span.wait_for(state="visible", timeout=10000)
    except TimeoutError:
        print("[WARN] Fallback sur un sélecteur texte simple.")
        orly_span = page.locator("text=Aéroport Paris Orly").first

    print("[STEP] Recherche du lien parent…")
    try:
        ancestor_link = orly_span.locator("xpath=ancestor::a[1]")
        clickable = ancestor_link.first if ancestor_link.count() > 0 else orly_span
    except Exception:
        clickable = orly_span

    print("[ACTION] Clic sur 'Aéroport Paris Orly'.")
    clicked_orly = safe_click(clickable, page)
    assert clicked_orly, "Échec du clic sur 'Aéroport Paris Orly'."

    page.wait_for_timeout(1200)

    # ------------------------------
    # Vérification finale
    # ------------------------------
    print("[STEP] Vérification de la présence du texte 'Aéroport Paris Orly'…")
    assert page.get_by_text("Aéroport Paris Orly").first.is_visible(), \
        "Le texte 'Aéroport Paris Orly' n'est pas visible après clic."

    print("===== FIN DU TEST AÉROPORTS =====\n")
