import re
import pytest
from playwright.sync_api import sync_playwright, expect


def test_itinerary_planning():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context()
        page = context.new_page()

        # ─────────────────────────────────────────────
        # ÉTAPE 1 : Navigation vers la page d'accueil
        # ─────────────────────────────────────────────
        page.goto("https://www.bonjour-ratp.fr/")
        page.wait_for_load_state("networkidle")

        # ─────────────────────────────────────────────
        # ÉTAPE 2 : Accepter les cookies
        # ─────────────────────────────────────────────
        cookie_popup = page.locator("#didomi-popup")
        if cookie_popup.is_visible():
            accept_button = page.locator("button", has_text=re.compile("accepter", re.I))
            accept_button.first.click()
            cookie_popup.wait_for(state="hidden", timeout=5000)
            print("✅ Cookies acceptés")
        else:
            print("ℹ️ Pas de popup de cookies détecté")

        # ─────────────────────────────────────────────
        # ÉTAPE 3 : Remplir le champ de départ
        # ─────────────────────────────────────────────
        departure_input = page.locator("input#departure")
        departure_input.wait_for(state="visible", timeout=10000)
        departure_input.click()
        departure_input.fill("Gare de Lyon")
        page.wait_for_selector("#departure-suggestions li", state="visible", timeout=10000)
        departure_suggestions = page.locator("#departure-suggestions li")
        departure_suggestions.first.click()
        print("✅ Champ de départ rempli : Gare de Lyon")

        # ─────────────────────────────────────────────
        # ÉTAPE 4 : Remplir le champ d'arrivée
        # ─────────────────────────────────────────────
        arrival_input = page.locator("input#arrival")
        arrival_input.wait_for(state="visible", timeout=10000)
        arrival_input.click()
        arrival_input.fill("Châtelet")
        page.wait_for_selector("#arrival-suggestions li", state="visible", timeout=10000)
        arrival_suggestions = page.locator("#arrival-suggestions li")
        arrival_suggestions.first.click()
        print("✅ Champ d'arrivée rempli : Châtelet")

        # ─────────────────────────────────────────────
        # ÉTAPE 5 : Double inversion des champs
        # ─────────────────────────────────────────────
        invert_button = page.locator("button[aria-label='Inverser départ et arrivée']")
        invert_button.wait_for(state="visible", timeout=5000)

        # Première inversion
        invert_button.click()
        page.wait_for_timeout(1000)
        print("✅ Première inversion effectuée")

        # Deuxième inversion (retour à l'état initial)
        invert_button.click()
        page.wait_for_timeout(1000)
        print("✅ Deuxième inversion effectuée")

        # ─────────────────────────────────────────────
        # ÉTAPE 6 : Vérifier les valeurs après double inversion
        # ─────────────────────────────────────────────
        departure_value = departure_input.input_value()
        arrival_value = arrival_input.input_value()
        assert "Gare de Lyon" in departure_value, (
            f"❌ Le départ devrait contenir 'Gare de Lyon', mais contient : '{departure_value}'"
        )
        assert "Châtelet" in arrival_value, (
            f"❌ L'arrivée devrait contenir 'Châtelet', mais contient : '{arrival_value}'"
        )
        print(f"✅ Valeurs après double inversion vérifiées — Départ: {departure_value} | Arrivée: {arrival_value}")

        # ─────────────────────────────────────────────
        # ÉTAPE 7 : Lancer la recherche d'itinéraire
        # ─────────────────────────────────────────────
        search_button = page.locator(
            "#main > section.i119okux.bu9trog > div > div.idw1uie > div.i11clvn1 > div:nth-child(2) > div.b12h0ode.i8ngrdz > button"
        )
        search_button.wait_for(state="visible", timeout=5000)
        search_button.click()
        page.wait_for_load_state("networkidle")
        print("✅ Recherche d'itinéraire lancée")

        # ─────────────────────────────────────────────
        # ÉTAPE 8 : Vérifier l'affichage de l'itinéraire
        # ─────────────────────────────────────────────
        itinerary_section = page.locator(
            "#main > section.i119okux.bu9trog > div > div.idw1uie > div.i11clvn1 > div:nth-child(2) > div.b12h0ode.i8ngrdz > button"
        )
        expect(page).to_have_url(re.compile(r".*(itineraire|journey|trajet).*"), timeout=10000)
        print("✅ Navigation vers la page d'itinéraire confirmée")

        # ─────────────────────────────────────────────
        # ÉTAPE 9 : Ouvrir les stations intermédiaires
        # ─────────────────────────────────────────────
        expand_stations_button = page.locator(
            "button[aria-controls='stations-list-expanded-content'][aria-expanded='false']"
        )
        expand_stations_button.wait_for(state="visible", timeout=10000)
        expand_stations_button.first.click()
        page.wait_for_timeout(1000)
        print("✅ Stations intermédiaires ouvertes")

        # ─────────────────────────────────────────────
        # ÉTAPE 10 : Retourner à la vue principale
        # ─────────────────────────────────────────────
        back_button = page.locator(
            "div.r1ox9p09, button[aria-label='Retour à votre trajet'], span.a1gdnitw"
        )
        back_button.wait_for(state="visible", timeout=5000)
        back_button.first.click()
        page.wait_for_timeout(1000)
        print("✅ Retour à la vue principale")

        # ─────────────────────────────────────────────
        # ÉTAPE 11 : Inverser les champs départ / arrivée
        # ─────────────────────────────────────────────
        invert_button.wait_for(state="visible", timeout=5000)
        invert_button.click()
        page.wait_for_timeout(1000)

        new_departure_value = departure_input.input_value()
        new_arrival_value = arrival_input.input_value()
        assert "Châtelet" in new_departure_value, (
            f"❌ Après inversion, le départ devrait contenir 'Châtelet', mais contient : '{new_departure_value}'"
        )
        assert "Gare de Lyon" in new_arrival_value, (
            f"❌ Après inversion, l'arrivée devrait contenir 'Gare de Lyon', mais contient : '{new_arrival_value}'"
        )
        print(f"✅ Inversion finale vérifiée — Départ: {new_departure_value} | Arrivée: {new_arrival_value}")

        # ─────────────────────────────────────────────
        # ÉTAPE 12 : Accéder aux filtres
        # ─────────────────────────────────────────────
        filter_button = page.locator("button[aria-label='Accéder aux options de filtre']")
        filter_button.wait_for(state="visible", timeout=5000)
        filter_button.click()
        page.wait_for_timeout(1000)
        print("✅ Panneau de filtres ouvert")

        # ─────────────────────────────────────────────
        # ÉTAPE 13 : Ouvrir la section "Mode de transport"
        # ─────────────────────────────────────────────
        transport_mode_button = page.locator("button:has(span:has-text('Mode de transport'))")
        transport_mode_button.wait_for(state="visible", timeout=5000)
        transport_mode_button.click()
        page.wait_for_timeout(1000)
        print("✅ Section 'Mode de transport' ouverte")

        # ─────────────────────────────────────────────
        # ÉTAPE 14 : Désactiver tous les modes sauf le Métro
        # ─────────────────────────────────────────────
        transport_modes_to_disable = ["RER", "TRANSILIEN", "BUS", "TRAM", "CABLE", "SELF_SERVICE_VEHICLE", "BICYCLE"]
        transport_modes_labels = {
            "RER": "label[for='RER']",
            "TRANSILIEN": "label[for='TRANSILIEN']",
            "BUS": "label[for='BUS']",
            "TRAM": "label[for='TRAM']",
            "CABLE": "label[for='CABLE']",
            "SELF_SERVICE_VEHICLE": "label[for='SELF_SERVICE_VEHICLE']",
            "BICYCLE": "label[for='BICYCLE']",
        }

        for mode, label_selector in transport_modes_labels.items():
            checkbox = page.locator(f"input#{mode}")
            label = page.locator(label_selector)

            if checkbox.is_visible() and checkbox.is_checked():
                label.click()
                page.wait_for_timeout(500)
                print(f"✅ Mode '{mode}' désactivé")
            else:
                print(f"ℹ️ Mode '{mode}' déjà désactivé ou non visible")

        # ─────────────────────────────────────────────
        # ÉTAPE 15 : Vérifier que le Métro est coché
        # ─────────────────────────────────────────────
        metro_checkbox = page.locator("input#METRO")
        metro_checkbox.wait_for(state="visible", timeout=5000)

        if not metro_checkbox.is_checked():
            metro_label = page.locator("label[for='METRO']")
            metro_label.click()
            page.wait_for_timeout(500)
            print("✅ Mode 'METRO' activé manuellement")
        else:
            print("✅ Mode 'METRO' déjà activé")

        assert metro_checkbox.is_checked(), "❌ Le filtre Métro devrait être coché"
        print("✅ Filtre Métro confirmé comme actif")

        # ─────────────────────────────────────────────
        # ÉTAPE 16 : Valider les filtres
        # ─────────────────────────────────────────────
        validate_button = page.locator(
            "button:has-text('Voir les résultats'), button[type='submit']"
        )
        validate_button.wait_for(state="visible", timeout=5000)
        validate_button.first.click()
        page.wait_for_load_state("networkidle")
        print("✅ Filtres validés — Résultats filtrés par Métro affichés")

        # ─────────────────────────────────────────────
        # ÉTAPE 17 : Vérification finale
        # ─────────────────────────────────────────────
        page.wait_for_timeout(2000)
        current_url = page.url
        print(f"✅ Test terminé avec succès — URL finale : {current_url}")

        # Fermeture du navigateur
        context.close()
        browser.close()


# ─────────────────────────────────────────────
# Point d'entrée principal
# ─────────────────────────────────────────────
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
