import re
import pytest
from playwright.sync_api import sync_playwright, TimeoutError

# -----------------------------
# FIXTURES PLAYWRIGHT
# -----------------------------

@pytest.fixture(scope="session")
def browser_context():
    print("\n[INFO] Lancement du navigateur…")
    with sync_playwright() as p:
        context = p.chromium.launch(headless=False)
        yield context
        print("[INFO] Fermeture du navigateur…")
        context.close()

@pytest.fixture
def page(browser_context):
    print("[INFO] Ouverture d'un nouvel onglet…")
    page = browser_context.new_page()
    yield page
    print("[INFO] Fermeture de l'onglet…")
    page.close()

# -----------------------------
# FONCTIONS UTILITAIRES
# -----------------------------

def accept_cookies(page):
    print("[STEP] Vérification du popup cookies…")
    try:
        page.wait_for_selector("#didomi-popup", timeout=5000)
        print("[ACTION] Popup détecté → clic sur 'Accepter'")
        page.get_by_role("button", name=re.compile("accepter", re.I)).click()
    except TimeoutError:
        print("[INFO] Aucun popup cookies détecté.")

def fill_autocomplete(page, input_selector, text):
    print(f"[STEP] Remplissage du champ {input_selector} avec '{text}'…")
    input_field = page.locator(input_selector)
    input_field.fill(text)

    print("[INFO] Attente des suggestions…")
    suggestion = page.locator("li", has_text=re.compile(text[:4], re.I))
    suggestion.first.wait_for(state="visible", timeout=10000)

    print("[ACTION] Clic sur la première suggestion.")
    suggestion.first.click()

def toggle_swap_twice(page):
    print("[STEP] Double inversion départ/arrivée…")
    swap_btn = page.get_by_role("button", name=re.compile("inverser", re.I))
    swap_btn.wait_for(state="visible", timeout=10000)

    print("[ACTION] Premier clic sur Inverser.")
    swap_btn.click()

    print("[ACTION] Deuxième clic sur Inverser.")
    swap_btn.click()

def open_filters(page):
    print("[STEP] Ouverture des filtres…")
    page.get_by_role("button", name=re.compile("options de filtre", re.I)).click()

    print("[ACTION] Ouverture du menu 'Mode de transport'.")
    page.get_by_role("button", name=re.compile("mode de transport", re.I)).click()

def set_transport(page, transport_id, enabled=True):
    checkbox = page.locator(f"input#{transport_id}")
    current_state = checkbox.is_checked()

    if current_state != enabled:
        print(f"[ACTION] Toggle du transport '{transport_id}' → {'ON' if enabled else 'OFF'}")
        page.locator(f"label[for='{transport_id}']").click()
    else:
        print(f"[INFO] Transport '{transport_id}' déjà dans l'état souhaité ({'ON' if enabled else 'OFF'}).")

# -----------------------------
# TEST PRINCIPAL
# -----------------------------

def test_itineraire_ma_position_republique_bus_uniquement(page):
    print("\n===== DÉBUT DU TEST ITINÉRAIRE =====")

    print("[STEP] Navigation vers bonjour-ratp.fr…")
    page.goto("https://www.bonjour-ratp.fr/")

    accept_cookies(page)

    fill_autocomplete(page, "input#departure", "Republique")
    fill_autocomplete(page, "input#arrival", "Gare de Lyon")

    toggle_swap_twice(page)

    print("[STEP] Recherche du bouton Itinéraire…")
    itineraire_btn = page.get_by_role("button", name=re.compile("itinéraire", re.I))
    itineraire_btn.wait_for(state="visible", timeout=20000)

    print("[ACTION] Clic sur Itinéraire.")
    itineraire_btn.click()

    print("[STEP] Tentative de dépliage des étapes…")
    try:
        stations = page.locator('button[aria-controls="stations-list-expanded-content"]')
        stations.first.wait_for(state="visible", timeout=5000)
        for btn in stations.all():
            print("[ACTION] Dépliage d'une étape.")
            btn.click()
    except TimeoutError:
        print("[INFO] Aucune étape dépliable détectée.")

    print("[STEP] Vérification du bouton Retour…")
    retour = page.get_by_role("button", name=re.compile("retour", re.I))
    if retour.count() > 0:
        print("[ACTION] Clic sur Retour au trajet.")
        retour.click()

    print("[STEP] Tentative de ré-inversion départ/arrivée…")
    try:
        page.get_by_role("button", name=re.compile("inverser", re.I)).click()
        print("[ACTION] Inversion effectuée.")
    except TimeoutError:
        print("[INFO] Bouton Inverser non trouvé.")

    open_filters(page)

    print("[STEP] Configuration des modes de transport…")
    transports = ["RER", "TRANSILIEN", "BUS", "TRAM", "CABLE", "SELF_SERVICE_VEHICLE", "BICYCLE"]
    for t in transports:
        set_transport(page, t, enabled=False)

    set_transport(page, "METRO", enabled=True)

    print("[STEP] Validation des filtres…")
    valider = page.get_by_role("button", name=re.compile("résultats|valider", re.I))
    valider.click()

    print("[STEP] Screenshot final…")
    page.screenshot(path="screenshot_itineraire_metro.png", full_page=True)

    print("===== FIN DU TEST ITINÉRAIRE =====\n")
