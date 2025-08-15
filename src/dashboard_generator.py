"""
Dashboard Generator for OpenChatStudio Analytics
Generates HTML dashboard with charts and metrics
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd

from ocs_client import OCSClient
from models import Session, SessionStats, DashboardData
from data_utils import get_latest_sessions_dir, load_sessions_from_directory
import constants

class DashboardGenerator:
    """Generate HTML dashboard following Coverage project patterns"""
    
    def __init__(self, client: OCSClient, output_dir: Path):
        self.client = client
        self.output_dir = output_dir
        self.data = None
        
    def generate_dashboard(self) -> str:
        """Main method to generate complete dashboard"""
        print("📊 Fetching data from API...")
        self.data = self._fetch_all_data()
        
        print("📈 Generating charts...")
        charts = self._generate_all_charts()
        
        print("🏗️ Building HTML dashboard...")
        dashboard_html = self._build_html_dashboard(charts)
        
        # Write dashboard file
        dashboard_path = self.output_dir / "index.html"
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(dashboard_html)
            
        return str(dashboard_path)
    
    def _fetch_all_data(self) -> DashboardData:
        """Load all session data from local JSON files"""
        
        print("  • Loading sessions from local files...")
        
        sessions_dir = get_latest_sessions_dir()
        if not sessions_dir:
            raise Exception("No session data found. Please run download first.")
        
        print(f"  • Loading from: {sessions_dir}")
        sessions_data = load_sessions_from_directory(sessions_dir)
        
        # Convert to Session objects
        sessions = []
        for session_data in sessions_data:
            try:
                session = Session.from_api_data(session_data)
                sessions.append(session)
            except Exception as e:
                print(f"    Warning: Could not parse session {session_data.get('id', 'unknown')}: {e}")
        
        print(f"  • Loaded {len(sessions)} sessions")
        
        # Calculate session stats (though we don't have messages, we can still calculate basic stats)
        session_stats = []
        for session in sessions:
            stats = SessionStats.from_session(session)
            session_stats.append(stats)
        
        return DashboardData(
            sessions=sessions,
            session_stats=session_stats
        )
    
    def _generate_all_charts(self) -> Dict[str, str]:
        """Generate all dashboard charts based on available session data"""
        charts = {}
        
        # Key metrics summary
        charts['metrics_summary'] = self._generate_metrics_summary()
        
        # Sessions over time
        charts['sessions_over_time'] = self._generate_sessions_over_time_chart()
        
        # Experiments distribution
        charts['experiments_distribution'] = self._generate_experiments_distribution_chart()
        
        # Teams distribution  
        charts['teams_distribution'] = self._generate_teams_distribution_chart()
        
        return charts
    
    def _generate_metrics_summary(self) -> str:
        """Generate key metrics summary"""
        total_sessions = self.data.get_session_count()
        experiments = self.data.get_sessions_by_experiment()
        teams = set(session.team.name for session in self.data.sessions)
        
        # Find date range
        if self.data.sessions:
            dates = [session.created_at.date() for session in self.data.sessions]
            min_date = min(dates)
            max_date = max(dates)
            date_range = f"{min_date} to {max_date}"
        else:
            date_range = "No data"
        
        metrics_html = f"""
        <div class="metrics-grid">
            <div class="metric-card">
                <h3>Total Sessions</h3>
                <div class="metric-value">{total_sessions:,}</div>
            </div>
            <div class="metric-card">
                <h3>Experiments</h3>
                <div class="metric-value">{len(experiments)}</div>
            </div>
            <div class="metric-card">
                <h3>Teams</h3>
                <div class="metric-value">{len(teams)}</div>
            </div>
            <div class="metric-card">
                <h3>Date Range</h3>
                <div class="metric-value" style="font-size: 0.8em;">{date_range}</div>
            </div>
        </div>
        """
        return metrics_html
    
    def _generate_sessions_over_time_chart(self) -> str:
        """Generate sessions over time chart"""
        if not self.data.sessions:
            return "<p>No session data available</p>"
        
        # Group sessions by date
        session_dates = [session.created_at.date() for session in self.data.sessions]
        df = pd.DataFrame({'date': session_dates})
        daily_counts = df.groupby('date').size().reset_index(name='count')
        
        fig = px.line(
            daily_counts, 
            x='date', 
            y='count',
            title='Sessions Over Time',
            labels={'date': 'Date', 'count': 'Number of Sessions'}
        )
        fig.update_layout(height=constants.DEFAULT_CHART_HEIGHT)
        
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    def _generate_experiments_distribution_chart(self) -> str:
        """Generate experiments distribution chart"""
        if not self.data.sessions:
            return "<p>No session data available</p>"
        
        experiments = self.data.get_sessions_by_experiment()
        experiment_names = list(experiments.keys())
        session_counts = [len(sessions) for sessions in experiments.values()]
        
        fig = px.bar(
            x=session_counts,
            y=experiment_names,
            orientation='h',
            title='Sessions by Experiment',
            labels={'x': 'Number of Sessions', 'y': 'Experiment'}
        )
        fig.update_layout(height=max(400, len(experiment_names) * 30))
        
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    def _generate_teams_distribution_chart(self) -> str:
        """Generate teams distribution chart"""
        if not self.data.sessions:
            return "<p>No session data available</p>"
        
        # Count sessions by team
        team_counts = {}
        for session in self.data.sessions:
            team_name = session.team.name
            team_counts[team_name] = team_counts.get(team_name, 0) + 1
        
        fig = px.pie(
            values=list(team_counts.values()),
            names=list(team_counts.keys()),
            title='Sessions by Team'
        )
        fig.update_layout(height=constants.DEFAULT_CHART_HEIGHT)
        
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    def _generate_rating_distribution_chart(self) -> str:
        """Generate rating distribution chart"""
        if not self.data.ratings:
            return "<p>No rating data available</p>"
        
        ratings = [rating.rating for rating in self.data.ratings]
        fig = px.histogram(
            x=ratings,
            nbins=5,
            title='FLW Rating Distribution',
            labels={'x': 'Rating (1-5)', 'y': 'Number of Sessions'}
        )
        fig.update_layout(height=constants.DEFAULT_CHART_HEIGHT)
        
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    def _generate_word_count_histogram(self) -> str:
        """Generate word count histogram"""
        word_counts = self.data.get_human_word_counts()
        if not word_counts:
            return "<p>No message data available</p>"
        
        fig = px.histogram(
            x=word_counts,
            title='User Message Word Count Distribution',
            labels={'x': 'Words per Message', 'y': 'Number of Messages'}
        )
        fig.update_layout(height=constants.DEFAULT_CHART_HEIGHT)
        
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    def _generate_annotation_summary_chart(self) -> str:
        """Generate annotation summary chart"""
        if not self.data.annotations:
            return "<p>No annotation data available</p>"
        
        # Count annotations by type
        annotation_counts = {}
        for ann in self.data.annotations:
            annotation_counts[ann.annotation_type] = annotation_counts.get(ann.annotation_type, 0) + 1
        
        fig = px.bar(
            x=list(annotation_counts.keys()),
            y=list(annotation_counts.values()),
            title='Annotations by Type',
            labels={'x': 'Annotation Type', 'y': 'Count'}
        )
        fig.update_layout(height=constants.DEFAULT_CHART_HEIGHT)
        
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    def _generate_user_engagement_pie(self) -> str:
        """Generate user engagement pie chart"""
        engagement_data = [ann.user_engagement for ann in self.data.annotations if ann.user_engagement]
        if not engagement_data:
            return "<p>No user engagement data available</p>"
        
        engagement_counts = {}
        for engagement in engagement_data:
            engagement_counts[engagement] = engagement_counts.get(engagement, 0) + 1
        
        fig = px.pie(
            values=list(engagement_counts.values()),
            names=list(engagement_counts.keys()),
            title='User Engagement Distribution'
        )
        fig.update_layout(height=constants.DEFAULT_CHART_HEIGHT)
        
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    def _generate_user_knowledge_pie(self) -> str:
        """Generate user knowledge pie chart"""
        knowledge_data = [ann.user_knowledge for ann in self.data.annotations if ann.user_knowledge]
        if not knowledge_data:
            return "<p>No user knowledge data available</p>"
        
        knowledge_counts = {}
        for knowledge in knowledge_data:
            knowledge_counts[knowledge] = knowledge_counts.get(knowledge, 0) + 1
        
        fig = px.pie(
            values=list(knowledge_counts.values()),
            names=list(knowledge_counts.keys()),
            title='User Knowledge Distribution'
        )
        fig.update_layout(height=constants.DEFAULT_CHART_HEIGHT)
        
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    def _build_html_dashboard(self, charts: Dict[str, str]) -> str:
        """Build complete HTML dashboard"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenChatStudio Dashboard</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #333;
            margin-bottom: 10px;
        }}
        .header .subtitle {{
            color: #666;
            font-size: 14px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .metric-card h3 {{
            margin: 0 0 10px 0;
            color: #333;
            font-size: 14px;
            font-weight: 600;
        }}
        .metric-value {{
            font-size: 32px;
            font-weight: bold;
            color: #2563eb;
            margin-bottom: 5px;
        }}
        .metric-subtitle {{
            font-size: 12px;
            color: #666;
        }}
        .chart-container {{
            background: white;
            margin-bottom: 30px;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .chart-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 OpenChatStudio Dashboard</h1>
        <div class="subtitle">ECD Bot Performance Analytics • Generated {timestamp}</div>
    </div>
    
    {charts['metrics_summary']}
    
    <div class="chart-container">
        {charts['sessions_over_time']}
    </div>
    
    <div class="chart-grid">
        <div class="chart-container">
            {charts['experiments_distribution']}
        </div>
        <div class="chart-container">
            {charts['teams_distribution']}
        </div>
    </div>
    
    <div class="footer">
        Generated by OCSDashboardECD • OpenChatStudio Analytics
    </div>
</body>
</html>
        """
        return html

