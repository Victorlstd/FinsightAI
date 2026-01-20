"""
Chargement et gestion de la configuration
"""
import yaml
from pathlib import Path
from dotenv import load_dotenv
import os

class ConfigLoader:
    """Charge la configuration depuis YAML et variables d'environnement"""

    def __init__(self, config_path="config/config.yaml"):
        self.config_path = Path(config_path)
        load_dotenv()  # Charger les variables d'environnement depuis .env
        self.config = self._load_config()

    def _load_config(self):
        """Charge le fichier de configuration YAML"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # Remplacer les variables d'environnement
        config = self._replace_env_vars(config)
        return config

    def _replace_env_vars(self, obj):
        """Remplace les références ${VAR} par les variables d'environnement"""
        if isinstance(obj, dict):
            return {k: self._replace_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._replace_env_vars(item) for item in obj]
        elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
            env_var = obj[2:-1]
            return os.getenv(env_var, obj)
        return obj

    def get(self, key_path, default=None):
        """
        Récupère une valeur de configuration par chemin
        Ex: get('sources.news.gdelt.enabled')
        """
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default

        return value

    def get_tickers(self):
        """Retourne la liste des tickers à surveiller"""
        return self.config.get('tickers', [])

    def get_keywords(self):
        """Retourne tous les mots-clés de surveillance"""
        keywords = []
        kw_config = self.config.get('keywords', {})
        for category in kw_config.values():
            if isinstance(category, list):
                keywords.extend(category)
        return keywords

    def get_date_range(self):
        """Retourne la période de collecte (start_date, end_date)"""
        return (
            self.config.get('data_collection', {}).get('start_date'),
            self.config.get('data_collection', {}).get('end_date')
        )
