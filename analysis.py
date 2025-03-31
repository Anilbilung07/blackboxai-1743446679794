import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List
import logging
import os

# Database connection configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'gamedb',
    'user': 'postgres',
    'password': 'postgres'
}

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GameDataAnalyzer:
    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        
    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()

    def query_to_dataframe(self, query: str) -> pd.DataFrame:
        """Execute SQL query and return results as DataFrame"""
        try:
            return pd.read_sql(query, self.conn)
        except Exception as e:
            logger.error(f"Database query error: {e}")
            raise

    def analyze_sales_trends(self) -> Dict:
        """Analyze sales trends by platform and year"""
        query = """
        SELECT 
            p.PlatformName,
            EXTRACT(YEAR FROM DATE_TRUNC('year', 
                   MAKE_DATE(g.ReleaseYear, 1, 1))) AS Year,
            SUM(g.GlobalSales) AS TotalSales
        FROM Games g
        JOIN Platforms p ON g.PlatformID = p.PlatformID
        WHERE g.ReleaseYear IS NOT NULL
        GROUP BY p.PlatformName, Year
        ORDER BY Year, TotalSales DESC
        """
        df = self.query_to_dataframe(query)
        
        # Generate visualization
        plt.figure(figsize=(12, 6))
        sns.lineplot(
            data=df,
            x='Year',
            y='TotalSales',
            hue='PlatformName',
            marker='o'
        )
        plt.title('Game Sales Trends by Platform and Year')
        plt.ylabel('Global Sales (Millions)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('sales_trends.png')
        plt.close()
        
        return {
            'data': df.to_dict('records'),
            'visualization': 'sales_trends.png'
        }

    def analyze_genre_popularity(self) -> Dict:
        """Analyze genre popularity over time"""
        query = """
        SELECT 
            gn.GenreName,
            EXTRACT(YEAR FROM DATE_TRUNC('year', 
                   MAKE_DATE(g.ReleaseYear, 1, 1))) AS Year,
            COUNT(*) AS GameCount,
            AVG(g.MetacriticScore) AS AvgScore
        FROM Games g
        JOIN Genres gn ON g.GenreID = gn.GenreID
        WHERE g.ReleaseYear IS NOT NULL
        GROUP BY gn.GenreName, Year
        HAVING COUNT(*) > 3
        ORDER BY Year, GameCount DESC
        """
        df = self.query_to_dataframe(query)
        
        # Pivot for heatmap
        pivot_df = df.pivot_table(
            index='GenreName',
            columns='Year',
            values='GameCount',
            fill_value=0
        )
        
        plt.figure(figsize=(12, 8))
        sns.heatmap(
            pivot_df,
            annot=True,
            fmt='g',
            cmap='YlGnBu',
            linewidths=.5
        )
        plt.title('Genre Popularity Over Time (Game Counts)')
        plt.tight_layout()
        plt.savefig('genre_popularity.png')
        plt.close()
        
        return {
            'data': df.to_dict('records'),
            'visualization': 'genre_popularity.png'
        }

    def analyze_score_correlation(self) -> Dict:
        """Analyze correlation between critic and user scores"""
        query = """
        SELECT 
            Title,
            MetacriticScore,
            UserScore,
            GlobalSales
        FROM Games
        WHERE MetacriticScore IS NOT NULL 
        AND UserScore IS NOT NULL
        """
        df = self.query_to_dataframe(query)
        
        # Calculate correlation
        correlation = df[['MetacriticScore', 'UserScore']].corr().iloc[0,1]
        
        # Generate visualization
        plt.figure(figsize=(10, 6))
        sns.regplot(
            data=df,
            x='MetacriticScore',
            y='UserScore',
            scatter_kws={'alpha':0.5}
        )
        plt.title(f'Critic vs User Scores (Correlation: {correlation:.2f})')
        plt.tight_layout()
        plt.savefig('score_correlation.png')
        plt.close()
        
        return {
            'correlation': correlation,
            'data': df.to_dict('records'),
            'visualization': 'score_correlation.png'
        }

    def export_analysis_results(self, output_dir: str = 'analysis_results'):
        """Run all analyses and export results"""
        os.makedirs(output_dir, exist_ok=True)
        
        analyses = {
            'sales_trends': self.analyze_sales_trends,
            'genre_popularity': self.analyze_genre_popularity,
            'score_correlation': self.analyze_score_correlation
        }
        
        results = {}
        for name, analysis_func in analyses.items():
            try:
                logger.info(f"Running analysis: {name}")
                results[name] = analysis_func()
                
                # Save data to CSV
                pd.DataFrame(results[name]['data']).to_csv(
                    f"{output_dir}/{name}.csv",
                    index=False
                )
                
            except Exception as e:
                logger.error(f"Error in {name} analysis: {e}")
                continue
                
        return results

if __name__ == "__main__":
    analyzer = GameDataAnalyzer()
    analysis_results = analyzer.export_analysis_results()
    
    print("Analysis completed. Results saved to:")
    for analysis_name, result in analysis_results.items():
        print(f"- {analysis_name}:")
        print(f"  Data: analysis_results/{analysis_name}.csv")
        print(f"  Visualization: {result['visualization']}")