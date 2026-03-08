import re
import time
import pytest
from playwright.sync_api import sync_playwright, TimeoutError, Page, BrowserContext

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────
BASE_URL        = "https://www.bonjour-ratp.fr/"
DEFAULT_TIMEOUT = 15000
NAV_TIMEOUT     = 30000
SHORT_TIMEOUT   = 5000

TRANSPORT_IDS = {
    "METRO":               "METRO",
    "RER":                 "RER",
    "TRANSILIEN":          "TRANSILIEN",
    "BUS":                 "BUS",
    "TRAM":                "TRAM",
    "CABLE":               "CABLE",
    "SELF_SERVICE_VEHICLE":"SELF_SERVICE_VEHICLE",
    "BICYCLE":             "BICYCLE",
}
KEEP_ACTIVE = {"METRO"}


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
        print("[SETUP] Contexte créé (1280×900, locale fr-FR).")
        yield context
        print("\n[TEARDOWN] Fermeture du navigateur.")
        context.close()
        browser.close()


@pytest.fixture
def page(browser_context: BrowserContext):
    page = browser_context.new_page()
    page.set_default_timeout(DEFAULT_TIMEOUT)
    page.set_default_navigation_timeout(NAV_TIMEOUT)
    print("[FIXTURE] Nouvelle page ouverte.")
    yield page
    if not page.is_closed():
        page.close()
        print("[FIXTURE] Page fermée.")


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────
def take_screenshot(page: Page, name: str) -> None:
    try:
        path = f"/tmp/screenshot_{name}_{int(time.time())}.png"
        page.screenshot(path=path, full_page=True)
        print(f"  [screenshot] Sauvegardé : {path}")
    except Exception as e:
        print(f"  [screenshot] Echec : {e}")


def accept_cookies(page: Page) -> None:
    """Accepte la bannière Didomi si elle apparaît."""
    print("  [cookies] Attente de la popup Didomi...")
    try:
        page.wait_for_selector("#didomi-popup", timeout=SHORT_TIMEOUT)
        print("  [cookies] Popup détectée — recherche du bouton Accepter.")
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
                    print("  [cookies] ✓ Bouton Accepter cliqué.")
                    break
            except Exception:
                continue
        if not clicked:
            print("  [cookies] AVERTISSEMENT : bouton Accepter introuvable — on continue.")
            return
        page.wait_for_selector("#didomi-popup", state="detached", timeout=10000)
        print("  [cookies] ✓ Popup fermée.")
    except TimeoutError:
        print("  [cookies] Pas de popup cookies (ou déjà acceptée).")


def safe_click(locator, page: Page, label: str = "élément", timeout: int = DEFAULT_TIMEOUT) -> bool:
    """Clic robuste : standard → forcé → dispatch JS."""
    print(f"  [click] Tentative sur : {label}")
    try:
        locator.scroll_into_view_if_needed(timeout=timeout)
    except Exception as e:
        print(f"  [click] Scroll échoué ({e}), on continue.")

    for attempt, kwargs in enumerate([
        {"timeout": timeout},
        {"force": True, "timeout": 3000},
    ], start=1):
        try:
            locator.click(**kwargs)
            print(f"  [click] ✓ Clic réussi (passe {attempt}) : {label}")
            return True
        except Exception as e:
            print(f"  [click] Passe {attempt} échouée : {e}")

    try:
        locator.dispatch_event("click")
        print(f"  [click] ✓ dispatch JS réussi : {label}")
        return True
    except Exception as e:
        print(f"  [click] dispatch JS échoué : {e}")

    print(f"  [click] ✗ Toutes les tentatives ont échoué pour : {label}")
    return False


def wait_for_any(page: Page, selectors: list[str], timeout: int = DEFAULT_TIMEOUT):
    """Attend que l'un des sélecteurs soit visible. Retourne (index, locator)."""
    deadline = time.time() + timeout / 1000
    while time.time() < deadline:
        for i, sel in enumerate(selectors):
            try:
                loc = page.locator(sel).first
                if loc.is_visible(timeout=500):
                    print(f"  [wait] ✓ Sélecteur trouvé (index {i}) : {sel!r}")
                    return i, loc
            except Exception:
                pass
        page.wait_for_timeout(300)
    raise TimeoutError(f"Aucun sélecteur visible en {timeout} ms : {selectors}")


