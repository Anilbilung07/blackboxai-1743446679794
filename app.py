from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import pandas as pd
import joblib
import logging
from typing import Dict, Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'gamedb'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres')
}

# ML Model configuration
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'sales_predictor.pkl')

class DatabaseManager:
    """Handles all database operations"""
    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor()
        
    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()
    
    def get_developers(self) -> list:
        """Fetch all developers from database"""
        self.cursor.execute("SELECT DeveloperID, DeveloperName FROM Developers ORDER BY DeveloperName")
        return [{'id': row[0], 'name': row[1]} for row in self.cursor.fetchall()]
    
    def get_publishers(self) -> list:
        """Fetch all publishers from database"""
        self.cursor.execute("SELECT PublisherID, PublisherName FROM Publishers ORDER BY PublisherName")
        return [{'id': row[0], 'name': row[1]} for row in self.cursor.fetchall()]
    
    def get_platforms(self) -> list:
        """Fetch all platforms from database"""
        self.cursor.execute("SELECT PlatformID, PlatformName FROM Platforms ORDER BY PlatformName")
        return [{'id': row[0], 'name': row[1]} for row in self.cursor.fetchall()]
    
    def get_genres(self) -> list:
        """Fetch all genres from database"""
        self.cursor.execute("SELECT GenreID, GenreName FROM Genres ORDER BY GenreName")
        return [{'id': row[0], 'name': row[1]} for row in self.cursor.fetchall()]
    
    def insert_game(self, game_data: Dict) -> Optional[int]:
        """Insert new game record into database"""
        try:
            self.cursor.execute("""
                INSERT INTO Games (
                    Title, ReleaseYear, DeveloperID, PublisherID, 
                    PlatformID, GenreID, MetacriticScore, UserScore, GlobalSales
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING GameID
            """, (
                game_data['title'],
                game_data['release_year'],
                game_data.get('developer_id'),
                game_data.get('publisher_id'),
                game_data['platform_id'],
                game_data['genre_id'],
                game_data.get('metacritic_score'),
                game_data.get('user_score'),
                game_data.get('global_sales')
            ))
            game_id = self.cursor.fetchone()[0]
            self.conn.commit()
            return game_id
        except Exception as e:
            logger.error(f"Error inserting game: {e}")
            self.conn.rollback()
            return None

class PredictionModel:
    """Handles sales predictions using ML model"""
    def __init__(self, model_path: str):
        try:
            self.model = joblib.load(model_path)
            logger.info("ML model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load ML model: {e}")
            self.model = None
    
    def predict_sales(self, features: Dict) -> Dict:
        """Predict game sales based on input features"""
        if not self.model:
            return {'error': 'Model not available'}
        
        try:
            # Prepare feature vector
            feature_df = pd.DataFrame([features])
            
            # Make prediction
            prediction = self.model.predict(feature_df)[0]
            confidence = self.model.predict_proba(feature_df)[0]
            
            return {
                'prediction': float(prediction),
                'confidence': float(max(confidence)),
                'lower_bound': float(prediction * 0.85),
                'upper_bound': float(prediction * 1.15)
            }
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return {'error': str(e)}

# Initialize services
db_manager = DatabaseManager()
prediction_model = PredictionModel(MODEL_PATH)

# API Endpoints
@app.route('/api/developers', methods=['GET'])
def get_developers():
    return jsonify(db_manager.get_developers())

@app.route('/api/publishers', methods=['GET'])
def get_publishers():
    return jsonify(db_manager.get_publishers())

@app.route('/api/platforms', methods=['GET'])
def get_platforms():
    return jsonify(db_manager.get_platforms())

@app.route('/api/genres', methods=['GET'])
def get_genres():
    return jsonify(db_manager.get_genres())

@app.route('/api/games', methods=['POST'])
def add_game():
    data = request.get_json()
    
    required_fields = ['title', 'release_year', 'platform_id', 'genre_id']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    game_id = db_manager.insert_game(data)
    if game_id:
        return jsonify({'game_id': game_id}), 201
    return jsonify({'error': 'Failed to add game'}), 500

@app.route('/api/predict', methods=['POST'])
def predict_sales():
    data = request.get_json()
    
    required_fields = ['genre', 'platform', 'score']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    prediction = prediction_model.predict_sales(data)
    if 'error' in prediction:
        return jsonify(prediction), 500
    return jsonify(prediction)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
