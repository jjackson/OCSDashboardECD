"""
Advanced metrics calculations for OCS dashboard
Based on analysis from friend's React dashboard implementation
"""

import re
import statistics
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict, Counter


class MetricsCalculator:
    """Calculate advanced metrics from session and message data"""
    
    def __init__(self, sessions: List[Dict], messages: List[Dict]):
        self.sessions = sessions
        self.messages = messages
        self.session_messages_map = self._build_session_messages_map()
    
    def _build_session_messages_map(self) -> Dict[str, Dict]:
        """Build a map of session_id to message data"""
        session_map = {}
        for message_data in self.messages:
            session_id = message_data.get('id')
            if session_id:
                session_map[session_id] = message_data
        return session_map
    
    def calculate_all_metrics(self) -> Dict[str, Any]:
        """Calculate all advanced metrics"""
        return {
            'basic_stats': self._calculate_basic_stats(),
            'message_stats': self._calculate_message_stats(),
            'sentiment_stats': self._calculate_sentiment_stats(),
            'annotation_stats': self._calculate_annotation_stats(),
            'coaching_quality': self._calculate_coaching_quality(),
            'experiment_stats': self._calculate_experiment_stats(),
        }
    
    def _calculate_basic_stats(self) -> Dict[str, Any]:
        """Calculate basic session statistics"""
        total_sessions = len(self.sessions)
        sessions_with_messages = len([s for s in self.sessions if s.get('id') in self.session_messages_map])
        
        # Date range
        dates = []
        for session in self.sessions:
            if session.get('created_at'):
                dates.append(session['created_at'])
        
        date_range = {
            'start': min(dates) if dates else None,
            'end': max(dates) if dates else None
        }
        
        return {
            'total_sessions': total_sessions,
            'sessions_with_messages': sessions_with_messages,
            'date_range': date_range,
            'experiments_count': len(set(s.get('experiment', {}).get('id') for s in self.sessions if s.get('experiment', {}).get('id'))),
            'teams_count': len(set(s.get('team', {}).get('slug') for s in self.sessions if s.get('team', {}).get('slug')))
        }
    
    def _calculate_message_stats(self) -> Dict[str, Any]:
        """Calculate message-based statistics"""
        user_word_counts = []
        assistant_word_counts = []
        total_messages = 0
        
        for session_id, message_data in self.session_messages_map.items():
            messages = message_data.get('messages', [])
            if not messages:
                continue
                
            session_user_words = []
            session_assistant_words = []
            
            for message in messages:
                total_messages += 1
                content = message.get('content', '')
                word_count = len(content.split()) if content else 0
                
                if message.get('role') == 'user':
                    session_user_words.append(word_count)
                elif message.get('role') == 'assistant':
                    session_assistant_words.append(word_count)
            
            # Add session totals
            if session_user_words:
                user_word_counts.extend(session_user_words)
            if session_assistant_words:
                assistant_word_counts.extend(session_assistant_words)
        
        return {
            'total_messages': total_messages,
            'median_user_words': statistics.median(user_word_counts) if user_word_counts else 0,
            'median_assistant_words': statistics.median(assistant_word_counts) if assistant_word_counts else 0,
            'avg_user_words': statistics.mean(user_word_counts) if user_word_counts else 0,
            'avg_assistant_words': statistics.mean(assistant_word_counts) if assistant_word_counts else 0,
            'sessions_with_messages': len([s for s in self.session_messages_map.values() if s.get('messages')])
        }
    
    def _calculate_sentiment_stats(self) -> Dict[str, Any]:
        """Calculate sentiment analysis from user messages"""
        appreciation_count = 0
        dissatisfaction_count = 0
        total_user_messages = 0
        
        # Patterns based on friend's dashboard
        appreciation_patterns = [
            r'\bthank\b', r'\bthanks\b', r'\bthank you\b', r'\bgrateful\b',
            r'\bappreciate\b', r'\bawesome\b', r'\bgreat\b', r'\bexcellent\b',
            r'\bhelpful\b', r'\bwonderful\b', r'\bamazing\b', r'\bperfect\b'
        ]
        
        dissatisfaction_patterns = [
            r'\bfrustrat\b', r'\bconfus\b', r'\bwrong\b', r'\bbad\b',
            r'\bterrible\b', r'\bawful\b', r'\buseless\b', r'\bstupid\b',
            r'\bdon\'t understand\b', r'\bdoesn\'t work\b', r'\bnot helpful\b'
        ]
        
        for session_id, message_data in self.session_messages_map.items():
            messages = message_data.get('messages', [])
            
            for message in messages:
                if message.get('role') == 'user':
                    total_user_messages += 1
                    content = message.get('content', '').lower()
                    
                    # Check for appreciation
                    if any(re.search(pattern, content, re.IGNORECASE) for pattern in appreciation_patterns):
                        appreciation_count += 1
                    
                    # Check for dissatisfaction
                    if any(re.search(pattern, content, re.IGNORECASE) for pattern in dissatisfaction_patterns):
                        dissatisfaction_count += 1
        
        return {
            'appreciation_count': appreciation_count,
            'dissatisfaction_count': dissatisfaction_count,
            'total_user_messages': total_user_messages,
            'appreciation_percentage': (appreciation_count / total_user_messages * 100) if total_user_messages > 0 else 0,
            'dissatisfaction_percentage': (dissatisfaction_count / total_user_messages * 100) if total_user_messages > 0 else 0
        }
    
    def _calculate_annotation_stats(self) -> Dict[str, Any]:
        """Calculate annotation statistics from session tags"""
        all_tags = []
        annotation_counts = defaultdict(int)
        
        for session in self.sessions:
            tags = session.get('tags', [])
            if tags:
                all_tags.extend(tags)
                
                for tag in tags:
                    tag_name = tag.get('name', '') if isinstance(tag, dict) else str(tag)
                    if tag_name:
                        # Filter out version tags (like "v7", "v8", etc.)
                        if not re.match(r'^v\d+$', tag_name.lower()):
                            annotation_counts[tag_name] += 1
        
        # Calculate quality metrics
        total_annotated = len([s for s in self.sessions if s.get('tags')])
        
        quality_categories = {
            'bot_performance_good': 0,
            'bot_performance_bad': 0,
            'engagement_good': 0,
            'engagement_bad': 0,
            'coaching_good': 0,
            'coaching_bad': 0,
            'coaching_undetermined': 0,
            'safe': 0,
            'accurate': 0,
            'user_knowledge_good': 0,
            'user_knowledge_bad': 0
        }
        
        for tag_name, count in annotation_counts.items():
            if tag_name in quality_categories:
                quality_categories[tag_name] = count
        
        return {
            'total_tags': len(all_tags),
            'unique_tags': len(set(all_tags)),
            'sessions_with_tags': total_annotated,
            'annotation_counts': dict(annotation_counts),
            'quality_categories': quality_categories
        }
    
    def _calculate_coaching_quality(self) -> Dict[str, Any]:
        """Calculate coaching quality percentages"""
        coaching_counts = defaultdict(int)
        total_coaching_annotations = 0
        
        for session in self.sessions:
            tags = session.get('tags', [])
            session_coaching_tags = []
            
            for tag in tags:
                tag_name = tag.get('name', '') if isinstance(tag, dict) else str(tag)
                if 'coaching' in tag_name.lower():
                    session_coaching_tags.append(tag_name)
                    coaching_counts[tag_name] += 1
            
            if session_coaching_tags:
                total_coaching_annotations += 1
        
        # Calculate percentages
        coaching_percentages = {}
        if total_coaching_annotations > 0:
            for tag_name, count in coaching_counts.items():
                coaching_percentages[tag_name] = (count / total_coaching_annotations) * 100
        
        return {
            'total_coaching_annotations': total_coaching_annotations,
            'coaching_counts': dict(coaching_counts),
            'coaching_percentages': coaching_percentages
        }
    
    def _calculate_experiment_stats(self) -> Dict[str, Any]:
        """Calculate experiment-specific statistics"""
        experiment_counts = defaultdict(int)
        experiment_names = {}
        version_counts = defaultdict(lambda: defaultdict(int))
        
        for session in self.sessions:
            experiment = session.get('experiment', {})
            if experiment:
                exp_id = experiment.get('id')
                exp_name = experiment.get('name', 'Unknown')
                
                if exp_id:
                    experiment_counts[exp_id] += 1
                    experiment_names[exp_id] = exp_name
                    
                    # Extract actual version from message tags, not session version_number
                    session_version = self._extract_version_from_session(session)
                    if session_version:
                        version_counts[exp_id][session_version] += 1
        
        return {
            'experiment_counts': dict(experiment_counts),
            'experiment_names': experiment_names,
            'version_counts': {exp_id: dict(versions) for exp_id, versions in version_counts.items()}
        }
    
    def _extract_version_from_session(self, session: Dict) -> Optional[int]:
        """Extract the actual version used from session message data"""
        session_id = session.get('id')
        if not session_id or session_id not in self.session_messages_map:
            # Fallback to session version_number if no message data
            return session.get('experiment', {}).get('version_number', 1)
            
        message_data = self.session_messages_map[session_id]
        messages = message_data.get('messages', [])
        
        # Look for version tags in messages (format: "v13", "v14", etc.)
        for message in messages:
            tags = message.get('tags', [])
            for tag in tags:
                if isinstance(tag, str) and tag.startswith('v') and tag[1:].isdigit():
                    return int(tag[1:])
        
        # Fallback to session version_number if no message tags found
        return session.get('experiment', {}).get('version_number', 1)
    
    def get_top_experiments(self, limit: int = 10) -> List[Tuple[str, str, int]]:
        """Get top experiments by session count"""
        experiment_stats = self._calculate_experiment_stats()
        
        experiments = []
        for exp_id, count in experiment_stats['experiment_counts'].items():
            name = experiment_stats['experiment_names'].get(exp_id, 'Unknown')
            experiments.append((exp_id, name, count))
        
        return sorted(experiments, key=lambda x: x[2], reverse=True)[:limit]
    
    def get_quality_summary(self) -> Dict[str, Any]:
        """Get a summary of quality metrics for the dashboard"""
        annotation_stats = self._calculate_annotation_stats()
        coaching_quality = self._calculate_coaching_quality()
        sentiment_stats = self._calculate_sentiment_stats()
        
        return {
            'total_sessions': len(self.sessions),
            'sessions_with_annotations': annotation_stats['sessions_with_tags'],
            'coaching_good_percentage': coaching_quality['coaching_percentages'].get('coaching_good', 0),
            'coaching_bad_percentage': coaching_quality['coaching_percentages'].get('coaching_bad', 0),
            'appreciation_percentage': sentiment_stats['appreciation_percentage'],
            'dissatisfaction_percentage': sentiment_stats['dissatisfaction_percentage'],
            'bot_performance_good': annotation_stats['quality_categories']['bot_performance_good'],
            'bot_performance_bad': annotation_stats['quality_categories']['bot_performance_bad']
        }
