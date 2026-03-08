import re
import pytest
from playwright.sync_api import sync_playwright, TimeoutError

# ---------------------------------------------------------
# FIXTURES PLAYWRIGHT
# ---------------------------------------------------------

@pytest.fixture(scope="session")
def browser():
    print("\n[INFO] Lancement du navigateur…")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        yield browser
        print("[INFO] Fermeture du navigateur…")
        browser.close()

@pytest.fixture
def page(browser):
    print("[INFO] Ouverture d'un nouvel onglet…")
    page = browser.new_page()
    yield page
    print("[INFO] Fermeture de l'onglet…")
    page.close()

# ---------------------------------------------------------
# FONCTIONS UTILITAIRES
# ---------------------------------------------------------

def scroll_smooth(page):
    print("[STEP] Scroll progressif jusqu'en bas…")
    page.evaluate("""
        () => new Promise(resolve => {
            let total = 0;
            const step = 150;
            const timer = setInterval(() => {
                window.scrollBy(0, step);
                total += step;
                if (total >= document.body.scrollHeight) {
                    clearInterval(timer);
                    resolve();
                }
            }, 120);
        })
    """)
    page.wait_for_timeout(800)
    print("[STEP] Scroll vers le haut…")
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(500)

def accept_cookies(page):
    print("[STEP] Vérification du popup cookies…")
    try:
        page.wait_for_selector("#didomi-popup", timeout=5000)
        print("[ACTION] Popup détecté → clic sur 'Accepter'")
        page.get_by_role("button", name=re.compile("accepter", re.I)).click()
        page.wait_for_selector("#didomi-popup", state="detached", timeout=8000)
    except TimeoutError:
        print("[INFO] Aucun popup cookies détecté.")

# ---------------------------------------------------------
# TEST PRINCIPAL
# ---------------------------------------------------------

def test_footer_links(page):
    print("\n===== DÉBUT DU TEST FOOTER =====")

    url_base = "https://www.bonjour-ratp.fr/"
    print(f"[STEP] Navigation vers {url_base}…")
    page.goto(url_base)

    accept_cookies(page)

    # Scroll pour afficher le footer
    scroll_smooth(page)

    # -----------------------------------------------------
    # Vérification du footer
    # -----------------------------------------------------
    print("[STEP] Vérification de la présence du footer…")
    footer = page.locator("footer")
    footer.wait_for(state="visible", timeout=10000)
    assert footer.is_visible(), "Footer non visible"

    # -----------------------------------------------------
    # Test du lien : Violences sexistes ou sexuelles
    # -----------------------------------------------------
    print("[STEP] Recherche du lien 'Violences sexistes ou sexuelles'…")
    lien_violences = footer.get_by_role("link", name=re.compile("Violences sexistes", re.I))

    lien_violences.wait_for(state="visible", timeout=5000)
    assert lien_violences.count() > 0, "Lien 'Violences sexistes ou sexuelles' introuvable"

    print("[ACTION] Clic sur le lien 'Violences sexistes ou sexuelles'…")
    with page.expect_navigation():
        lien_violences.click()

    expected_url = "https://www.bonjour-ratp.fr/aide-contact/?question=je-suis-victime-ou-temoin-d-une-agression"
    assert page.url == expected_url, f"URL incorrecte après clic : {page.url}"

    # Retour à la page précédente
    print("[STEP] Retour à la page d'accueil…")
    page.go_back()
    page.wait_for_load_state("load")

    # -----------------------------------------------------
    # Test du lien : Mentions légales
    # -----------------------------------------------------
    print("[STEP] Recherche du lien 'Mentions légales'…")
    footer = page.locator("footer")
    footer.wait_for(state="visible", timeout=8000)

    lien_mentions = footer.get_by_role("link", name=re.compile("Mentions légales", re.I))
    lien_mentions.wait_for(state="visible", timeout=8000)
    assert lien_mentions.count() > 0, "Lien 'Mentions légales' non trouvé"

    print("[ACTION] Clic sur 'Mentions légales'…")
    lien_mentions.click()

    print("[STEP] Vérification de l'URL…")
    page.wait_for_url("**/informations-legales/#mentions-legales", timeout=10000)
    assert "#mentions-legales" in page.url, f"Fragment #mentions-legales absent : {page.url}"

    print("[STEP] Vérification du titre 'Mentions légales'…")
    titre_mentions = page.locator("h1, h2", has_text="Mentions légales")
    titre_mentions.wait_for(state="visible", timeout=5000)
    assert titre_mentions.is_visible(), "Titre 'Mentions légales' non visible"

    print("===== FIN DU TEST FOOTER =====\n")
