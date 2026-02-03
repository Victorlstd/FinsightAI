"""
Classificateur de pertinence des news.
Convertit les scores numériques en catégories qualitatives.
"""


def classify_pertinence(score: float) -> dict:
    """
    Classifie un score de pertinence en catégorie qualitative.

    Système de classification basé sur la distribution réelle des scores :
    - Haute pertinence : 70-100 (corrélation forte et directe)
    - Pertinence moyenne : 45-69 (corrélation probable)
    - Faible pertinence : 10-44 (corrélation incertaine)

    Args:
        score: Score de pertinence (10-100)

    Returns:
        Dict avec 'label', 'class' (CSS), 'color', 'emoji'
    """
    score = float(score)

    if score >= 70:
        return {
            "label": "Haute pertinence",
            "class": "pertinence-high",
            "color": "#16c784",  # Vert (comme les gains dans le dashboard)
            "emoji": "🎯",
            "description": "Corrélation forte et directe avec l'anomalie"
        }
    elif score >= 45:
        return {
            "label": "Pertinence moyenne",
            "class": "pertinence-medium",
            "color": "#f39c12",  # Orange (comme Minor)
            "emoji": "📊",
            "description": "Corrélation probable avec l'anomalie"
        }
    else:
        return {
            "label": "Faible pertinence",
            "class": "pertinence-low",
            "color": "#95a5a6",  # Gris
            "emoji": "❓",
            "description": "Corrélation incertaine avec l'anomalie"
        }


def get_pertinence_badge_html(score: float, show_score: bool = True) -> str:
    """
    Génère un badge HTML pour afficher la pertinence.

    Args:
        score: Score de pertinence
        show_score: Afficher le score numérique à côté

    Returns:
        HTML du badge
    """
    pertinence = classify_pertinence(score)

    score_text = f" ({score:.0f}/100)" if show_score else ""

    return f"""
        <span class="pertinence-badge {pertinence['class']}"
              style="background-color: {pertinence['color']}; color: white;
                     padding: 5px 12px; border-radius: 15px; font-size: 0.9em;
                     font-weight: 600; display: inline-block;">
            {pertinence['emoji']} {pertinence['label']}{score_text}
        </span>
    """


def get_pertinence_stats(scores: list) -> dict:
    """
    Calcule les statistiques de distribution des pertinences.

    Args:
        scores: Liste des scores

    Returns:
        Dict avec comptage par catégorie
    """
    if not scores:
        return {
            "Haute pertinence": 0,
            "Pertinence moyenne": 0,
            "Faible pertinence": 0,
            "total": 0,
            "score_moyen": 0
        }

    high = sum(1 for s in scores if s >= 70)
    medium = sum(1 for s in scores if 45 <= s < 70)
    low = sum(1 for s in scores if s < 45)

    return {
        "Haute pertinence": high,
        "Pertinence moyenne": medium,
        "Faible pertinence": low,
        "total": len(scores),
        "score_moyen": sum(scores) / len(scores) if scores else 0
    }


# Exemples d'utilisation
if __name__ == "__main__":
    # Test du classificateur
    test_scores = [95, 75, 60, 50, 45, 30, 15]

    print("Tests de classification :")
    print("=" * 60)

    for score in test_scores:
        result = classify_pertinence(score)
        print(f"Score {score:3d}/100 → {result['emoji']} {result['label']}")
        print(f"              {result['description']}")
        print()

    # Test des statistiques
    all_scores = [95, 85, 75, 60, 55, 50, 48, 45, 40, 30, 25, 20]
    stats = get_pertinence_stats(all_scores)

    print("\nStatistiques de distribution :")
    print("=" * 60)
    print(f"🎯 Haute pertinence   : {stats['Haute pertinence']} ({stats['Haute pertinence']/stats['total']*100:.1f}%)")
    print(f"📊 Pertinence moyenne : {stats['Pertinence moyenne']} ({stats['Pertinence moyenne']/stats['total']*100:.1f}%)")
    print(f"❓ Faible pertinence  : {stats['Faible pertinence']} ({stats['Faible pertinence']/stats['total']*100:.1f}%)")
    print(f"📈 Score moyen        : {stats['score_moyen']:.1f}/100")