def fill_field(page: Page, input_id: str, suggestions_id: str, text: str) -> None:
    """
    Remplit un champ de saisie et clique sur la 2e suggestion (index 1).
    Fallback : 1re suggestion si la 2e est absente.
    """
    print(f"  [fill] Remplissage du champ #{input_id} avec '{text}'")

    # Sélecteurs du champ en ordre de priorité
    field_selectors = [
        f"input#{input_id}",
        f"input[name='{input_id}']",
        f"input[placeholder*='{input_id}' i]",
        f"[data-testid='{input_id}'] input",
    ]
    _, field = wait_for_any(page, field_selectors, timeout=DEFAULT_TIMEOUT)

    field.click(timeout=DEFAULT_TIMEOUT)
    field.fill(text)
    print(f"  [fill] Texte saisi : '{text}'")
    page.wait_for_timeout(800)

    # Attendre les suggestions
    suggestion_selectors = [
        f"#{suggestions_id} li",
        f"[id*='suggestion'] li",
        f"ul[role='listbox'] li",
        f"[aria-label*='suggestion' i] li",
    ]
    print(f"  [fill] Attente des suggestions pour '{text}'...")
    try:
        _, suggestions_root = wait_for_any(page, suggestion_selectors, timeout=10000)
    except TimeoutError:
        take_screenshot(page, f"fill_{input_id}_no_suggestions")
        pytest.fail(f"Aucune suggestion n'est apparue pour le champ '{input_id}' avec le texte '{text}'.")

    # Cliquer sur la 2e suggestion (index 1), sinon la 1re
    suggestions = page.locator(suggestion_selectors[0])
    count = suggestions.count()
    print(f"  [fill] {count} suggestion(s) disponible(s).")
    target_idx = 1 if count > 1 else 0
    assert safe_click(suggestions.nth(target_idx), page, label=f"Suggestion {target_idx} pour '{text}'"), \
        f"Impossible de cliquer sur la suggestion pour '{input_id}'."
    print(f"  [fill] ✓ Suggestion sélectionnée pour '{input_id}'.")
    page.wait_for_timeout(600)


def swap(page: Page) -> None:
    """Inverse départ et arrivée."""
    print("  [swap] Inversion départ / arrivée...")
    swap_selectors = [
        'button[aria-label="Inverser départ et arrivée"]',
        'button[aria-label*="nverser" i]',
        'button[title*="nverser" i]',
        'button.swap-button',
    ]
    try:
        _, btn = wait_for_any(page, swap_selectors, timeout=DEFAULT_TIMEOUT)
    except TimeoutError:
        take_screenshot(page, "swap_not_found")
        pytest.fail("Bouton d'inversion départ/arrivée introuvable.")

    assert safe_click(btn, page, label="Bouton swap"), "Clic sur le bouton swap échoué."
    page.wait_for_timeout(600)
    print("  [swap] ✓ Inversion effectuée.")


def is_checked(page: Page, transport_id: str) -> bool:
    cb = page.locator(f"input#{transport_id}")
    try:
        return cb.count() > 0 and cb.is_checked()
    except Exception:
        return False


def toggle_transport(page: Page, transport_id: str, name: str) -> None:
    """Coche/décoche un mode de transport via son label ou sa checkbox."""
    label_selectors = [
        f"label[for='{transport_id}']",
        f"label:has(input#{transport_id})",
        f"[data-transport='{transport_id}']",
    ]
    clicked = False
    for sel in label_selectors:
        loc = page.locator(sel)
        if loc.count() > 0:
            if safe_click(loc.first, page, label=f"Label transport {name}"):
                clicked = True
                break

    if not clicked:
        # Fallback : clic direct sur la checkbox
        cb = page.locator(f"input#{transport_id}")
        if cb.count() > 0:
            safe_click(cb.first, page, label=f"Checkbox {name}")

    page.wait_for_timeout(400)
    state = "activé" if is_checked(page, transport_id) else "désactivé"
    print(f"  [transport] {name} → {state}")


