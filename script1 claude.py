import re
import pytest
from playwright.sync_api import sync_playwright, TimeoutError

# ─────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────

@pytest.fixture(scope="session")
def browser_context():
    with sync_playwright() as p:
        context = p.chromium.launch(headless=False)
        yield context
        context.close()

@pytest.fixture
def page(browser_context):
    page = browser_context.new_page()
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
        print("Pas de popup cookies.")

def fill_field(page, input_id, suggestions_id, text):
    page.wait_for_timeout(1000)
    page.locator(f"input#{input_id}").fill(text)
    suggestions = page.locator(f"#{suggestions_id} li")
    suggestions.first.wait_for(state="visible", timeout=10000)
    suggestions.nth(1).click()
    print(f"Champ '{input_id}' rempli avec '{text}'.")

def swap(page):
    btn = page.locator('button[aria-label="Inverser départ et arrivée"]')
    btn.wait_for(state="visible", timeout=10000)
    btn.click()
    print("Départ/Arrivée inversés.")

def is_checked(page, transport_id):
    cb = page.locator(f"input#{transport_id}")
    return cb.count() > 0 and cb.is_checked()

def toggle(page, transport_id, name):
    label = page.locator(f"label[for='{transport_id}']")
    if label.count() > 0:
        label.click()
        page.wait_for_timeout(500)
        print(f"  {name} → {'activé' if is_checked(page, transport_id) else 'désactivé'}")

# ─────────────────────────────────────────
# TEST
# ─────────────────────────────────────────

def test_itineraire_metro_uniquement(page):
    page.goto("https://www.bonjour-ratp.fr/")

    # 1. Cookies
    accept_cookies(page)

    # 2. Remplir départ / arrivée
    fill_field(page, "departure", "departure-suggestions", "Republique")
    fill_field(page, "arrival",   "arrival-suggestions",   "Gare de Lyon")

    # 3. Double inversion
    swap(page)
    page.wait_for_timeout(500)
    swap(page)

    # 4. Cliquer sur le premier itinéraire proposé
    bouton_itineraire = page.locator(
        "#main > section.i119okux.bu9trog > div > div.idw1uie "
        "> div.i11clvn1 > div:nth-child(2) > div.b12h0ode.i8ngrdz > button"
    )
    bouton_itineraire.wait_for(state="visible", timeout=30000)
    bouton_itineraire.click()
    print("Itinéraire cliqué.")

    # 5. Ouvrir les stations intermédiaires
    stations_buttons = page.locator(
        'button[aria-controls="stations-list-expanded-content"][aria-expanded="false"]'
    )
    try:
        stations_buttons.first.wait_for(state="visible", timeout=10000)
        for i in range(stations_buttons.count()):
            stations_buttons.nth(i).click()
            page.wait_for_timeout(1000)
            print(f"Tronçon {i + 1} ouvert.")
    except TimeoutError:
        print("Aucun bouton de stations intermédiaires.")

    # 6. Retour à la vue principale
    for sel in ['div.r1ox9p09', 'button[aria-label="Retour à votre trajet"]', 'span.a1gdnitw']:
        chevron = page.locator(sel)
        if chevron.count() > 0 and chevron.is_visible():
            chevron.click()
            page.wait_for_timeout(1000)
            print(f"Retour via {sel}.")
            break

    # 7. Inverser départ / arrivée
    page.wait_for_timeout(2000)
    swap(page)

    # 8. Ouvrir les filtres → Mode de transport
    page.locator('button[aria-label="Accéder aux options de filtre"]').click()
    page.wait_for_timeout(2000)
    page.locator('button:has(span:has-text("Mode de transport"))').wait_for(state="visible", timeout=5000)
    page.locator('button:has(span:has-text("Mode de transport"))').click()
    page.wait_for_timeout(1000)
    print("Filtres ouverts.")

    # 9. Désactiver tout sauf METRO
    to_disable = ["RER", "TRANSILIEN", "BUS", "TRAM", "CABLE", "SELF_SERVICE_VEHICLE", "BICYCLE"]
    for t in to_disable:
        if is_checked(page, t):
            toggle(page, t, t)

    if not is_checked(page, "METRO"):
        toggle(page, "METRO", "METRO")

    print("Seul METRO est actif.")
    page.wait_for_timeout(1000)

    # 10. Valider les filtres
    valider = page.locator("button", has_text=re.compile("Voir les résultats", re.I))
    if valider.count() > 0 and valider.is_visible():
        valider.click()
    else:
        page.locator("button[type='submit']").click()
    print("Filtres validés.")

    # 11. Screenshot final
    page.wait_for_timeout(5000)
    page.screenshot(path="screenshot_itineraire_metro.png", full_page=True)
    print("Screenshot enregistré : screenshot_itineraire_metro.png")

    page.wait_for_timeout(3000)
    print("Test terminé.")
