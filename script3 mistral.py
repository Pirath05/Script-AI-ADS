import re
import pytest
from playwright.sync_api import sync_playwright, TimeoutError

@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        yield browser
        browser.close()

@pytest.fixture
def page(browser):
    page = browser.new_page()
    yield page
    page.close()

def test_footer_links(page):
    url_base = "https://www.bonjour-ratp.fr/"
    page.goto(url_base)

    try:
        page.wait_for_selector("#didomi-popup", timeout=5000)
        bouton_cookies = page.locator('button', has_text=re.compile("accepter", re.I))
        if bouton_cookies.count() > 0 and bouton_cookies.is_visible():
            bouton_cookies.first.click()
        page.wait_for_selector("#didomi-popup", state="detached", timeout=10000)
    except TimeoutError:
        pass

    page.evaluate("""() => {
        return new Promise(resolve => {
            let totalHeight = 0;
            const distance = 100;
            const timer = setInterval(() => {
                window.scrollBy(0, distance);
                totalHeight += distance;
                if (totalHeight >= document.body.scrollHeight) {
                    clearInterval(timer);
                    resolve();
                } else {
                    setTimeout(() => {}, 500);
                }
            }, 200);
        });
    }""")

    page.wait_for_timeout(2000)
    page.wait_for_load_state("load")

    footer = page.locator("footer")
    assert footer.count() > 0, "Footer non trouvé dans le DOM"
    footer.wait_for(state="visible", timeout=10000)
    assert footer.is_visible(), "Footer non visible"

    lien_violences = footer.locator("a.l185tp5q", has_text="Violences sexistes ou sexuelles")
    lien_violences.wait_for(state="visible", timeout=5000)

    if lien_violences.count() > 0:
        with page.expect_navigation():
            lien_violences.click()
        assert page.url == "https://www.bonjour-ratp.fr/aide-contact/?question=je-suis-victime-ou-temoin-d-une-agression"

    page.go_back()
    page.wait_for_load_state("load")
    page.wait_for_selector("footer", timeout=15000)

    footer = page.locator("footer")
    lien_mentions = footer.locator("a", has_text="Mentions légales")
    lien_mentions.wait_for(state="visible", timeout=10000)
    assert lien_mentions.count() > 0, "Lien 'Mentions légales' non trouvé"

    lien_mentions.click()
    page.wait_for_url("**/informations-legales/#mentions-legales", timeout=10000)
    assert "#mentions-legales" in page.url, f"Fragment #mentions-legales absent de l'URL : {page.url}"

    titre_mentions = page.locator("h1, h2", has_text="Mentions légales")
    titre_mentions.wait_for(state="visible", timeout=5000)
    assert titre_mentions.is_visible(), "Titre 'Mentions légales' non visible"
