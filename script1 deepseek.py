import re
import time
import pytest
from playwright.sync_api import sync_playwright, TimeoutError, Page, BrowserContext

BASE_URL        = "https://www.bonjour-ratp.fr/"
DEFAULT_TIMEOUT = 15000
NAV_TIMEOUT     = 30000
SHORT_TIMEOUT   = 5000

TRANSPORT_IDS = ["METRO", "RER", "TRANSILIEN", "BUS", "TRAM", "CABLE", "SELF_SERVICE_VEHICLE", "BICYCLE"]
KEEP_ACTIVE   = {"METRO"}


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


def fill_field(page: Page, input_id: str, suggestions_id: str, text: str) -> None:
    print(f"[fill] #{input_id} ← '{text}'")
    field = first_visible(page, [
        f"input#{input_id}",
        f"input[name='{input_id}']",
        f"[data-testid='{input_id}'] input",
        f"input[placeholder*='{input_id}' i]",
    ])
    field.click()
    field.fill(text)
    page.wait_for_timeout(800)

    try:
        suggestions = first_visible(page, [
            f"#{suggestions_id} li",
            "ul[role='listbox'] li",
            "[id*='suggestion'] li",
            "[aria-label*='suggestion' i] li",
        ], timeout=10000)
    except TimeoutError:
        snap(page, f"fill_{input_id}_no_suggestions")
        pytest.fail(f"Aucune suggestion pour '{input_id}' avec texte '{text}'.")

    all_suggestions = page.locator(f"#{suggestions_id} li")
    count = all_suggestions.count()
    print(f"[fill] {count} suggestion(s) — sélection index {'1' if count > 1 else '0'}")
    target = all_suggestions.nth(1 if count > 1 else 0)
    assert safe_click(target, label=f"Suggestion '{text}'"), f"Clic suggestion '{input_id}' échoué."
    page.wait_for_timeout(600)


def swap(page: Page) -> None:
    print("[swap] Inversion départ / arrivée")
    try:
        btn = first_visible(page, [
            'button[aria-label="Inverser départ et arrivée"]',
            'button[aria-label*="nverser" i]',
            'button[title*="nverser" i]',
            'button.swap-button',
        ])
    except TimeoutError:
        snap(page, "swap_not_found")
        pytest.fail("Bouton swap introuvable.")
    assert safe_click(btn, label="Swap"), "Clic swap échoué."
    page.wait_for_timeout(600)
    print("[swap] ✓ Inversé.")


def is_checked(page: Page, tid: str) -> bool:
    try:
        cb = page.locator(f"input#{tid}")
        return cb.count() > 0 and cb.is_checked()
    except Exception:
        return False


def toggle_transport(page: Page, tid: str) -> None:
    clicked = False
    for sel in [f"label[for='{tid}']", f"label:has(input#{tid})", f"[data-transport='{tid}']"]:
        loc = page.locator(sel)
        if loc.count() > 0:
            if safe_click(loc.first, label=f"Label {tid}"):
                clicked = True
                break
    if not clicked:
        cb = page.locator(f"input#{tid}")
        if cb.count() > 0:
            safe_click(cb.first, label=f"Checkbox {tid}")
    page.wait_for_timeout(400)
    print(f"[transport] {tid} → {'ON' if is_checked(page, tid) else 'OFF'}")


