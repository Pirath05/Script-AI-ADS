import re
import pytest
from playwright.sync_api import sync_playwright, expect


def test_footer_links():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context()
        page = context.new_page()

        # ─────────────────────────────────────────────
        # ÉTAPE 1 : Navigation vers la page d'accueil
        # ─────────────────────────────────────────────
        page.goto("https://www.bonjour-ratp.fr/")
        page.wait_for_load_state("networkidle")
        print("✅ Page d'accueil chargée")

        # ─────────────────────────────────────────────
        # ÉTAPE 2 : Accepter les cookies
        # ─────────────────────────────────────────────
        cookie_popup = page.locator("#didomi-popup")
        if cookie_popup.is_visible():
            accept_button = page.locator(
                "button", has_text=re.compile("accepter", re.I)
            )
            accept_button.first.click()
            cookie_popup.wait_for(state="hidden", timeout=5000)
            print("✅ Cookies acceptés")
        else:
            print("ℹ️ Pas de popup de cookies détecté")

        # ─────────────────────────────────────────────
        # ÉTAPE 3 : Défiler jusqu'en bas de la page
        # ─────────────────────────────────────────────
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1500)

        footer = page.locator("footer")
        footer.wait_for(state="visible", timeout=10000)
        footer.scroll_into_view_if_needed()
        page.wait_for_timeout(1000)
        print("✅ Défilement jusqu'au footer effectué")

        # ─────────────────────────────────────────────
        # ÉTAPE 4 : Cliquer sur le lien "Violences sexistes ou sexuelles"
        # ─────────────────────────────────────────────
        violences_link = page.locator(
            "a.l185tp5q", has_text="Violences sexistes ou sexuelles"
        )
        violences_link.wait_for(state="visible", timeout=10000)
        violences_link.scroll_into_view_if_needed()
        page.wait_for_timeout(500)

        # Vérification de la présence du lien avant le clic
        expect(violences_link).to_be_visible()
        expect(violences_link).to_have_text(
            re.compile("Violences sexistes ou sexuelles", re.I)
        )
        print("✅ Lien 'Violences sexistes ou sexuelles' trouvé et visible")

        violences_link.click()
        page.wait_for_load_state("networkidle")
        print("✅ Clic sur 'Violences sexistes ou sexuelles' effectué")

        # ─────────────────────────────────────────────
        # ÉTAPE 5 : Vérifier la navigation vers la page de contact
        # ─────────────────────────────────────────────
        expect(page).to_have_url(
            re.compile(r".*(contact|violences|signalement).*", re.I),
            timeout=10000
        )
        current_url_after_violences = page.url
        print(f"✅ Navigation vers la page de contact confirmée — URL : {current_url_after_violences}")

        # ─────────────────────────────────────────────
        # ÉTAPE 6 : Retourner à la page précédente
        # ─────────────────────────────────────────────
        page.go_back()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)

        expect(page).to_have_url(
            re.compile(r"https://www\.bonjour-ratp\.fr/?", re.I),
            timeout=10000
        )
        print(f"✅ Retour à la page d'accueil confirmé — URL : {page.url}")

        # ─────────────────────────────────────────────
        # ÉTAPE 7 : Défiler à nouveau jusqu'au footer
        # ─────────────────────────────────────────────
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1500)

        footer = page.locator("footer")
        footer.wait_for(state="visible", timeout=10000)
        footer.scroll_into_view_if_needed()
        page.wait_for_timeout(1000)
        print("✅ Défilement jusqu'au footer effectué à nouveau")

        # ─────────────────────────────────────────────
        # ÉTAPE 8 : Cliquer sur le lien "Mentions légales"
        # ─────────────────────────────────────────────
        mentions_link = page.locator(
            "footer a", has_text="Mentions légales"
        )
        mentions_link.wait_for(state="visible", timeout=10000)
        mentions_link.scroll_into_view_if_needed()
        page.wait_for_timeout(500)

        # Vérification de la présence du lien avant le clic
        expect(mentions_link).to_be_visible()
        expect(mentions_link).to_have_text(
            re.compile("Mentions légales", re.I)
        )
        print("✅ Lien 'Mentions légales' trouvé et visible")

        mentions_link.click()
        page.wait_for_load_state("networkidle")
        print("✅ Clic sur 'Mentions légales' effectué")

        # ─────────────────────────────────────────────
        # ÉTAPE 9 : Vérifier la navigation vers la page des mentions légales
        # ─────────────────────────────────────────────
        expect(page).to_have_url(
            re.compile(r".*(mentions.legales|legal).*", re.I),
            timeout=10000
        )
        print(f"✅ Navigation vers la page des mentions légales confirmée — URL : {page.url}")

        # ─────────────────────────────────────────────
        # ÉTAPE 10 : Vérifier le contenu de la page des mentions légales
        # ─────────────────────────────────────────────
        mentions_heading = page.locator(
            "h1, h2", has_text="Mentions légales"
        )
        mentions_heading.wait_for(state="visible", timeout=10000)
        expect(mentions_heading.first).to_be_visible()
        expect(mentions_heading.first).to_have_text(
            re.compile("Mentions légales", re.I)
        )
        print("✅ Titre 'Mentions légales' présent et visible sur la page")

        # ─────────────────────────────────────────────
        # ÉTAPE 11 : Vérification finale
        # ─────────────────────────────────────────────
        final_url = page.url
        print(f"✅ Test terminé avec succès — URL finale : {final_url}")

        # Fermeture du navigateur
        context.close()
        browser.close()


# ─────────────────────────────────────────────
# Point d'entrée principal
# ─────────────────────────────────────────────
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
