"""
Système de stockage et gestion de la base de données
Support SQLite (simple) et PostgreSQL (production)
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from loguru import logger
import pandas as pd

Base = declarative_base()


# Modèles de données

class MarketData(Base):
    """Données financières de marché"""
    __tablename__ = 'market_data'

    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    return_pct = Column(Float)
    volatility_20d = Column(Float)
    volume_ratio = Column(Float)
    abnormal_move = Column(Boolean, default=False)

    __table_args__ = (
        Index('idx_ticker_date', 'ticker', 'date'),
    )


class NewsArticle(Base):
    """Articles de news"""
    __tablename__ = 'news_articles'

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False, index=True)
    title = Column(Text, nullable=False)
    text = Column(Text)
    url = Column(String(500), unique=True)
    source = Column(String(100))
    query = Column(String(50), index=True)  # Ticker/mot-clé associé
    language = Column(String(10))
    sentiment_score = Column(Float)  # Score de sentiment (-1 à 1)
    relevance_score = Column(Float)  # Score de pertinence (0 à 1)

    __table_args__ = (
        Index('idx_query_date', 'query', 'date'),
    )


class SocialPost(Base):
    """Posts de réseaux sociaux (Reddit, Twitter)"""
    __tablename__ = 'social_posts'

    id = Column(Integer, primary_key=True)
    platform = Column(String(20), nullable=False)  # reddit, twitter
    post_id = Column(String(100), unique=True)
    date = Column(DateTime, nullable=False, index=True)
    title = Column(Text)
    text = Column(Text)
    author = Column(String(100))
    url = Column(String(500))
    score = Column(Integer)  # Upvotes/likes
    num_comments = Column(Integer)
    keyword = Column(String(50), index=True)  # Ticker/mot-clé
    sentiment_score = Column(Float)

    __table_args__ = (
        Index('idx_keyword_date', 'keyword', 'date'),
    )


class MarketEvent(Base):
    """Événements de marché détectés (anomalies, mouvements significatifs)"""
    __tablename__ = 'market_events'

    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    event_type = Column(String(50))  # price_surge, volume_spike, volatility_spike
    magnitude = Column(Float)  # Ampleur du mouvement
    description = Column(Text)

    # Corrélations avec news/social
    num_news_24h = Column(Integer, default=0)
    num_social_24h = Column(Integer, default=0)
    avg_sentiment_news = Column(Float)
    avg_sentiment_social = Column(Float)


class DatabaseManager:
    """Gestionnaire de base de données"""

    def __init__(self, db_url: str = "sqlite:///data/market_data.db"):
        """
        Initialise la connexion à la base de données

        Args:
            db_url: URL de connexion SQLAlchemy
                - SQLite: "sqlite:///path/to/db.db"
                - PostgreSQL: "postgresql://user:pass@localhost:5432/dbname"
        """
        # Créer le répertoire si nécessaire (pour SQLite)
        if db_url.startswith("sqlite"):
            db_path = Path(db_url.replace("sqlite:///", ""))
            db_path.parent.mkdir(parents=True, exist_ok=True)

        self.engine = create_engine(db_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Créer toutes les tables
        Base.metadata.create_all(self.engine)
        logger.info(f"✓ Base de données initialisée: {db_url}")

    def get_session(self) -> Session:
        """Retourne une nouvelle session"""
        return self.SessionLocal()

    def save_market_data(self, df: pd.DataFrame):
        """Sauvegarde les données financières"""
        try:
            session = self.get_session()

            for _, row in df.iterrows():
                market_data = MarketData(
                    ticker=row.get('Ticker'),
                    date=row.name if isinstance(row.name, datetime) else pd.to_datetime(row.name),
                    open=row.get('Open'),
                    high=row.get('High'),
                    low=row.get('Low'),
                    close=row.get('Close'),
                    volume=row.get('Volume'),
                    return_pct=row.get('Return'),
                    volatility_20d=row.get('Volatility_20d'),
                    volume_ratio=row.get('Volume_Ratio'),
                    abnormal_move=row.get('Abnormal_Move', False)
                )
                session.merge(market_data)

            session.commit()
            logger.success(f"✓ {len(df)} lignes de market data sauvegardées")
        except Exception as e:
            session.rollback()
            logger.error(f"Erreur sauvegarde market data: {str(e)}")
        finally:
            session.close()

    def save_news(self, df: pd.DataFrame):
        """Sauvegarde les articles de news"""
        try:
            session = self.get_session()

            for _, row in df.iterrows():
                news = NewsArticle(
                    date=pd.to_datetime(row.get('date')),
                    title=row.get('title', ''),
                    text=row.get('text', ''),
                    url=row.get('url', ''),
                    source=row.get('source', ''),
                    query=row.get('query', ''),
                    language=row.get('language', 'en'),
                    sentiment_score=row.get('sentiment_score'),
                    relevance_score=row.get('relevance_score')
                )
                session.merge(news)

            session.commit()
            logger.success(f"✓ {len(df)} articles sauvegardés")
        except Exception as e:
            session.rollback()
            logger.error(f"Erreur sauvegarde news: {str(e)}")
        finally:
            session.close()

    def save_social_posts(self, df: pd.DataFrame, platform: str = "reddit"):
        """Sauvegarde les posts des réseaux sociaux"""
        try:
            session = self.get_session()

            for _, row in df.iterrows():
                post = SocialPost(
                    platform=platform,
                    post_id=row.get('id', ''),
                    date=pd.to_datetime(row.get('created_utc', row.get('date'))),
                    title=row.get('title', ''),
                    text=row.get('text', ''),
                    author=row.get('author', ''),
                    url=row.get('url', ''),
                    score=row.get('score', 0),
                    num_comments=row.get('num_comments', 0),
                    keyword=row.get('keyword', row.get('query', '')),
                    sentiment_score=row.get('sentiment_score')
                )
                session.merge(post)

            session.commit()
            logger.success(f"✓ {len(df)} posts {platform} sauvegardés")
        except Exception as e:
            session.rollback()
            logger.error(f"Erreur sauvegarde social posts: {str(e)}")
        finally:
            session.close()

    def get_market_data(
        self,
        ticker: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """Récupère les données de marché"""
        session = self.get_session()

        query = session.query(MarketData).filter(MarketData.ticker == ticker)

        if start_date:
            query = query.filter(MarketData.date >= start_date)
        if end_date:
            query = query.filter(MarketData.date <= end_date)

        results = query.all()
        session.close()

        if not results:
            return pd.DataFrame()

        data = [{
            'date': r.date,
            'ticker': r.ticker,
            'open': r.open,
            'high': r.high,
            'low': r.low,
            'close': r.close,
            'volume': r.volume,
            'return_pct': r.return_pct,
            'volatility_20d': r.volatility_20d,
            'abnormal_move': r.abnormal_move
        } for r in results]

        return pd.DataFrame(data)

    def get_news_by_date_range(
        self,
        query: str,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """Récupère les news dans une période"""
        session = self.get_session()

        results = session.query(NewsArticle).filter(
            NewsArticle.query == query,
            NewsArticle.date >= start_date,
            NewsArticle.date <= end_date
        ).all()

        session.close()

        if not results:
            return pd.DataFrame()

        data = [{
            'date': r.date,
            'title': r.title,
            'text': r.text,
            'source': r.source,
            'sentiment_score': r.sentiment_score
        } for r in results]

        return pd.DataFrame(data)

    def export_to_csv(self, output_dir: str = "data/processed"):
        """Exporte toutes les tables en CSV pour analyse"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        tables = {
            'market_data': MarketData,
            'news_articles': NewsArticle,
            'social_posts': SocialPost,
            'market_events': MarketEvent
        }

        for table_name, model in tables.items():
            try:
                df = pd.read_sql_table(table_name, self.engine)
                csv_path = output_path / f"{table_name}.csv"
                df.to_csv(csv_path, index=False)
                logger.info(f"✓ {table_name} exporté: {len(df)} lignes")
            except Exception as e:
                logger.warning(f"Erreur export {table_name}: {str(e)}")


if __name__ == "__main__":
    # Test de la base de données
    from src.utils.logger import setup_logger

    setup_logger()

    db = DatabaseManager()
    logger.info("Base de données créée avec succès!")
