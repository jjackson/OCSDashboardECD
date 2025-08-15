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
from data_utils import get_latest_sessions_dir, load_sessions_from_directory, load_sessions_with_messages
from metrics_calculator import MetricsCalculator
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
        """Load all session data and messages from local JSON files"""
        
        print("  • Loading sessions and messages from local files...")
        
        # Load both sessions and messages
        raw_sessions, raw_messages = load_sessions_with_messages()
        
        if not raw_sessions:
            raise Exception("No session data found. Please run 'download-sessions' first.")
        
        print(f"  • Loaded {len(raw_sessions)} sessions")
        print(f"  • Loaded {len(raw_messages)} message files")
        
        # Initialize metrics calculator
        self.metrics_calculator = MetricsCalculator(raw_sessions, raw_messages)
        
        # Convert to Session objects
        sessions = []
        for session_data in raw_sessions:
            try:
                session = Session.from_api_data(session_data)
                sessions.append(session)
            except Exception as e:
                print(f"    Warning: Could not parse session {session_data.get('id', 'unknown')}: {e}")
        
        # Calculate session stats using the metrics calculator
        session_stats = []
        for session in sessions:
            stats = SessionStats.from_session(session)
            session_stats.append(stats)
        
        return DashboardData(
            sessions=sessions,
            session_stats=session_stats
        )
    
    def _generate_all_charts(self) -> Dict[str, str]:
        """Generate dashboard components - just filters and metrics cards for now"""
        charts = {}
        
        # Filters UI
        charts['filters_ui'] = self._generate_filters_ui()
        
        # Key metrics summary
        charts['metrics_summary'] = self._generate_metrics_summary()
        
        return charts
    
    def _generate_metrics_summary(self) -> str:
        """Generate advanced metrics summary with card-based layout"""
        if not hasattr(self, 'metrics_calculator') or not self.metrics_calculator:
            return self._generate_basic_metrics_summary()
        
        # Get all metrics
        all_metrics = self.metrics_calculator.calculate_all_metrics()
        basic_stats = all_metrics['basic_stats']
        message_stats = all_metrics['message_stats']
        sentiment_stats = all_metrics['sentiment_stats']
        annotation_stats = all_metrics['annotation_stats']
        coaching_quality = all_metrics['coaching_quality']
        
        # Generate card-based metrics layout
        metrics_html = f"""
        <div class="metrics-grid">
            <!-- Basic Stats Row -->
            <div class="metric-card primary">
                <div class="metric-icon">📊</div>
                <div class="metric-content">
                    <h3>Total Sessions</h3>
                    <div class="metric-value">{basic_stats['total_sessions']:,}</div>
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-icon">🧪</div>
                <div class="metric-content">
                    <h3>Experiments</h3>
                    <div class="metric-value">{basic_stats['experiments_count']}</div>
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-icon">👥</div>
                <div class="metric-content">
                    <h3>Teams</h3>
                    <div class="metric-value">{basic_stats['teams_count']}</div>
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-icon">💬</div>
                <div class="metric-content">
                    <h3>Sessions with Messages</h3>
                    <div class="metric-value">{basic_stats['sessions_with_messages']}</div>
                </div>
            </div>
            
            <!-- Message Stats Row -->
            <div class="metric-card success">
                <div class="metric-icon">📝</div>
                <div class="metric-content">
                    <h3>Total Messages</h3>
                    <div class="metric-value">{message_stats['total_messages']:,}</div>
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-icon">📏</div>
                <div class="metric-content">
                    <h3>Median User Words</h3>
                    <div class="metric-value">{message_stats['median_user_words']:.0f}</div>
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-icon">🤖</div>
                <div class="metric-content">
                    <h3>Median Bot Words</h3>
                    <div class="metric-value">{message_stats['median_assistant_words']:.0f}</div>
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-icon">🏷️</div>
                <div class="metric-content">
                    <h3>Annotated Sessions</h3>
                    <div class="metric-value">{annotation_stats['sessions_with_tags']}</div>
                </div>
            </div>
            
            <!-- Sentiment & Quality Row -->
            <div class="metric-card positive">
                <div class="metric-icon">😊</div>
                <div class="metric-content">
                    <h3>Appreciation</h3>
                    <div class="metric-value">{sentiment_stats['appreciation_percentage']:.1f}%</div>
                    <div class="metric-subtitle">{sentiment_stats['appreciation_count']} messages</div>
                </div>
            </div>
            <div class="metric-card negative">
                <div class="metric-icon">😔</div>
                <div class="metric-content">
                    <h3>Dissatisfaction</h3>
                    <div class="metric-value">{sentiment_stats['dissatisfaction_percentage']:.1f}%</div>
                    <div class="metric-subtitle">{sentiment_stats['dissatisfaction_count']} messages</div>
                </div>
            </div>
            <div class="metric-card coaching">
                <div class="metric-icon">🎯</div>
                <div class="metric-content">
                    <h3>Coaching Annotations</h3>
                    <div class="metric-value">{coaching_quality['total_coaching_annotations']}</div>
                    <div class="metric-subtitle">Quality assessments</div>
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-icon">🏆</div>
                <div class="metric-content">
                    <h3>Bot Performance Good</h3>
                    <div class="metric-value">{annotation_stats['quality_categories']['bot_performance_good']}</div>
                </div>
            </div>
        </div>
        """
        return metrics_html
    
    def _generate_basic_metrics_summary(self) -> str:
        """Generate basic metrics summary when advanced metrics are not available"""
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
    
    def _generate_filters_ui(self) -> str:
        """Generate interactive filters UI for experiments and versions"""
        if not hasattr(self, 'metrics_calculator') or not self.metrics_calculator:
            return ""
        
        # Get experiment and version data
        all_metrics = self.metrics_calculator.calculate_all_metrics()
        experiment_stats = all_metrics['experiment_stats']
        
        # Build experiment options
        experiment_options = []
        for exp_id, count in experiment_stats['experiment_counts'].items():
            name = experiment_stats['experiment_names'].get(exp_id, 'Unknown')
            # Truncate long names
            display_name = name[:50] + "..." if len(name) > 50 else name
            experiment_options.append({
                'id': exp_id,
                'name': display_name,
                'full_name': name,
                'count': count
            })
        
        # Sort by session count (descending)
        experiment_options.sort(key=lambda x: x['count'], reverse=True)
        
        # Generate experiment options HTML
        experiment_options_html = ""
        for exp in experiment_options:
            experiment_options_html += f"""
            <div class="filter-option" onclick="toggleExperimentFilter('{exp['id']}', event)">
                <input type="checkbox" id="exp_{exp['id']}" onclick="event.stopPropagation()" onchange="updateExperimentSelection()">
                <div class="filter-option-name" title="{exp['full_name']}">{exp['name']}</div>
                <div class="filter-option-count">{exp['count']}</div>
            </div>
            """
        
        # Version options will be generated dynamically by JavaScript
        version_options_html = '<div id="version-options-placeholder">Select experiments to see their versions</div>'
        
        filters_html = f"""
        <div class="filters-container">
            <div class="filters-header">
                <span>🔍</span>
                <span>Filter Data</span>
            </div>
            <div class="filters-grid">
                <div class="filter-section">
                    <h4>
                        <span>🧪</span>
                        <span>Experiments</span>
                    </h4>
                    <div class="filter-controls">
                        <button class="filter-btn" onclick="selectAllExperiments()">Select All</button>
                        <button class="filter-btn" onclick="clearAllExperiments()">Clear All</button>
                        <button class="filter-btn" onclick="selectTopExperiments(10)">Top 10</button>
                    </div>
                    <div class="filter-options" id="experiment-options">
                        {experiment_options_html}
                    </div>
                    <div class="filter-stats" id="experiment-stats">
                        {len(experiment_options)} experiments available
                    </div>
                </div>
                
                <div class="filter-section">
                    <h4>
                        <span>📊</span>
                        <span>Versions</span>
                    </h4>
                    <div class="filter-controls">
                        <button class="filter-btn" onclick="selectAllVersions()">Select All</button>
                        <button class="filter-btn" onclick="clearAllVersions()">Clear All</button>
                        <button class="filter-btn" onclick="selectLatestVersions()">Latest Only</button>
                    </div>
                    <div class="filter-options" id="version-options">
                        {version_options_html}
                    </div>
                    <div class="filter-stats" id="version-stats">
                        Select experiments to see versions
                    </div>
                </div>
            </div>
        </div>
        """
        
        return filters_html
    
    def _get_sessions_data_json(self) -> str:
        """Get sessions data as JSON string for JavaScript"""
        if not hasattr(self, 'metrics_calculator') or not self.metrics_calculator:
            return "[]"
        
        # Convert sessions to JSON-serializable format
        sessions_data = []
        for session in self.metrics_calculator.sessions:
            # Use the corrected version extraction from metrics calculator
            actual_version = self.metrics_calculator._extract_version_from_session(session)
            
            sessions_data.append({
                'id': session.get('id', ''),
                'experiment': {
                    'id': session.get('experiment', {}).get('id', ''),
                    'name': session.get('experiment', {}).get('name', ''),
                    'version_number': actual_version  # Use the corrected version from message tags
                },
                'team': {
                    'slug': session.get('team', {}).get('slug', ''),
                    'name': session.get('team', {}).get('name', '')
                },
                'tags': session.get('tags', []),
                'created_at': session.get('created_at', '')
            })
        
        return json.dumps(sessions_data)
    
    def _get_experiment_versions_json(self) -> str:
        """Get experiment versions mapping as JSON string for JavaScript"""
        if not hasattr(self, 'metrics_calculator') or not self.metrics_calculator:
            return "{}"
        
        # Get experiment and version data
        all_metrics = self.metrics_calculator.calculate_all_metrics()
        experiment_stats = all_metrics['experiment_stats']
        
        # Build experiment versions mapping with names and descriptions
        experiment_versions = {}
        for exp_id, versions in experiment_stats['version_counts'].items():
            exp_name = experiment_stats['experiment_names'].get(exp_id, 'Unknown')
            
            # Get version descriptions from session data
            version_descriptions = {}
            for session in self.metrics_calculator.sessions:
                if session.get('experiment', {}).get('id') == exp_id:
                    exp_data = session.get('experiment', {})
                    if 'versions' in exp_data:
                        for version_info in exp_data['versions']:
                            version_num = version_info.get('version_number')
                            version_desc = version_info.get('version_description', '').strip()
                            if version_num and version_desc:
                                version_descriptions[version_num] = version_desc
                    break  # Only need one session per experiment to get version info
            
            experiment_versions[exp_id] = {
                'name': exp_name,
                'versions': versions,
                'version_descriptions': version_descriptions
            }
        
        return json.dumps(experiment_versions)
    
    def _get_messages_data_json(self) -> str:
        """Get messages data as JSON string for JavaScript"""
        if not hasattr(self, 'metrics_calculator') or not self.metrics_calculator:
            return "[]"
        
        # Convert messages to JSON-serializable format
        messages_data = []
        for message_data in self.metrics_calculator.messages:
            messages_data.append({
                'id': message_data.get('id', ''),
                'messages': message_data.get('messages', [])
            })
        
        return json.dumps(messages_data)
    
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
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            border: 1px solid #e5e7eb;
            transition: transform 0.2s, box-shadow 0.2s;
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        .metric-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 12px rgba(0,0,0,0.15);
        }}
        .metric-card.primary {{
            border-left: 4px solid #3b82f6;
            background: linear-gradient(135deg, #dbeafe, #ffffff);
        }}
        .metric-card.success {{
            border-left: 4px solid #10b981;
            background: linear-gradient(135deg, #d1fae5, #ffffff);
        }}
        .metric-card.positive {{
            border-left: 4px solid #059669;
            background: linear-gradient(135deg, #ecfdf5, #ffffff);
        }}
        .metric-card.negative {{
            border-left: 4px solid #dc2626;
            background: linear-gradient(135deg, #fee2e2, #ffffff);
        }}
        .metric-card.coaching {{
            border-left: 4px solid #7c3aed;
            background: linear-gradient(135deg, #ede9fe, #ffffff);
        }}
        .metric-icon {{
            font-size: 32px;
            line-height: 1;
            flex-shrink: 0;
        }}
        .metric-content {{
            flex: 1;
            text-align: left;
        }}
        .metric-card h3 {{
            margin: 0 0 8px 0;
            color: #374151;
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .metric-value {{
            font-size: 28px;
            font-weight: 700;
            color: #1f2937;
            margin-bottom: 4px;
            line-height: 1;
        }}
        .metric-subtitle {{
            font-size: 12px;
            color: #6b7280;
            font-weight: 500;
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
        
        /* Filter Styles */
        .filters-container {{
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            border: 1px solid #e5e7eb;
        }}
        .filters-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 20px;
            font-size: 18px;
            font-weight: 600;
            color: #374151;
        }}
        .filters-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
        }}
        .filter-section {{
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 15px;
            background: #f9fafb;
        }}
        .filter-section h4 {{
            margin: 0 0 15px 0;
            color: #374151;
            font-size: 16px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .filter-controls {{
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
        }}
        .filter-btn {{
            padding: 6px 12px;
            border: 1px solid #d1d5db;
            background: white;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 500;
            color: #374151;
            transition: all 0.2s;
        }}
        .filter-btn:hover {{
            background: #f3f4f6;
        }}
        .filter-btn.active {{
            background: #3b82f6;
            color: white;
            border-color: #3b82f6;
        }}
        .filter-options {{
            max-height: 200px;
            overflow-y: auto;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            background: white;
        }}
        .filter-option {{
            padding: 8px 12px;
            border-bottom: 1px solid #f3f4f6;
            display: flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.2s;
        }}
        .filter-option:hover {{
            background: #f9fafb;
        }}
        .filter-option:last-child {{
            border-bottom: none;
        }}
        .filter-option input[type="checkbox"] {{
            margin: 0;
        }}
        .filter-option-name {{
            font-weight: 500;
            color: #374151;
            flex: 1;
        }}
        .filter-option-count {{
            font-size: 12px;
            color: #6b7280;
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
        }}
        .filter-stats {{
            margin-top: 15px;
            padding: 10px;
            background: #eff6ff;
            border-radius: 6px;
            font-size: 12px;
            color: #1e40af;
        }}
        .version-experiment-header {{
            padding: 8px 12px;
            background: #f8fafc;
            border-bottom: 1px solid #e2e8f0;
            font-size: 13px;
            color: #475569;
            font-weight: 600;
        }}
        .version-option {{
            margin-left: 10px;
            border-left: 2px solid #e2e8f0;
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .filters-grid {{
                grid-template-columns: 1fr;
                gap: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 OpenChatStudio Dashboard</h1>
        <div class="subtitle">ECD Bot Performance Analytics • Generated {timestamp}</div>
    </div>
    
    {charts.get('filters_ui', '')}
    
    <!-- Loading indicator -->
    <div id="loading-indicator" style="text-align: center; padding: 40px; background: #f8fafc; border-radius: 12px; margin-bottom: 20px;">
        <div style="font-size: 18px; color: #6b7280; margin-bottom: 10px;">🔄 Loading Dashboard...</div>
        <div style="font-size: 14px; color: #9ca3af;">Processing session data and initializing filters</div>
    </div>
    
    <div id="metrics-summary" style="display: none;">
        {charts['metrics_summary']}
    </div>
    
    <div class="footer">
        Generated by OCSDashboardECD • OpenChatStudio Analytics
    </div>
    
    <script>
        // Global data storage
        let allSessionsData = {self._get_sessions_data_json()};
        let allMessagesData = {self._get_messages_data_json()};
        let experimentVersionsData = {self._get_experiment_versions_json()};
        let selectedExperiments = new Set();
        let selectedVersions = new Map(); // Map of experiment_id -> Set of versions
        
        // Initialize filters - start with nothing selected to show empty state
        document.addEventListener('DOMContentLoaded', function() {{
            // Start with no filters selected - show empty state by default
            updateVersionDisplay();
            updateFilters();
            
            // Hide loading indicator and show dashboard content
            const loadingIndicator = document.getElementById('loading-indicator');
            const metricsContent = document.getElementById('metrics-summary');
            
            if (loadingIndicator) loadingIndicator.style.display = 'none';
            if (metricsContent) metricsContent.style.display = 'block';
        }});
        
        // Filter control functions
        function selectAllExperiments() {{
            document.querySelectorAll('#experiment-options input[type="checkbox"]').forEach(cb => {{
                cb.checked = true;
                selectedExperiments.add(cb.id.replace('exp_', ''));
            }});
            updateVersionDisplay();
            selectAllVersions();
        }}
        
        function clearAllExperiments() {{
            document.querySelectorAll('#experiment-options input[type="checkbox"]').forEach(cb => {{
                cb.checked = false;
            }});
            selectedExperiments.clear();
            selectedVersions.clear(); // Also clear all selected versions
            
            // Force update the experiment selection to ensure consistency
            updateExperimentSelection();
        }}
        
        function selectTopExperiments(count) {{
            clearAllExperiments();
            const checkboxes = document.querySelectorAll('#experiment-options input[type="checkbox"]');
            for (let i = 0; i < Math.min(count, checkboxes.length); i++) {{
                checkboxes[i].checked = true;
                selectedExperiments.add(checkboxes[i].id.replace('exp_', ''));
            }}
            updateFilters();
        }}
        
        function selectAllVersions() {{
            // Select all versions for currently selected experiments
            selectedExperiments.forEach(expId => {{
                if (experimentVersionsData[expId]) {{
                    if (!selectedVersions.has(expId)) {{
                        selectedVersions.set(expId, new Set());
                    }}
                    Object.keys(experimentVersionsData[expId].versions).forEach(version => {{
                        selectedVersions.get(expId).add(parseInt(version));
                    }});
                }}
            }});
            updateVersionDisplay();
            updateFilters();
        }}
        
        function clearAllVersions() {{
            selectedVersions.clear();
            updateVersionDisplay();
            updateFilters();
        }}
        
        function selectLatestVersions() {{
            clearAllVersions();
            // Select the highest version for each selected experiment
            selectedExperiments.forEach(expId => {{
                if (experimentVersionsData[expId]) {{
                    const versions = Object.keys(experimentVersionsData[expId].versions).map(v => parseInt(v));
                    if (versions.length > 0) {{
                        const latestVersion = Math.max(...versions);
                        if (!selectedVersions.has(expId)) {{
                            selectedVersions.set(expId, new Set());
                        }}
                        selectedVersions.get(expId).add(latestVersion);
                    }}
                }}
            }});
            updateVersionDisplay();
            updateFilters();
        }}
        
        function updateExperimentSelection() {{
            // Update selected experiments based on checkboxes
            const previouslySelected = new Set(selectedExperiments);
            const newSelectedExperiments = new Set();
            
            document.querySelectorAll('#experiment-options input[type="checkbox"]').forEach(cb => {{
                if (cb.checked) {{
                    const expId = cb.id.replace('exp_', '');
                    newSelectedExperiments.add(expId);
                    
                    // If this experiment was just selected (not previously selected), select all its versions
                    if (!previouslySelected.has(expId)) {{
                        const expData = experimentVersionsData[expId];
                        if (expData && expData.versions) {{
                            if (!selectedVersions.has(expId)) {{
                                selectedVersions.set(expId, new Set());
                            }}
                            const versionSet = selectedVersions.get(expId);
                            // Add all versions for this experiment
                            Object.keys(expData.versions).forEach(version => {{
                                versionSet.add(parseInt(version));
                            }});
                        }}
                    }}
                }}
            }});
            
            selectedExperiments = newSelectedExperiments;
            
            // Clear versions for unselected experiments
            const experimentsToRemove = [];
            selectedVersions.forEach((versions, expId) => {{
                if (!selectedExperiments.has(expId)) {{
                    experimentsToRemove.push(expId);
                }}
            }});
            experimentsToRemove.forEach(expId => selectedVersions.delete(expId));
            
            updateVersionDisplay();
            updateFilters();
        }}
        
        function toggleExperimentFilter(expId, event) {{
            // If clicking on checkbox directly, let it handle itself
            if (event && event.target.type === 'checkbox') {{
                return;
            }}
            // Otherwise, toggle the checkbox programmatically
            const checkbox = document.getElementById('exp_' + expId);
            checkbox.checked = !checkbox.checked;
            updateExperimentSelection();
        }}
        
        function toggleVersionFilter(expId, version, event) {{
            // If clicking on checkbox directly, let it handle itself
            if (event && event.target.type === 'checkbox') {{
                return;
            }}
            
            if (!selectedVersions.has(expId)) {{
                selectedVersions.set(expId, new Set());
            }}
            
            const versionSet = selectedVersions.get(expId);
            if (versionSet.has(version)) {{
                versionSet.delete(version);
                if (versionSet.size === 0) {{
                    selectedVersions.delete(expId);
                }}
            }} else {{
                versionSet.add(version);
            }}
            
            // Also toggle the checkbox state
            const checkbox = document.getElementById(`ver_${{expId}}_${{version}}`);
            if (checkbox) {{
                checkbox.checked = versionSet.has(version);
            }}
            
            updateVersionDisplay();
            updateFilters();
        }}
        
        function updateVersionDisplay() {{
            const versionOptionsContainer = document.getElementById('version-options');
            if (!versionOptionsContainer) return;
            
            if (selectedExperiments.size === 0) {{
                versionOptionsContainer.innerHTML = '<div id="version-options-placeholder">Select experiments to see their versions</div>';
                return;
            }}
            
            let versionOptionsHtml = '';
            selectedExperiments.forEach(expId => {{
                if (experimentVersionsData[expId]) {{
                    const expData = experimentVersionsData[expId];
                    const expName = expData.name.length > 30 ? expData.name.substring(0, 30) + '...' : expData.name;
                    
                    // Add experiment header
                    versionOptionsHtml += `
                        <div class="version-experiment-header">
                            <strong>${{expName}}</strong>
                        </div>
                    `;
                    
                    // Add versions for this experiment
                    Object.entries(expData.versions).forEach(([version, count]) => {{
                        const versionInt = parseInt(version);
                        const isChecked = selectedVersions.has(expId) && selectedVersions.get(expId).has(versionInt);
                        
                        // Get version description from experiment data
                        const versionDesc = expData.version_descriptions && expData.version_descriptions[versionInt] 
                            ? expData.version_descriptions[versionInt] 
                            : '';
                        
                        // Truncate long descriptions
                        const truncatedDesc = versionDesc && versionDesc.length > 35 
                            ? versionDesc.substring(0, 35) + '...'
                            : versionDesc;
                        
                        const displayName = truncatedDesc ? `V${{version}} - ${{truncatedDesc}}` : `V${{version}}`;
                        
                        versionOptionsHtml += `
                            <div class="filter-option version-option" onclick="toggleVersionFilter('${{expId}}', ${{versionInt}}, event)">
                                <input type="checkbox" id="ver_${{expId}}_${{version}}" ${{isChecked ? 'checked' : ''}} onclick="event.stopPropagation()" onchange="toggleVersionFilter('${{expId}}', ${{versionInt}})">
                                <div class="filter-option-name" title="${{versionDesc || 'V' + version}}">${{displayName}}</div>
                                <div class="filter-option-count">${{count}}</div>
                            </div>
                        `;
                    }});
                }}
            }});
            
            versionOptionsContainer.innerHTML = versionOptionsHtml;
        }}
        
        function updateFilters() {{
            // Filter sessions based on selected experiments and versions
            const filteredSessions = allSessionsData.filter(session => {{
                const expId = session.experiment?.id;
                const version = session.experiment?.version_number || 1;
                
                // If no experiments selected, show no data (empty state)
                if (selectedExperiments.size === 0) return false;
                
                // Must match selected experiment
                const expMatch = selectedExperiments.has(expId);
                if (!expMatch) return false;
                
                // If experiment is selected, check if version is selected for this experiment
                const expVersions = selectedVersions.get(expId);
                // If no versions are selected for this experiment, show no data
                if (!expVersions || expVersions.size === 0) return false;
                // Otherwise, check if this specific version is selected
                const verMatch = expVersions.has(version);
                return verMatch;
            }});
            
            // Filter messages based on filtered sessions
            const filteredSessionIds = new Set(filteredSessions.map(s => s.id));
            const filteredMessages = allMessagesData.filter(msg => filteredSessionIds.has(msg.id));
            
            // Recalculate and update metrics
            updateMetrics(filteredSessions, filteredMessages);
            
            // Update filter stats
            updateFilterStats(filteredSessions);
        }}
        
        function updateMetrics(sessions, messages) {{
            // Calculate new metrics based on filtered data
            const metrics = calculateMetrics(sessions, messages);
            
            // Update metric cards
            updateMetricCard('Total Sessions', metrics.totalSessions.toLocaleString());
            updateMetricCard('Experiments', metrics.experimentsCount);
            updateMetricCard('Teams', metrics.teamsCount);
            updateMetricCard('Sessions with Messages', metrics.sessionsWithMessages);
            updateMetricCard('Total Messages', metrics.totalMessages.toLocaleString());
            updateMetricCard('Median User Words', Math.round(metrics.medianUserWords));
            updateMetricCard('Median Bot Words', Math.round(metrics.medianBotWords));
            updateMetricCard('Annotated Sessions', metrics.annotatedSessions);
            updateMetricCard('Appreciation', metrics.appreciationPercentage.toFixed(1) + '%', metrics.appreciationCount + ' messages');
            updateMetricCard('Dissatisfaction', metrics.dissatisfactionPercentage.toFixed(1) + '%', metrics.dissatisfactionCount + ' messages');
            updateMetricCard('Coaching Annotations', metrics.coachingAnnotations);
            updateMetricCard('Bot Performance Good', metrics.botPerformanceGood);
        }}
        
        function updateMetricCard(title, value, subtitle = '') {{
            const cards = document.querySelectorAll('.metric-card');
            cards.forEach(card => {{
                const h3 = card.querySelector('h3');
                if (h3 && h3.textContent.trim().toUpperCase() === title.toUpperCase()) {{
                    const valueEl = card.querySelector('.metric-value');
                    const subtitleEl = card.querySelector('.metric-subtitle');
                    if (valueEl) valueEl.textContent = value;
                    if (subtitleEl && subtitle) subtitleEl.textContent = subtitle;
                }}
            }});
        }}
        
        function updateFilterStats(filteredSessions) {{
            const expStats = document.getElementById('experiment-stats');
            const verStats = document.getElementById('version-stats');
            
            if (expStats) {{
                if (selectedExperiments.size === 0) {{
                    expStats.textContent = `No experiments selected • ${{filteredSessions.length}} sessions`;
                }} else {{
                    expStats.textContent = `${{selectedExperiments.size}} experiments selected • ${{filteredSessions.length}} sessions`;
                }}
            }}
            if (verStats) {{
                let totalVersions = 0;
                selectedVersions.forEach(versions => totalVersions += versions.size);
                if (selectedExperiments.size === 0) {{
                    verStats.textContent = `Select experiments to see data`;
                }} else if (totalVersions === 0) {{
                    verStats.textContent = `All versions for selected experiments shown`;
                }} else {{
                    verStats.textContent = `${{totalVersions}} versions selected • ${{filteredSessions.length}} sessions`;
                }}
            }}
        }}
        
        function calculateMetrics(sessions, messages) {{
            // Build session-message map
            const sessionMessagesMap = {{}};
            messages.forEach(msgData => {{
                if (msgData.id) {{
                    sessionMessagesMap[msgData.id] = msgData;
                }}
            }});
            
            // Basic stats
            const totalSessions = sessions.length;
            const experimentsCount = new Set(sessions.map(s => s.experiment?.id).filter(Boolean)).size;
            const teamsCount = new Set(sessions.map(s => s.team?.slug).filter(Boolean)).size;
            const sessionsWithMessages = sessions.filter(s => sessionMessagesMap[s.id]).length;
            
            // Message stats
            let totalMessages = 0;
            let userWordCounts = [];
            let botWordCounts = [];
            let appreciationCount = 0;
            let dissatisfactionCount = 0;
            let totalUserMessages = 0;
            
            const appreciationPatterns = [/\\bthank\\b/i, /\\bthanks\\b/i, /\\bthank you\\b/i, /\\bgrateful\\b/i, /\\bappreciate\\b/i, /\\bawesome\\b/i, /\\bgreat\\b/i, /\\bexcellent\\b/i, /\\bhelpful\\b/i, /\\bwonderful\\b/i, /\\bamazing\\b/i, /\\bperfect\\b/i];
            const dissatisfactionPatterns = [/\\bfrustrat\\b/i, /\\bconfus\\b/i, /\\bwrong\\b/i, /\\bbad\\b/i, /\\bterrible\\b/i, /\\bawful\\b/i, /\\buseless\\b/i, /\\bstupid\\b/i, /\\bdon't understand\\b/i, /\\bdoesn't work\\b/i, /\\bnot helpful\\b/i];
            
            sessions.forEach(session => {{
                const messageData = sessionMessagesMap[session.id];
                if (messageData && messageData.messages) {{
                    messageData.messages.forEach(msg => {{
                        totalMessages++;
                        const content = msg.content || '';
                        const wordCount = content.split(' ').length;
                        
                        if (msg.role === 'user') {{
                            totalUserMessages++;
                            userWordCounts.push(wordCount);
                            
                            // Check sentiment
                            const lowerContent = content.toLowerCase();
                            if (appreciationPatterns.some(pattern => pattern.test(lowerContent))) {{
                                appreciationCount++;
                            }}
                            if (dissatisfactionPatterns.some(pattern => pattern.test(lowerContent))) {{
                                dissatisfactionCount++;
                            }}
                        }} else if (msg.role === 'assistant') {{
                            botWordCounts.push(wordCount);
                        }}
                    }});
                }}
            }});
            
            // Annotation stats
            let annotatedSessions = 0;
            let coachingAnnotations = 0;
            let botPerformanceGood = 0;
            
            sessions.forEach(session => {{
                const tags = session.tags || [];
                if (tags.length > 0) {{
                    annotatedSessions++;
                    tags.forEach(tag => {{
                        const tagName = typeof tag === 'string' ? tag : tag.name || '';
                        if (tagName.toLowerCase().includes('coaching')) {{
                            coachingAnnotations++;
                        }}
                        if (tagName === 'bot_performance_good') {{
                            botPerformanceGood++;
                        }}
                    }});
                }}
            }});
            
            return {{
                totalSessions,
                experimentsCount,
                teamsCount,
                sessionsWithMessages,
                totalMessages,
                medianUserWords: userWordCounts.length > 0 ? median(userWordCounts) : 0,
                medianBotWords: botWordCounts.length > 0 ? median(botWordCounts) : 0,
                annotatedSessions,
                appreciationCount,
                dissatisfactionCount,
                appreciationPercentage: totalUserMessages > 0 ? (appreciationCount / totalUserMessages) * 100 : 0,
                dissatisfactionPercentage: totalUserMessages > 0 ? (dissatisfactionCount / totalUserMessages) * 100 : 0,
                coachingAnnotations,
                botPerformanceGood
            }};
        }}
        
        function median(arr) {{
            if (arr.length === 0) return 0;
            const sorted = [...arr].sort((a, b) => a - b);
            const mid = Math.floor(sorted.length / 2);
            return sorted.length % 2 === 0 ? (sorted[mid - 1] + sorted[mid]) / 2 : sorted[mid];
        }}
    </script>
</body>
</html>
        """
        return html

