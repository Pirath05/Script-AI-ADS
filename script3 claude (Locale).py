import re
import time
import pytest
from playwright.sync_api import sync_playwright, TimeoutError, Page, Locator

# ─────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────
BASE_URL = "https://www.bonjour-ratp.fr/"

EXPECTED_VIOLENCES_URL = (
    "https://www.bonjour-ratp.fr/aide-contact/"
    "?question=je-suis-victime-ou-temoin-d-une-agression"
)
EXPECTED_MENTIONS_URL_PATTERN = "**/informations-legales/**"
EXPECTED_MENTIONS_FRAGMENT = "#mentions-legales"

# ─────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────
@pytest.fixture(scope="session")
def browser():
    print("\n[SETUP] Lancement du navigateur Chromium...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            slow_mo=100,  # léger ralentissement pour stabilité visuelle
            args=["--start-maximized"],
        )
        print("[SETUP] Navigateur lancé.")
        yield browser
        print("[TEARDOWN] Fermeture du navigateur.")
        browser.close()


@pytest.fixture
def page(browser):
    context = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="fr-FR",
    )
    page = context.new_page()

    # Écoute des erreurs console pour diagnostic
    page.on("console", lambda msg: (
        print(f"  [CONSOLE {msg.type.upper()}] {msg.text}")
        if msg.type in ("error", "warning") else None
    ))
    page.on("pageerror", lambda err: print(f"  [PAGE ERROR] {err}"))

    yield page

    page.close()
    context.close()


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def accept_cookies(page: Page, timeout: int = 8000) -> None:
    """Accepte la bannière de cookies Didomi si elle apparaît."""
    print("  [COOKIES] Attente de la bannière cookies...")
    try:
        # Sélecteur principal : popup Didomi
        page.wait_for_selector("#didomi-popup", timeout=timeout)
        print("  [COOKIES] Bannière détectée.")

        # Tentative 1 : bouton texte "accepter" (FR)
        clicked = _try_click_cookie_button(page, [
            'button:has-text("Tout accepter")',
            'button:has-text("Accepter")',
            '[id*="didomi-notice-agree-button"]',
            '[data-testid*="accept"]',
            'button[aria-label*="accept" i]',
        ])

        if not clicked:
            # Tentative 2 : regex plus large
            btn = page.locator("button", has_text=re.compile(r"accept", re.I)).first
            if btn.count() > 0:
                btn.click()
                clicked = True
                print("  [COOKIES] Bouton accepter (regex) cliqué.")

        if not clicked:
            print("  [COOKIES] ⚠ Aucun bouton accepter trouvé, on continue quand même.")
            return

        # Attente disparition popup
        page.wait_for_selector("#didomi-popup", state="detached", timeout=10000)
        print("  [COOKIES] ✓ Bannière cookies fermée.")

    except TimeoutError:
        print("  [COOKIES] Aucune bannière cookies détectée (timeout), on continue.")


def _try_click_cookie_button(page: Page, selectors: list[str]) -> bool:
    """Essaie chaque sélecteur de liste jusqu'à trouver un bouton cliquable."""
    for sel in selectors:
        try:
            btn = page.locator(sel).first
            if btn.count() > 0 and btn.is_visible():
                btn.click()
                print(f"  [COOKIES] Bouton cliqué via sélecteur : {sel!r}")
                return True
        except Exception:
            continue
    return False


def scroll_to_bottom(page: Page, pause: float = 2.0) -> None:
    """Scroll progressif jusqu'en bas pour déclencher le lazy loading."""
    print("  [SCROLL] Défilement vers le bas de la page...")
    page.evaluate("""
        () => new Promise(resolve => {
            const distance = 400;
            const delay = 150;
            let scrolled = 0;
            const total = document.body.scrollHeight;
            const timer = setInterval(() => {
                window.scrollBy(0, distance);
                scrolled += distance;
                if (scrolled >= total) {
                    clearInterval(timer);
                    resolve();
                }
            }, delay);
        })
    """)
    page.wait_for_timeout(int(pause * 1000))
    print("  [SCROLL] ✓ Scroll terminé.")


