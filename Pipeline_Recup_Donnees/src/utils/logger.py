"""
Configuration du système de logging
"""
from loguru import logger
import sys
from pathlib import Path

def setup_logger(log_file="logs/pipeline.log", level="INFO"):
    """Configure le logger pour toute l'application"""

    # Créer le répertoire logs s'il n'existe pas
    Path("logs").mkdir(exist_ok=True)

    # Supprimer le handler par défaut
    logger.remove()

    # Ajouter un handler pour la console avec couleurs
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=level,
        colorize=True
    )

    # Ajouter un handler pour le fichier
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=level,
        rotation="10 MB",  # Rotation à 10MB
        retention="30 days",  # Garder les logs 30 jours
        compression="zip"  # Compresser les anciens logs
    )

    return logger
