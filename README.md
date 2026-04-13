# AI-Generated Playwright Test Scripts — Bonjour RATP

> Scripts de tests fonctionnels générés par IA (Cloud & Local) dans le cadre d'une étude comparative sur l'automatisation QA assistée par intelligence artificielle.

---

## Note de confidentialité

Les scripts présents dans ce dépôt sont des **versions publiques anonymisées**.

Dans un souci de conformité et de sécurité interne à **RATP Smart Systems**, les éléments suivants ont été **modifiés ou supprimés** par rapport aux scripts originaux exécutés en préproduction :

- Les **URLs de préproduction** ont été remplacées par les URLs publiques de production (`https://www.bonjour-ratp.fr/`)
- Les **sélecteurs CSS et XPath spécifiques** à l'environnement de préproduction ont été adaptés ou remplacés par des sélecteurs génériques équivalents
- Les **classes CSS internes** non publiques ont été neutralisées avec des sélecteurs de fallback robustes
- Certains **éléments sensibles** (identifiants internes, paramètres d'environnement) ont été supprimés

---

## Contexte

Ce dépôt s'inscrit dans une étude comparative menée dans le cadre d'un mémoire de fin d'études portant sur l'**automatisation des tests QA par l'IA générative**.

L'objectif est d'évaluer et comparer plusieurs modèles IA (Cloud et Local) sur leur capacité à générer des scripts de tests Playwright fonctionnels, maintenables et conformes aux standards QA.

---

## Scénarios de tests

Trois scénarios fonctionnels représentatifs du site Bonjour RATP ont été sélectionnés :

| # | Scénario | Description |
|---|----------|-------------|
| 1 | `test_itineraire` | Recherche d'un itinéraire standard avec filtrage par mode de transport |
| 2 | `test_aeroports` | Vérification du parcours vers la page Aéroports (Paris Orly) |
| 3 | `test_footer_links` | Vérification des liens du footer (Violences, Mentions légales) |

---

## Modèles IA évalués

### Cloud
| Modèle | Stratégies |
|--------|-----------|
| Claude Sonnet 4.6 (Anthropic) | Zero-Shot & Few-Shot |
| ChatGPT (OpenAI) | Zero-Shot & Few-Shot |
| Mistral Codestral-2501 | Zero-Shot & Few-Shot |

### Local 
| Modèle | Environnement |
|--------|--------------|
| DeepSeek-R1 7B | Terminal — PC personnel |
| Claude Code | CLI — PC personnel |

### Cloud/Local
| Modèle | Environnement |
|--------|--------------|
| Github Copilot (Copilot) | Editeur — Online |
---

## Stack technique

- **Langage** : Python 3.11+
- **Framework** : [Playwright](https://playwright.dev/python/) (sync API)
- **Navigateur** : Chromium
- **Test runner** : pytest
- **Matériel** : Apple M1, 8 Go RAM

---

## Résultats par modèle et stratégie

| Modèle / Outil     | Scénario     | Stratégie | Succès (Fonctionnel) | Corrections | Conformité | Palier Temps |
|--------------------|--------------|-----------|----------------------|-------------|------------|--------------|
| ChatGPT Cloud      | Itinéraire   | Zero-Shot | ✅ 1                 | Faible      | 100%       | Palier 1     |
| ChatGPT Cloud      | Aéroport     | Zero-Shot | ❌ 0                 | Faible      | 100%       | Palier 1     |
| ChatGPT Cloud      | Footer       | Zero-Shot | ❌ 0                 | Faible      | 100%       | Palier 1     |
| ChatGPT Cloud      | Itinéraire   | Few-Shot  | ✅ 1                 | Faible      | 100%       | Palier 2     |
| ChatGPT Cloud      | Aéroport     | Few-Shot  | ✅ 1                 | Faible      | 100%       | Palier 2     |
| ChatGPT Cloud      | Footer       | Few-Shot  | ✅ 1                 | Faible      | 100%       | Palier 2     |
| Claude Cloud       | Itinéraire   | Zero-Shot | ✅ 1                 | Faible      | 100%       | Palier 2     |
| Claude Cloud       | Aéroport     | Zero-Shot | ❌ 0                 | Faible      | 100%       | Palier 2     |
| Claude Cloud       | Footer       | Zero-Shot | ✅ 1                 | Faible      | 100%       | Palier 2     |
| Claude Cloud       | Itinéraire   | Few-Shot  | ✅ 1                 | Faible      | 100%       | Palier 3     |
| Claude Cloud       | Aéroport     | Few-Shot  | ✅ 1                 | Faible      | 100%       | Palier 3     |
| Claude Cloud       | Footer       | Few-Shot  | ✅ 1                 | Faible      | 100%       | Palier 3     |
| Mistral Cloud      | (Tous)       | Zero-Shot | ❌ 0                 | Beaucoup    | 20%        | Palier 1     |
| Mistral Cloud      | (Tous)       | Few-Shot  | ✅ 1                 | Faible      | 100%       | Palier 2     |
| DeepSeek Local     | (Tous)       | N/A       | ✅ 1                 | Faible      | 100%       | Palier 2     |
| Claude Local       | (Tous)       | N/A       | ✅ 1                 | Faible      | 100%       | Palier 2     |
| GitHub Copilot     | (Tous)       | N/A       | ✅ 1                 | Faible      | 100%       | Palier 2     |

---

## Mentions

Ce projet est partagé à des fins académiques uniquement dans le cadre d'un mémoire de fin d'études. Toute réutilisation commerciale est interdite.