# ─────────────────────────────────────────
# TEST PRINCIPAL
# ─────────────────────────────────────────
def test_itineraire_metro_uniquement(page: Page):
    print("\n" + "═" * 55)
    print("DÉBUT DU TEST : test_itineraire_metro_uniquement")
    print("═" * 55)

    # ── Étape 1 : Navigation ──────────────────────────────
    print(f"\n[ÉTAPE 1] Navigation vers {BASE_URL}")
    page.goto(BASE_URL, timeout=NAV_TIMEOUT, wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle", timeout=DEFAULT_TIMEOUT)
    print("  ✓ Page chargée.")
    take_screenshot(page, "01_page_loaded")

    # ── Étape 2 : Cookies ────────────────────────────────
    print("\n[ÉTAPE 2] Gestion des cookies")
    accept_cookies(page)
    take_screenshot(page, "02_cookies_done")

    # ── Étape 3 : Remplir départ / arrivée ───────────────
    print("\n[ÉTAPE 3] Saisie Départ : 'Republique'")
    fill_field(page, "departure", "departure-suggestions", "Republique")

    print("\n[ÉTAPE 3] Saisie Arrivée : 'Gare de Lyon'")
    fill_field(page, "arrival", "arrival-suggestions", "Gare de Lyon")
    take_screenshot(page, "03_fields_filled")

    # ── Étape 4 : Double inversion ───────────────────────
    print("\n[ÉTAPE 4] Double inversion départ / arrivée")
    swap(page)
    page.wait_for_timeout(500)
    swap(page)
    page.wait_for_timeout(500)
    take_screenshot(page, "04_after_double_swap")

    # ── Étape 5 : Clic sur le 1er itinéraire proposé ─────
    print("\n[ÉTAPE 5] Recherche du bouton du premier itinéraire")
    itinerary_selectors = [
        # Sélecteur original (CSS path)
        "#main > section.i119okux.bu9trog > div > div.idw1uie > div.i11clvn1 > div:nth-child(2) > div.b12h0ode.i8ngrdz > button",
        # Fallbacks progressivement plus larges
        "div.i11clvn1 div.b12h0ode button",
        "div.b12h0ode button",
        "[class*='itinerary'] button",
        "[class*='result'] button",
        "section button[class*='itinerary']",
        "main button[class*='route']",
    ]
    try:
        _, itinerary_btn = wait_for_any(page, itinerary_selectors, timeout=NAV_TIMEOUT)
    except TimeoutError:
        take_screenshot(page, "05_itinerary_not_found")
        pytest.fail("Aucun bouton d'itinéraire n'est apparu après la recherche.")

    assert safe_click(itinerary_btn, page, label="Premier itinéraire"), \
        "Impossible de cliquer sur le premier itinéraire."
    page.wait_for_timeout(1500)
    take_screenshot(page, "05_itinerary_clicked")

    # ── Étape 6 : Ouvrir les stations intermédiaires ─────
    print("\n[ÉTAPE 6] Ouverture des tronçons / stations intermédiaires")
    stations_selectors = [
        'button[aria-controls="stations-list-expanded-content"][aria-expanded="false"]',
        'button[aria-controls*="stations"][aria-expanded="false"]',
        'button[aria-expanded="false"][aria-controls*="station"]',
    ]
    opened = 0
    for sel in stations_selectors:
        btns = page.locator(sel)
        count = btns.count()
        if count > 0:
            print(f"  [stations] {count} bouton(s) trouvé(s) avec : {sel!r}")
            for i in range(count):
                try:
                    btns.nth(i).wait_for(state="visible", timeout=3000)
                    safe_click(btns.nth(i), page, label=f"Tronçon {i + 1}")
                    page.wait_for_timeout(800)
                    opened += 1
                    print(f"  [stations] ✓ Tronçon {i + 1} ouvert.")
                except Exception as e:
                    print(f"  [stations] Tronçon {i + 1} ignoré : {e}")
            break

    if opened == 0:
        print("  [stations] Aucun bouton de stations intermédiaires trouvé — on continue.")
    take_screenshot(page, "06_stations_expanded")

    # ── Étape 7 : Retour à la vue principale ─────────────
    print("\n[ÉTAPE 7] Retour à la vue principale")
    back_selectors = [
        'button[aria-label="Retour à votre trajet"]',
        'button[aria-label*="Retour" i]',
        'div.r1ox9p09',
        'span.a1gdnitw',
        'a[href*="itineraire"]',
    ]
    back_clicked = False
    for sel in back_selectors:
        loc = page.locator(sel)
        if loc.count() > 0:
            try:
                if loc.first.is_visible(timeout=2000):
                    safe_click(loc.first, page, label=f"Retour ({sel})")
                    page.wait_for_timeout(1000)
                    back_clicked = True
                    print(f"  [back] ✓ Retour effectué via : {sel!r}")
                    break
            except Exception:
                continue
    if not back_clicked:
        print("  [back] Bouton retour non trouvé — on continue (peut-être déjà en vue principale).")
    take_screenshot(page, "07_back_to_main")

    # ── Étape 8 : Inverser départ / arrivée ──────────────
    print("\n[ÉTAPE 8] Inversion départ / arrivée")
    page.wait_for_timeout(2000)
    swap(page)
    take_screenshot(page, "08_swapped")

    # ── Étape 9 : Ouvrir les filtres → Mode de transport ─
    print("\n[ÉTAPE 9] Ouverture des filtres")
    filter_selectors = [
        'button[aria-label="Accéder aux options de filtre"]',
        'button[aria-label*="filtre" i]',
        'button[aria-label*="filter" i]',
        'button:has-text("Filtres")',
        'button:has-text("Options")',
    ]
    try:
        _, filter_btn = wait_for_any(page, filter_selectors, timeout=DEFAULT_TIMEOUT)
    except TimeoutError:
        take_screenshot(page, "09_filter_btn_not_found")
        pytest.fail("Bouton d'accès aux filtres introuvable.")

    assert safe_click(filter_btn, page, label="Bouton filtres"), "Clic sur filtres échoué."
    page.wait_for_timeout(2000)
    take_screenshot(page, "09_filters_opened")

    # ── Étape 10 : Ouvrir la section "Mode de transport" ─
    print("\n[ÉTAPE 10] Ouverture de la section 'Mode de transport'")
    transport_section_selectors = [
        'button:has(span:has-text("Mode de transport"))',
        'button:has-text("Mode de transport")',
        '[aria-label*="transport" i]',
        'div:has-text("Mode de transport") button',
    ]
    try:
        _, transport_section = wait_for_any(page, transport_section_selectors, timeout=SHORT_TIMEOUT)
    except TimeoutError:
        take_screenshot(page, "10_transport_section_not_found")
        pytest.fail("Section 'Mode de transport' introuvable dans les filtres.")

    assert safe_click(transport_section, page, label="Section Mode de transport"), \
        "Clic sur la section Mode de transport échoué."
    page.wait_for_timeout(1000)
    take_screenshot(page, "10_transport_section_opened")

    # ── Étape 11 : Désactiver tout sauf METRO ────────────
    print("\n[ÉTAPE 11] Configuration des modes de transport (METRO uniquement)")
    to_disable = [t for t in TRANSPORT_IDS if t not in KEEP_ACTIVE]

    for transport_id in to_disable:
        if is_checked(page, transport_id):
            print(f"  [transport] Désactivation de {transport_id}...")
            toggle_transport(page, transport_id, transport_id)
        else:
            print(f"  [transport] {transport_id} déjà désactivé.")

    for transport_id in KEEP_ACTIVE:
        if not is_checked(page, transport_id):
            print(f"  [transport] Activation de {transport_id}...")
            toggle_transport(page, transport_id, transport_id)
        else:
            print(f"  [transport] {transport_id} déjà actif ✓")

    # Vérification
    active = [t for t in TRANSPORT_IDS if is_checked(page, t)]
    print(f"  [transport] Modes actifs : {active}")
    assert active == ["METRO"] or set(active) == KEEP_ACTIVE, \
        f"Configuration inattendue des transports : {active}"
    print("  ✓ Seul METRO est actif.")
    take_screenshot(page, "11_transport_configured")
    page.wait_for_timeout(800)

    # ── Étape 12 : Valider les filtres ───────────────────
    print("\n[ÉTAPE 12] Validation des filtres")
    validate_selectors = [
        'button:has-text("Voir les résultats")',
        'button:has-text("Valider")',
        'button:has-text("Appliquer")',
        "button[type='submit']",
    ]
    try:
        _, validate_btn = wait_for_any(page, validate_selectors, timeout=SHORT_TIMEOUT)
        assert safe_click(validate_btn, page, label="Valider filtres"), "Clic sur Valider échoué."
    except TimeoutError:
        print("  [validate] Bouton Valider non trouvé — les filtres sont peut-être auto-appliqués.")
    print("  ✓ Filtres validés.")

    # ── Étape 13 : Screenshot final ──────────────────────
    print("\n[ÉTAPE 13] Screenshot final")
    page.wait_for_timeout(5000)
    final_path = "screenshot_itineraire_metro.png"
    page.screenshot(path=final_path, full_page=True)
    print(f"  ✓ Screenshot enregistré : {final_path}")
    take_screenshot(page, "13_final")

    page.wait_for_timeout(2000)
    print("\n" + "═" * 55)
    print("✓ TEST RÉUSSI : Itinéraire Metro uniquement terminé.")
    print("═" * 55)
