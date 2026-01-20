
---

# 📈 Finsight AI : Moteur Intelligent d'Investissement & Détection d'Anomalies

**Finsight AI** est un système d'intelligence artificielle conçu pour démocratiser l'investissement personnalisé et sécuriser les portefeuilles face à la volatilité des marchés. Ce projet s'inscrit dans le cadre du Projet de Fin d'Études (PFE) du Master 2 Data & Intelligence Artificielle à l'ECE Paris.

---

## 🚀 Vision du Projet

Le projet repose sur trois piliers fondamentaux identifiés lors de notre étude de l'état de l'art:

1. 
**Performance** : Optimisation de l'allocation via l'apprentissage par renforcement (RL).


2. 
**Robustesse** : Détection multimodale d'anomalies de marché (signaux quantitatifs + analyse textuelle).


3. 
**Accessibilité** : Explicabilité en langage naturel des décisions d'investissement via des LLMs.



---

## 🛠 Architecture Technique

Le système intègre 5 modèles clés pour une analyse complète du marché :

1. 
**Prédiction de Prix** : Architecture hybride LSTM + Transformers pour réduire la variance des prédictions.


2. 
**Détection d'Anomalies Quantitatives** : Utilisation d'Isolation Forest et d'Autoencoders pour repérer les ruptures de volume et de prix.


3. 
**Analyse de News & Événements (NLP)** : Extraction de causalité via des graphes de connaissances et détection d'événements exogènes (crises, scandales).


4. 
**Recommandation & Allocation** : Utilisation de l'XAI pour justifier les choix strategiques et democratiser les conseils d'investissements.


---

## 👥 Équipe & Remerciements


**Institution** : ECE Paris - École d'Ingénieurs.



**Promotion** : Année académique 2025-2026.



**Majeure** : Data & Intelligence Artificielle.

---

Ce projet est une version 1.0 (Novembre 2025) de l'état de l'art de Finsight AI.

---


# 📘 Guide de Contribution Git

Bienvenue dans l'équipe ! Pour que nous puissions travailler ensemble sans "casser" le projet, nous suivons un processus précis.

**🚨 La Règle d'Or :** On ne travaille **JAMAIS** directement sur les branches `main` ou `release`. On crée toujours sa propre branche.

---

## 🔄 Comment ça marche ? (Vue d'ensemble)

Nous utilisons 3 types de branches :

1.  **`main` (ou master)** : 🏆 La version "Sacrée". C'est celle en production. Elle doit toujours être stable.
2.  **`release`** : 🧪 La zone de "Répétition Générale". C'est une copie de main où l'on teste tout avant de valider.
3.  **`feature/...`** : 🚧 Votre espace de travail. C'est ici que vous créez de nouvelles fonctionnalités.

### Le Cycle de Vie d'une tâche
```mermaid
    [Main] -->|Copie| (Release)

    [Release/v1.0.0] -->|Création branche| [prenom/dev] (Basile/dev)

    [Basile/dev] -->|Commit & Push|

    [Basile/dev] -->|Pull Request| [Release/v1.0.0]

    [Release/v1.0.0] -->|Tests OK ?| [Main]
    [Release/v1.0.0] -->|Tests KO ?| [Hotfix/v1.0.1]

    [Hotfix/v1.0.1] -->|Correction| Release
```


---

# 🚀 Guide de Contribution Git & Workflow

Ce guide explique comment contribuer au projet en suivant nos bonnes pratiques. Nous utilisons un flux de travail structuré pour garantir la stabilité du code.

## 📌 Notre Stratégie de Branches

* **`main` (ou `master`)** : Le code stable en production. On ne travaille **jamais** directement dessus.
* **`release`** : Branche de pré-production. On y regroupe les nouveautés pour les tester avant le déploiement final.
* **`feature/nom-de-la-tache` ou `prenom/dev`** : Branches temporaires pour développer une fonctionnalité ou corriger un bug.

---

## 🛠 Étape 1 : Créer sa branche de travail

Avant de coder, créez toujours une nouvelle branche à partir de `main`.

| **VS Code** | Cliquez sur le nom de la branche en bas à gauche > **Créer une branche à partir de...** > Sélectionnez **main**. |

---

## 💾 Étape 2 : Enregistrer son travail (Commit & Push)

Une fois vos modifications terminées :

### Via VS Code

1. Allez dans l'onglet **Source Control** (l'icône avec le 
2. Tapez un message de commit clair (ex: `feat: ajout du bouton de contact`).
3. Cliquez sur le bouton **Commit**

Une fois que vos differents commits ont ete effectues et que vous voulez ajouter votre travail sur le repos, cliquez sur **Sync Changes** (ou l'icône de nuage) pour envoyer sur GitHub (push).

---

## 🔃 Étape 3 : La Pull Request (PR) vers `release`

Une fois votre code en ligne, il faut l'envoyer vers la branche **`release`** pour les tests.

1. Allez sur GitHub, un bandeau jaune devrait proposer **"Compare & pull request"**.
2. **Important :** Changez la branche de destination (base). Par défaut c'est `main`, choisissez **`release`**.
3. Ajoutez vos collègues en "Reviewers".
4. Une fois validée par l'équipe, cliquez sur **"Merge pull request"**.

---

## 🧪 Étape 4 : Tests et passage en `main`

Le code est maintenant sur la branche `release`. C'est le moment de tester !

* **Si les tests sont OK ✅ :** On crée une nouvelle Pull Request de `release` vers `main`. C'est le déploiement final.
* **Si les tests échouent ❌ :** On ne touche plus à la branche de feature initiale. On crée un **Hotfix**.

---

## 🛠 Cas particulier : Le Hotfix (Correction urgente)

Si un bug est découvert sur la branche `release` ou `main`, on suit cette procédure :

1. **Création :** On crée une branche `hotfix/v1.x.x` (en augmentant le numéro de version).
2. **Correction :** On corrige le bug sur cette branche.
3. **Validation :** On fait une PR directement vers `main` (pour corriger vite) ET on pense à mettre à jour `release` pour que le bug ne revienne pas.

---

## 🚨 Les 3 Règles d'Or (Best Practices)

1. **Pull avant de Push :** Avant de commencer à travailler, faites toujours un `git pull` pour avoir la version la plus récente.
2. **Petits Commits :** Mieux vaut 10 petits commits clairs qu'un énorme commit "Modifications générales".
3. **Messages explicites :** Utilisez des préfixes comme :
* `feat:` pour une nouvelle fonctionnalité.
* `fix:` pour une correction de bug.
* `docs:` pour de la documentation.


---
