"""
Collecteur de données des réseaux sociaux (Reddit, Twitter)
Reddit via PRAW est plus accessible que Twitter pour les données historiques
"""
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
import time
from loguru import logger
import json


class RedditCollector:
    """
    Collecteur de posts Reddit historiques
    Utilise PRAW (Python Reddit API Wrapper)
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        user_agent: str = "MarketAnomalyDetector/1.0",
        output_dir: str = "data/raw/social"
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent
        self.reddit = None

        # Initialiser la connexion si credentials fournis
        if client_id and client_secret:
            self._initialize_reddit()

    def _initialize_reddit(self):
        """Initialise la connexion Reddit"""
        try:
            import praw

            self.reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent
            )
            logger.info("✓ Connexion Reddit établie")
        except ImportError:
            logger.error("praw n'est pas installé. Installez avec: pip install praw")
        except Exception as e:
            logger.error(f"Erreur connexion Reddit: {str(e)}")

    def fetch_subreddit_posts(
        self,
        subreddit_name: str,
        keywords: List[str],
        limit: int = 1000,
        time_filter: str = "all"
    ) -> pd.DataFrame:
        """
        Récupère les posts d'un subreddit filtrés par mots-clés

        Args:
            subreddit_name: Nom du subreddit (ex: 'wallstreetbets')
            keywords: Liste de mots-clés/tickers à rechercher
            limit: Nombre max de posts
            time_filter: 'hour', 'day', 'week', 'month', 'year', 'all'

        Returns:
            DataFrame avec les posts
        """
        if not self.reddit:
            logger.warning("Reddit non initialisé. Utilisez des credentials valides.")
            return pd.DataFrame()

        try:
            logger.info(f"Collecte Reddit: r/{subreddit_name} - Keywords: {keywords[:3]}...")

            subreddit = self.reddit.subreddit(subreddit_name)
            posts_data = []

            # Rechercher par mots-clés
            for keyword in keywords:
                try:
                    search_results = subreddit.search(
                        keyword,
                        sort='relevance',
                        time_filter=time_filter,
                        limit=limit // len(keywords)
                    )

                    for post in search_results:
                        posts_data.append({
                            'id': post.id,
                            'title': post.title,
                            'text': post.selftext,
                            'author': str(post.author),
                            'created_utc': datetime.fromtimestamp(post.created_utc),
                            'score': post.score,
                            'upvote_ratio': post.upvote_ratio,
                            'num_comments': post.num_comments,
                            'subreddit': subreddit_name,
                            'url': post.url,
                            'keyword': keyword,
                            'permalink': f"https://reddit.com{post.permalink}"
                        })

                    time.sleep(0.5)  # Rate limiting

                except Exception as e:
                    logger.warning(f"Erreur recherche '{keyword}': {str(e)}")
                    continue

            if posts_data:
                df = pd.DataFrame(posts_data)
                df = df.drop_duplicates(subset=['id'])
                logger.success(f"✓ {len(df)} posts Reddit collectés de r/{subreddit_name}")
                return df
            else:
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"Erreur collecte Reddit: {str(e)}")
            return pd.DataFrame()

    def fetch_multiple_subreddits(
        self,
        subreddits: List[str],
        keywords: List[str],
        limit_per_subreddit: int = 500
    ) -> pd.DataFrame:
        """Collecte des posts de plusieurs subreddits"""
        all_posts = []

        for subreddit in subreddits:
            df = self.fetch_subreddit_posts(
                subreddit,
                keywords,
                limit=limit_per_subreddit
            )
            if not df.empty:
                all_posts.append(df)
            time.sleep(1)

        if all_posts:
            combined = pd.concat(all_posts, ignore_index=True)
            combined = combined.drop_duplicates(subset=['id'])
            logger.success(f"✓ Total: {len(combined)} posts Reddit uniques")

            # Sauvegarder
            self._save_data(combined, "reddit_posts_historical")
            return combined
        else:
            return pd.DataFrame()

    def fetch_top_posts_by_date_range(
        self,
        subreddit_name: str,
        start_date: datetime,
        end_date: datetime,
        keywords: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Récupère les top posts dans une période donnée
        Note: PRAW ne permet pas de filtrer directement par date,
        donc on récupère beaucoup et on filtre après
        """
        if not self.reddit:
            return pd.DataFrame()

        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            posts_data = []

            # Récupérer les top posts (plus de chances d'être pertinents)
            for post in subreddit.top(time_filter='all', limit=None):
                post_date = datetime.fromtimestamp(post.created_utc)

                # Filtrer par date
                if start_date <= post_date <= end_date:
                    # Filtrer par mots-clés si fournis
                    if keywords:
                        text_to_search = (post.title + ' ' + post.selftext).lower()
                        if not any(kw.lower() in text_to_search for kw in keywords):
                            continue

                    posts_data.append({
                        'id': post.id,
                        'title': post.title,
                        'text': post.selftext,
                        'author': str(post.author),
                        'created_utc': post_date,
                        'score': post.score,
                        'upvote_ratio': post.upvote_ratio,
                        'num_comments': post.num_comments,
                        'subreddit': subreddit_name,
                        'url': post.url,
                        'permalink': f"https://reddit.com{post.permalink}"
                    })

                # Arrêter si on dépasse la date de fin
                elif post_date < start_date:
                    break

            if posts_data:
                df = pd.DataFrame(posts_data)
                logger.success(f"✓ {len(df)} posts filtrés par date")
                return df
            else:
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"Erreur: {str(e)}")
            return pd.DataFrame()

    def _save_data(self, df: pd.DataFrame, filename: str):
        """Sauvegarde les données"""
        csv_path = self.output_dir / f"{filename}.csv"
        df.to_csv(csv_path, index=False)

        json_path = self.output_dir / f"{filename}.json"
        df.to_json(json_path, orient='records', date_format='iso')

        logger.debug(f"Données sauvegardées: {csv_path}")