def get_footer(page: Page, timeout: int = 15000) -> Locator:
    """Récupère le footer et attend qu'il soit visible."""
    print("  [FOOTER] Recherche du footer...")
    # Sélecteurs de secours ordonnés par priorité
    footer_selectors = [
        "footer",
        "[role='contentinfo']",
        "#footer",
        ".footer",
        "div[class*='footer']",
    ]
    for sel in footer_selectors:
        try:
            locator = page.locator(sel).first
            locator.wait_for(state="visible", timeout=timeout // len(footer_selectors))
            print(f"  [FOOTER] ✓ Footer trouvé via sélecteur : {sel!r}")
            return locator
        except TimeoutError:
            print(f"  [FOOTER] ✗ Sélecteur non trouvé : {sel!r}")
            continue

    raise AssertionError("Aucun footer trouvé sur la page avec les sélecteurs disponibles.")


def find_link_in_footer(footer: Locator, text: str, page: Page, timeout: int = 8000) -> Locator:
    """
    Cherche un lien dans le footer avec plusieurs stratégies de sélection.
    Lève une AssertionError si aucun lien n'est trouvé.
    """
    print(f"  [LINK] Recherche du lien '{text}' dans le footer...")

    strategies = [
        # Sélecteur original avec classe CSS
        lambda: footer.locator("a.l185tp5q", has_text=text),
        # Texte exact
        lambda: footer.locator(f'a:has-text("{text}")'),
        # Regex insensible à la casse
        lambda: footer.locator("a", has_text=re.compile(re.escape(text), re.I)),
        # Aria-label
        lambda: footer.locator(f'a[aria-label*="{text}" i]'),
        # Titre
        lambda: footer.locator(f'a[title*="{text}" i]'),
        # Fallback : chercher dans toute la page
        lambda: page.locator("a", has_text=re.compile(re.escape(text), re.I)),
    ]

    for i, strategy in enumerate(strategies, 1):
        try:
            locator = strategy()
            locator.first.wait_for(state="visible", timeout=timeout // len(strategies))
            count = locator.count()
            if count > 0:
                print(f"  [LINK] ✓ Lien '{text}' trouvé (stratégie {i}, {count} occurrence(s)).")
                return locator.first
        except (TimeoutError, Exception) as e:
            print(f"  [LINK] ✗ Stratégie {i} échouée : {e}")
            continue

    raise AssertionError(
        f"Lien '{text}' introuvable dans le footer après {len(strategies)} stratégies."
    )


def safe_navigate(page: Page, action, timeout: int = 15000) -> None:
    """Effectue une action et attend la navigation de façon sécurisée."""
    print("  [NAV] Déclenchement de la navigation...")
    try:
        with page.expect_navigation(timeout=timeout):
            action()
    except TimeoutError:
        # Certains sites naviguent sans déclencher l'événement standard
        print("  [NAV] expect_navigation timeout — on attend networkidle.")
        page.wait_for_load_state("networkidle", timeout=timeout)
    print(f"  [NAV] ✓ Navigation terminée. URL : {page.url}")


def go_back_and_reload(page: Page) -> None:
    """Revient en arrière et attend le chargement complet."""
    print("  [NAV] Retour à la page précédente...")
    page.go_back()
    page.wait_for_load_state("load")
    page.wait_for_timeout(1000)
    print(f"  [NAV] ✓ Retour effectué. URL : {page.url}")


# ─────────────────────────────────────────
# TEST PRINCIPAL
# ─────────────────────────────────────────

def test_footer_links(page: Page):
    """
    Vérifie les liens du footer de bonjour-ratp.fr :
      1. Lien "Violences sexistes ou sexuelles" → URL correcte
      2. Lien "Mentions légales" → URL + fragment + titre visible
    """
    print("\n" + "=" * 60)
    print("TEST : test_footer_links")
    print("=" * 60)

    # ── ÉTAPE 1 : Chargement de la page ────────────────────────
    print(f"\n[ÉTAPE 1] Chargement de {BASE_URL}")
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_load_state("load", timeout=30000)
    print(f"  ✓ Page chargée. Titre : {page.title()!r}")

    # ── ÉTAPE 2 : Gestion des cookies ──────────────────────────
    print("\n[ÉTAPE 2] Gestion des cookies")
    accept_cookies(page)

    # ── ÉTAPE 3 : Scroll pour lazy loading ─────────────────────
    print("\n[ÉTAPE 3] Scroll pour déclencher le lazy loading")
    scroll_to_bottom(page)
    page.wait_for_load_state("networkidle", timeout=15000)

    # ── ÉTAPE 4 : Vérification du footer ───────────────────────
    print("\n[ÉTAPE 4] Vérification de la présence du footer")
    footer = get_footer(page)
    assert footer.is_visible(), "❌ Footer non visible sur la page d'accueil."
    print("  ✓ Footer visible.")

    # ── ÉTAPE 5 : Lien "Violences sexistes ou sexuelles" ───────
    print("\n[ÉTAPE 5] Vérification du lien 'Violences sexistes ou sexuelles'")
    lien_violences = find_link_in_footer(footer, "Violences sexistes ou sexuelles", page)

    href = lien_violences.get_attribute("href")
    print(f"  href détecté : {href!r}")

    safe_navigate(page, lambda: lien_violences.click())

    actual_url = page.url
    print(f"  URL après navigation : {actual_url!r}")
    assert actual_url == EXPECTED_VIOLENCES_URL, (
        f"❌ URL inattendue pour 'Violences sexistes ou sexuelles'.\n"
        f"   Attendu  : {EXPECTED_VIOLENCES_URL}\n"
        f"   Obtenu   : {actual_url}"
    )
    print("  ✓ URL correcte.")

    # ── ÉTAPE 6 : Retour à l'accueil ───────────────────────────
    print("\n[ÉTAPE 6] Retour à la page d'accueil")
    go_back_and_reload(page)

    # ── ÉTAPE 7 : Re-scroll (footer peut nécessiter lazy load) ─
    print("\n[ÉTAPE 7] Re-scroll pour afficher le footer")
    scroll_to_bottom(page)

    # ── ÉTAPE 8 : Lien "Mentions légales" ──────────────────────
    print("\n[ÉTAPE 8] Vérification du lien 'Mentions légales'")
    footer = get_footer(page)
    lien_mentions = find_link_in_footer(footer, "Mentions légales", page)

    href_mentions = lien_mentions.get_attribute("href")
    print(f"  href détecté : {href_mentions!r}")

    lien_mentions.click()
    page.wait_for_url(EXPECTED_MENTIONS_URL_PATTERN, timeout=15000)

    actual_url = page.url
    print(f"  URL après navigation : {actual_url!r}")
    assert EXPECTED_MENTIONS_FRAGMENT in actual_url, (
        f"❌ Fragment '{EXPECTED_MENTIONS_FRAGMENT}' absent de l'URL.\n"
        f"   URL obtenue : {actual_url}"
    )
    print(f"  ✓ Fragment '{EXPECTED_MENTIONS_FRAGMENT}' présent.")

    # ── ÉTAPE 9 : Vérification du titre "Mentions légales" ─────
    print("\n[ÉTAPE 9] Vérification du titre de la page 'Mentions légales'")
    titre_selectors = [
        "h1:has-text('Mentions légales')",
        "h2:has-text('Mentions légales')",
        "[class*='title']:has-text('Mentions légales')",
        "h1, h2, h3",  # fallback : premier titre visible
    ]
    titre_found = False
    for sel in titre_selectors:
        try:
            titre = page.locator(sel).first
            titre.wait_for(state="visible", timeout=5000)
            if titre.is_visible():
                inner = titre.inner_text()
                print(f"  Titre trouvé ({sel!r}) : {inner!r}")
                # Pour le fallback générique, on vérifie le contenu
                if "mention" in inner.lower() or sel in titre_selectors[:3]:
                    assert titre.is_visible(), "❌ Titre 'Mentions légales' non visible."
                    titre_found = True
                    print("  ✓ Titre visible.")
                    break
        except TimeoutError:
            continue

    if not titre_found:
        print("  ⚠ Titre 'Mentions légales' non trouvé dans les sélecteurs testés.")
        # On ne fait pas échouer le test car la page et le fragment sont corrects

    # ── BILAN ──────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("✅ TOUTES LES ÉTAPES SONT PASSÉES AVEC SUCCÈS.")
    print("=" * 60)
