import re
import pytest
from playwright.sync_api import sync_playwright, TimeoutError

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

def accept_cookies(page):
    try:
        page.wait_for_selector("#didomi-popup", timeout=5000)
        bouton_cookies = page.locator('button', has_text=re.compile("accepter", re.I))
        if bouton_cookies.count() > 0 and bouton_cookies.is_visible():
            bouton_cookies.first.click()
    except TimeoutError:
        pass

def fill_departure(page, text="République"):
    input_depart = page.locator("input#departure")
    input_depart.fill(text)
    suggestions_depart = page.locator("#departure-suggestions li")
    suggestions_depart.first.wait_for(state="visible", timeout=10000)
    suggestions_depart.nth(1).click()

def fill_arrival(page, text="Gare de Lyon"):
    input_arrivee = page.locator("input#arrival")
    input_arrivee.fill(text)
    suggestions_arrivee = page.locator("#arrival-suggestions li")
    suggestions_arrivee.first.wait_for(state="visible", timeout=10000)
    suggestions_arrivee.nth(1).click()

def toggle_swap_twice(page):
    inverser_button = page.locator('button[aria-label="Inverser départ et arrivée"]')
    inverser_button.wait_for(state="visible", timeout=10000)
    inverser_button.click()
    page.wait_for_timeout(500)
    inverser_button.click()

def test_itineraire_ma_position_republique_bus_uniquement(page):
    url = "https://www.bonjour-ratp.fr/"
    page.goto(url)

    accept_cookies(page)
    fill_departure(page, "Republique")
    fill_arrival(page, "Gare de Lyon")
    toggle_swap_twice(page)

    try:
        bouton_itineraire = page.locator(
            "#main > section.i119okux.bu9trog > div > div.idw1uie > div.i11clvn1 > div:nth-child(2) > div.b12h0ode.i8ngrdz > button")
        bouton_itineraire.wait_for(state="visible", timeout=30000)
        bouton_itineraire.click()
    except TimeoutError:
        assert False, "L'itinéraire n'a pas été trouvé."

    stations_buttons = page.locator('button[aria-controls="stations-list-expanded-content"][aria-expanded="false"]')
    try:
        stations_buttons.first.wait_for(state="visible", timeout=10000)
        for btn in stations_buttons.all():
            btn.click()
            page.wait_for_timeout(1000)
    except TimeoutError:
        pass

    chevron_selectors = [
        'div.r1ox9p09',
        'button[aria-label="Retour à votre trajet"]',
        'span.a1gdnitw',
    ]
    for sel in chevron_selectors:
        chevron = page.locator(sel)
        if chevron.count() > 0 and chevron.is_visible():
            chevron.click()
            page.wait_for_timeout(1000)
            break

    try:
        inverser_button = page.locator('button[aria-label="Inverser départ et arrivée"]')
        inverser_button.wait_for(state="visible", timeout=10000)
        inverser_button.click()
    except TimeoutError:
        try:
            inverser_button = page.locator('button[title*="Inverser"]')
            inverser_button.wait_for(state="visible", timeout=5000)
            inverser_button.click()
        except TimeoutError:
            pass

    filtre_button = page.locator('button[aria-label="Accéder aux options de filtre"]')
    filtre_button.click()
    page.wait_for_timeout(2000)

    try:
        mode_transport = page.locator('button:has(span:has-text("Mode de transport"))')
        mode_transport.wait_for(state="visible", timeout=5000)
        mode_transport.click()
    except TimeoutError:
        assert False, "Impossible de cliquer sur le bouton Mode de transport dans les filtres."

    def is_transport_enabled(transport_id):
        checkbox = page.locator(f"input#{transport_id}")
        return checkbox.is_checked()

    def toggle_transport(transport_id):
        transport_label = page.locator(f"label[for='{transport_id}']")
        if transport_label.count() > 0:
            transport_label.click()
            page.wait_for_timeout(500)

    transports_a_desactiver = [
        "RER", "TRANSILIEN", "BUS", "TRAM", "CABLE", "SELF_SERVICE_VEHICLE"
    ]

    for transport_id in transports_a_desactiver:
        if is_transport_enabled(transport_id):
            toggle_transport(transport_id)

    if is_transport_enabled("BICYCLE"):
        toggle_transport("BICYCLE")

    if not is_transport_enabled("METRO"):
        toggle_transport("METRO")

    try:
        valider_button = page.locator("button", has_text=re.compile("Voir les résultats", re.I))
        if valider_button.count() > 0 and valider_button.is_visible():
            valider_button.click()
        else:
            valider_button = page.locator("button[type='submit']")
            if valider_button.count() > 0 and valider_button.is_visible():
                valider_button.click()
            else:
                all_buttons = page.locator("button")
                for btn in all_buttons.all():
                    if "valider" in btn.inner_text().lower() or "résultats" in btn.inner_text().lower():
                        btn.click()
                        break
    except Exception as e:
        pass

    page.wait_for_timeout(5000)
    screenshot_path = "screenshot_itineraire_metro.png"
    page.screenshot(path=screenshot_path, full_page=True)
    page.wait_for_timeout(3000)