class TwitterScraperCollector:
    """
    Collecteur de tweets historiques via scraping
    Alternative à Twitter API (qui est payant pour l'historique)

    Note: snscrape est une option mais peut être instable.
    Pour production, considérer:
    - Kaggle datasets de tweets financiers
    - Twitter Academic API (gratuit mais nécessite approbation)
    """

    def __init__(self, output_dir: str = "data/raw/social"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def fetch_tweets_snscrape(
        self,
        query: str,
        start_date: str,
        end_date: str,
        max_tweets: int = 1000
    ) -> pd.DataFrame:
        """
        Récupère des tweets via snscrape

        ATTENTION: snscrape peut être instable car Twitter bloque souvent
        """
        try:
            import snscrape.modules.twitter as sntwitter

            logger.info(f"Scraping Twitter: '{query}' de {start_date} à {end_date}")

            tweets_list = []
            search_query = f"{query} since:{start_date} until:{end_date}"

            # Scraper les tweets
            for i, tweet in enumerate(sntwitter.TwitterSearchScraper(search_query).get_items()):
                if i >= max_tweets:
                    break

                tweets_list.append({
                    'date': tweet.date,
                    'id': tweet.id,
                    'text': tweet.rawContent,
                    'user': tweet.user.username,
                    'retweet_count': tweet.retweetCount,
                    'like_count': tweet.likeCount,
                    'reply_count': tweet.replyCount,
                    'url': tweet.url,
                    'query': query
                })

            if tweets_list:
                df = pd.DataFrame(tweets_list)
                logger.success(f"✓ {len(df)} tweets scrapés pour '{query}'")
                return df
            else:
                logger.warning(f"Aucun tweet trouvé pour '{query}'")
                return pd.DataFrame()

        except ImportError:
            logger.error("snscrape non installé. Installez avec: pip install snscrape")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Erreur scraping Twitter: {str(e)}")
            logger.info("💡 Alternative: utilisez des datasets Kaggle de tweets financiers")
            return pd.DataFrame()

    def load_kaggle_dataset(self, dataset_path: str) -> pd.DataFrame:
        """
        Charge un dataset de tweets depuis Kaggle ou autre source

        Datasets recommandés sur Kaggle:
        - "Stock Market Tweets"
        - "Twitter Financial News"
        """
        try:
            df = pd.read_csv(dataset_path)
            logger.success(f"✓ Dataset chargé: {len(df)} tweets")
            return df
        except Exception as e:
            logger.error(f"Erreur chargement dataset: {str(e)}")
            return pd.DataFrame()


if __name__ == "__main__":
    # Test du collecteur Reddit
    from src.utils.logger import setup_logger
    import os

    setup_logger()

    # Test Reddit (nécessite credentials)
    client_id = os.getenv('REDDIT_CLIENT_ID')
    client_secret = os.getenv('REDDIT_CLIENT_SECRET')

    if client_id and client_secret:
        collector = RedditCollector(client_id, client_secret)

        df = collector.fetch_subreddit_posts(
            subreddit_name="wallstreetbets",
            keywords=["AAPL", "Tesla", "TSLA"],
            limit=50
        )

        if not df.empty:
            print("\nAperçu des posts Reddit:")
            print(df.head())
            print(f"\nTotal posts: {len(df)}")
    else:
        print("⚠️  Reddit credentials non configurés")
        print("Ajoutez REDDIT_CLIENT_ID et REDDIT_CLIENT_SECRET dans .env")
