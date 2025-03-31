import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2
from analysis import GameDataAnalyzer
from typing import Dict, List
import logging

# Configure page
st.set_page_config(
    page_title="Game Data Dashboard",
    page_icon="🎮",
    layout="wide"
)

# Custom CSS for Tailwind-like styling
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
            
body {
    font-family: 'Inter', sans-serif;
}
            
.header {
    background-color: #1a1a2e;
    color: white;
    padding: 1rem;
    border-radius: 0.5rem;
    margin-bottom: 2rem;
}
            
.card {
    background-color: #f8f9fa;
    border-radius: 0.5rem;
    padding: 1rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    margin-bottom: 1rem;
}
            
.filter-section {
    background-color: #e9ecef;
    border-radius: 0.5rem;
    padding: 1rem;
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

class GameDashboard:
    def __init__(self):
        self.analyzer = GameDataAnalyzer()
        
    def create_header(self):
        """Create dashboard header section"""
        st.markdown("""
        <div class="header">
            <h1 style="margin:0;">🎮 Game Data Analytics Dashboard</h1>
            <p style="margin:0; opacity:0.8;">Explore trends in video game sales, scores, and genres</p>
        </div>
        """, unsafe_allow_html=True)
        
    def create_filters(self) -> Dict:
        """Create interactive filters"""
        st.markdown("""
        <div class="filter-section">
            <h3 style="margin-top:0;">🔍 Filters</h3>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            year_range = st.slider(
                "Release Year Range",
                1980, 2023, (2010, 2023),
                help="Filter games by release year range"
            )
            
        with col2:
            platforms = self._get_unique_values("Platforms", "PlatformName")
            selected_platforms = st.multiselect(
                "Platforms",
                platforms,
                default=platforms[:3],
                help="Select platforms to include"
            )
            
        with col3:
            genres = self._get_unique_values("Genres", "GenreName")
            selected_genres = st.multiselect(
                "Genres",
                genres,
                default=genres[:3],
                help="Select genres to include"
            )
            
        return {
            'year_range': year_range,
            'platforms': selected_platforms,
            'genres': selected_genres
        }
        
    def _get_unique_values(self, table: str, column: str) -> List:
        """Get unique values from database table"""
        query = f"SELECT DISTINCT {column} FROM {table} ORDER BY {column}"
        df = self.analyzer.query_to_dataframe(query)
        return df[column].tolist()
        
    def show_sales_analysis(self, filters: Dict):
        """Display sales analysis section"""
        st.markdown("""
        <div class="card">
            <h3 style="margin-top:0;">💰 Sales Analysis</h3>
        </div>
        """, unsafe_allow_html=True)
        
        query = f"""
        SELECT 
            p.PlatformName,
            g.ReleaseYear,
            SUM(g.GlobalSales) AS TotalSales
        FROM Games g
        JOIN Platforms p ON g.PlatformID = p.PlatformID
        JOIN Genres gn ON g.GenreID = gn.GenreID
        WHERE g.ReleaseYear BETWEEN {filters['year_range'][0]} AND {filters['year_range'][1]}
            AND p.PlatformName IN ({self._format_sql_list(filters['platforms'])})
            AND gn.GenreName IN ({self._format_sql_list(filters['genres'])})
        GROUP BY p.PlatformName, g.ReleaseYear
        ORDER BY g.ReleaseYear, TotalSales DESC
        """
        
        df = self.analyzer.query_to_dataframe(query)
        
        if not df.empty:
            tab1, tab2 = st.tabs(["Trend Chart", "Data Table"])
            
            with tab1:
                fig = px.line(
                    df,
                    x="ReleaseYear",
                    y="TotalSales",
                    color="PlatformName",
                    markers=True,
                    title="Game Sales by Platform Over Time",
                    labels={
                        "ReleaseYear": "Year",
                        "TotalSales": "Global Sales (Millions)",
                        "PlatformName": "Platform"
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
                
            with tab2:
                st.dataframe(
                    df.sort_values(["ReleaseYear", "TotalSales"], ascending=[True, False]),
                    hide_index=True,
                    use_container_width=True
                )
        else:
            st.warning("No data available for selected filters")
            
    def show_genre_analysis(self, filters: Dict):
        """Display genre analysis section"""
        st.markdown("""
        <div class="card">
            <h3 style="margin-top:0;">🎭 Genre Analysis</h3>
        </div>
        """, unsafe_allow_html=True)
        
        query = f"""
        SELECT 
            gn.GenreName,
            g.ReleaseYear,
            COUNT(*) AS GameCount,
            AVG(g.MetacriticScore) AS AvgCriticScore,
            AVG(g.UserScore) AS AvgUserScore
        FROM Games g
        JOIN Genres gn ON g.GenreID = gn.GenreID
        JOIN Platforms p ON g.PlatformID = p.PlatformID
        WHERE g.ReleaseYear BETWEEN {filters['year_range'][0]} AND {filters['year_range'][1]}
            AND p.PlatformName IN ({self._format_sql_list(filters['platforms'])})
            AND gn.GenreName IN ({self._format_sql_list(filters['genres'])})
        GROUP BY gn.GenreName, g.ReleaseYear
        HAVING COUNT(*) > 1
        ORDER BY g.ReleaseYear, GameCount DESC
        """
        
        df = self.analyzer.query_to_dataframe(query)
        
        if not df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                fig1 = px.bar(
                    df,
                    x="ReleaseYear",
                    y="GameCount",
                    color="GenreName",
                    title="Game Releases by Genre",
                    labels={
                        "ReleaseYear": "Year",
                        "GameCount": "Number of Games",
                        "GenreName": "Genre"
                    }
                )
                st.plotly_chart(fig1, use_container_width=True)
                
            with col2:
                fig2 = px.scatter(
                    df,
                    x="AvgCriticScore",
                    y="AvgUserScore",
                    color="GenreName",
                    size="GameCount",
                    hover_name="GenreName",
                    title="Critic vs User Scores by Genre",
                    labels={
                        "AvgCriticScore": "Metacritic Score",
                        "AvgUserScore": "User Score",
                        "GenreName": "Genre",
                        "GameCount": "Number of Games"
                    }
                )
                st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("No data available for selected filters")
            
    def _format_sql_list(self, items: List[str]) -> str:
        """Format list of strings for SQL IN clause"""
        return ", ".join([f"'{item}'" for item in items])
        
    def run(self):
        """Run the dashboard"""
        self.create_header()
        filters = self.create_filters()
        
        self.show_sales_analysis(filters)
        self.show_genre_analysis(filters)
        
        st.markdown("---")
        st.caption("Game Data Dashboard v1.0 | Data sources: IGDB, Metacritic, Steam")

if __name__ == "__main__":
    dashboard = GameDashboard()
    dashboard.run()