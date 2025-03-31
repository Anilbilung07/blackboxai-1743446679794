import psycopg2
import requests
from bs4 import BeautifulSoup
import time
from typing import Optional, Dict, List
import logging

# Database connection configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'gamedb',
    'user': 'postgres',
    'password': 'postgres'
}

# API configuration
IGDB_API_URL = "https://api.igdb.com/v4/games"
STEAM_API_URL = "https://store.steampowered.com/api/appdetails"

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GameDataLoader:
    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor()
        
    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()

    def fetch_from_igdb(self, game_name: str) -> Optional[Dict]:
        """Fetch game data from IGDB API"""
        try:
            headers = {
                'Client-ID': 'YOUR_CLIENT_ID',
                'Authorization': 'Bearer YOUR_ACCESS_TOKEN'
            }
            query = f'search "{game_name}"; fields name, first_release_date, platforms.name, genres.name, rating;'
            response = requests.post(IGDB_API_URL, headers=headers, data=query)
            response.raise_for_status()
            return response.json()[0] if response.json() else None
        except Exception as e:
            logger.error(f"IGDB API error: {e}")
            return None

    def scrape_metacritic(self, game_name: str) -> Optional[Dict]:
        """Fallback to scraping Metacritic if API fails"""
        try:
            search_url = f"https://www.metacritic.com/search/game/{game_name}/results"
            headers = {'User-Agent': 'Mozilla/5.0'}
            
            response = requests.get(search_url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            first_result = soup.find('div', class_='result_wrap')
            if not first_result:
                return None
                
            game_url = first_result.find('a')['href']
            game_response = requests.get(f"https://www.metacritic.com{game_url}", headers=headers)
            game_soup = BeautifulSoup(game_response.text, 'html.parser')
            
            return {
                'title': game_soup.find('h1').text.strip(),
                'score': float(game_soup.find('span', itemprop='ratingValue').text),
                'user_score': float(game_soup.find('div', class_='metascore_w user').text),
                'platform': game_soup.find('span', class_='platform').text.strip(),
                'release_date': game_soup.find('span', class_='release_date').text.strip()
            }
        except Exception as e:
            logger.error(f"Metacritic scraping error: {e}")
            return None

    def insert_game_data(self, game_data: Dict) -> bool:
        """Insert game data into database"""
        try:
            # Check if developer exists or insert new
            self.cursor.execute(
                "INSERT INTO Developers (DeveloperName) VALUES (%s) ON CONFLICT DO NOTHING RETURNING DeveloperID",
                (game_data.get('developer'),)
            )
            developer_id = self.cursor.fetchone()[0] if self.cursor.rowcount > 0 else None

            # Similar checks for publisher, platform, genre
            # ... (omitted for brevity)

            # Insert game data
            self.cursor.execute("""
                INSERT INTO Games (
                    Title, ReleaseYear, DeveloperID, PublisherID, 
                    PlatformID, GenreID, MetacriticScore, UserScore, GlobalSales
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                game_data['title'],
                game_data.get('release_year'),
                developer_id,
                game_data.get('publisher_id'),
                game_data.get('platform_id'),
                game_data.get('genre_id'),
                game_data.get('metacritic_score'),
                game_data.get('user_score'),
                game_data.get('sales')
            ))
            
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Database insertion error: {e}")
            self.conn.rollback()
            return False

    def load_games(self, game_names: List[str]):
        """Main method to load multiple games"""
        for name in game_names:
            logger.info(f"Processing game: {name}")
            
            # Try API first
            game_data = self.fetch_from_igdb(name)
            
            # Fallback to scraping if API fails
            if not game_data:
                game_data = self.scrape_metacritic(name)
                if not game_data:
                    logger.warning(f"No data found for {name}")
                    continue
            
            # Process and insert data
            if not self.insert_game_data(game_data):
                logger.warning(f"Failed to insert data for {name}")
            
            # Rate limiting
            time.sleep(1)

if __name__ == "__main__":
    loader = GameDataLoader()
    games_to_load = [
        "The Legend of Zelda: Breath of the Wild",
        "Elden Ring",
        "God of War Ragnarök"
    ]
    loader.load_games(games_to_load)