def test_itineraire_metro_uniquement(page: Page):
    print("\n" + "═" * 50)
    print("TEST : test_itineraire_metro_uniquement")
    print("═" * 50)

    print("\n[1] Navigation")
    page.goto(BASE_URL, timeout=NAV_TIMEOUT, wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle", timeout=DEFAULT_TIMEOUT)
    print("  ✓ Page chargée")
    snap(page, "01_loaded")

    print("\n[2] Cookies")
    accept_cookies(page)
    snap(page, "02_cookies")

    print("\n[3] Saisie départ / arrivée")
    fill_field(page, "departure", "departure-suggestions", "Republique")
    fill_field(page, "arrival",   "arrival-suggestions",   "Gare de Lyon")
    snap(page, "03_fields")

    print("\n[4] Double inversion")
    swap(page)
    page.wait_for_timeout(500)
    swap(page)
    snap(page, "04_swapped")

    print("\n[5] Clic premier itinéraire")
    try:
        itinerary = first_visible(page, [
            "#main > section.i119okux.bu9trog > div > div.idw1uie > div.i11clvn1 > div:nth-child(2) > div.b12h0ode.i8ngrdz > button",
            "div.i11clvn1 div.b12h0ode button",
            "div.b12h0ode button",
            "[class*='itinerary'] button",
            "[class*='result'] button",
            "main button[class*='route']",
        ], timeout=NAV_TIMEOUT)
    except TimeoutError:
        snap(page, "05_itinerary_not_found")
        pytest.fail("Aucun bouton d'itinéraire trouvé.")
    assert safe_click(itinerary, label="Premier itinéraire"), "Clic itinéraire échoué."
    page.wait_for_timeout(1500)
    snap(page, "05_itinerary_clicked")

    print("\n[6] Stations intermédiaires")
    opened = 0
    for sel in [
        'button[aria-controls="stations-list-expanded-content"][aria-expanded="false"]',
        'button[aria-controls*="stations"][aria-expanded="false"]',
        'button[aria-expanded="false"][aria-controls*="station"]',
    ]:
        btns = page.locator(sel)
        if btns.count() > 0:
            for i in range(btns.count()):
                try:
                    btns.nth(i).wait_for(state="visible", timeout=3000)
                    safe_click(btns.nth(i), label=f"Tronçon {i+1}")
                    page.wait_for_timeout(700)
                    opened += 1
                except Exception:
                    pass
            break
    print(f"  {opened} tronçon(s) ouvert(s).")
    snap(page, "06_stations")

    print("\n[7] Retour vue principale")
    for sel in [
        'button[aria-label="Retour à votre trajet"]',
        'button[aria-label*="Retour" i]',
        'div.r1ox9p09',
        'span.a1gdnitw',
    ]:
        loc = page.locator(sel)
        if loc.count() > 0:
            try:
                if loc.first.is_visible(timeout=2000):
                    safe_click(loc.first, label=f"Retour ({sel})")
                    page.wait_for_timeout(1000)
                    print(f"  ✓ Retour via {sel!r}")
                    break
            except Exception:
                pass
    snap(page, "07_back")

    print("\n[8] Inversion finale")
    page.wait_for_timeout(2000)
    swap(page)
    snap(page, "08_swap_final")

    print("\n[9] Ouverture des filtres")
    try:
        filter_btn = first_visible(page, [
            'button[aria-label="Accéder aux options de filtre"]',
            'button[aria-label*="filtre" i]',
            'button:has-text("Filtres")',
            'button:has-text("Options")',
        ])
    except TimeoutError:
        snap(page, "09_filter_not_found")
        pytest.fail("Bouton filtres introuvable.")
    assert safe_click(filter_btn, label="Filtres"), "Clic filtres échoué."
    page.wait_for_timeout(2000)
    snap(page, "09_filters")

    print("\n[10] Section Mode de transport")
    try:
        section = first_visible(page, [
            'button:has(span:has-text("Mode de transport"))',
            'button:has-text("Mode de transport")',
            '[aria-label*="transport" i]',
        ], timeout=SHORT_TIMEOUT)
    except TimeoutError:
        snap(page, "10_transport_section_not_found")
        pytest.fail("Section 'Mode de transport' introuvable.")
    assert safe_click(section, label="Mode de transport"), "Clic section transport échoué."
    page.wait_for_timeout(1000)
    snap(page, "10_transport_section")

    print("\n[11] Configuration transports")
    for tid in TRANSPORT_IDS:
        should_be_on = tid in KEEP_ACTIVE
        currently_on = is_checked(page, tid)
        if should_be_on != currently_on:
            toggle_transport(page, tid)
        else:
            print(f"[transport] {tid} → déjà {'ON' if currently_on else 'OFF'} ✓")

    active = [t for t in TRANSPORT_IDS if is_checked(page, t)]
    print(f"  Actifs : {active}")
    assert set(active) == KEEP_ACTIVE, f"Configuration inattendue : {active}"
    print("  ✓ METRO seul actif.")
    snap(page, "11_transports")

    print("\n[12] Validation filtres")
    try:
        validate = first_visible(page, [
            'button:has-text("Voir les résultats")',
            'button:has-text("Valider")',
            'button:has-text("Appliquer")',
            "button[type='submit']",
        ], timeout=SHORT_TIMEOUT)
        safe_click(validate, label="Valider filtres")
    except TimeoutError:
        print("  ⚠ Bouton Valider absent (filtres auto-appliqués).")
    page.wait_for_timeout(5000)

    print("\n[13] Screenshot final")
    page.screenshot(path="screenshot_itineraire_metro.png", full_page=True)
    snap(page, "13_final")
    print("  ✓ screenshot_itineraire_metro.png enregistré")

    print("\n✓ TEST RÉUSSI")
