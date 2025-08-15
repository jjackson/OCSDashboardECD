"""
Data Models for OpenChatStudio Dashboard
Based on actual API schema from https://chatbots.dimagi.com/api/schema/
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any
import json
import os

@dataclass
class Team:
    """Team information"""
    name: str
    slug: str
    
    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'Team':
        return cls(
            name=data.get('name', ''),
            slug=data.get('slug', '')
        )

@dataclass
class ExperimentVersion:
    """Experiment version information"""
    name: str
    version_number: int
    is_default_version: bool
    version_description: str
    
    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'ExperimentVersion':
        return cls(
            name=data.get('name', ''),
            version_number=data.get('version_number', 0),
            is_default_version=data.get('is_default_version', False),
            version_description=data.get('version_description', '')
        )

@dataclass
class Experiment:
    """Experiment/Bot information"""
    id: str
    name: str
    url: str
    version_number: int
    versions: List[ExperimentVersion]
    
    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'Experiment':
        versions = [ExperimentVersion.from_api_data(v) for v in data.get('versions', [])]
        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            url=data.get('url', ''),
            version_number=data.get('version_number', 0),
            versions=versions
        )

@dataclass
class Participant:
    """Session participant information"""
    identifier: str
    remote_id: str
    
    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'Participant':
        return cls(
            identifier=data.get('identifier', ''),
            remote_id=data.get('remote_id', '')
        )

@dataclass
class Message:
    """Individual message in a chat session - matches API Message schema"""
    role: str  # 'system', 'user', 'assistant'
    content: str
    created_at: datetime
    metadata: Dict[str, Any]
    tags: List[str]
    attachments: List[Dict[str, Any]]  # File attachments
    word_count: int  # Calculated field
    
    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'Message':
        """Create Message from API response data"""
        content = data.get('content', '')
        created_at = datetime.fromisoformat(data.get('created_at', '').replace('Z', '+00:00'))
        
        return cls(
            role=data.get('role', ''),
            content=content,
            created_at=created_at,
            metadata=data.get('metadata', {}),
            tags=data.get('tags', []),
            attachments=data.get('attachments', []),
            word_count=len(content.split()) if content else 0
        )

@dataclass
class Session:
    """Chat session between bot and user - matches API ExperimentSessionWithMessages schema"""
    id: str
    url: str
    team: Team
    experiment: Experiment
    participant: Participant
    created_at: datetime
    updated_at: datetime
    tags: List[str]
    messages: Optional[List[Message]] = None  # Only populated when fetched with messages
    
    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'Session':
        """Create Session from API response data"""
        # Parse datetime strings
        created_at = datetime.fromisoformat(data.get('created_at', '').replace('Z', '+00:00'))
        updated_at = datetime.fromisoformat(data.get('updated_at', '').replace('Z', '+00:00'))
        
        # Parse nested objects
        team = Team.from_api_data(data.get('team', {}))
        experiment = Experiment.from_api_data(data.get('experiment', {}))
        participant = Participant.from_api_data(data.get('participant', {}))
        
        # Parse messages if present
        messages = None
        if 'messages' in data and data['messages']:
            messages = [Message.from_api_data(msg) for msg in data['messages']]
        
        return cls(
            id=data.get('id', ''),
            url=data.get('url', ''),
            team=team,
            experiment=experiment,
            participant=participant,
            created_at=created_at,
            updated_at=updated_at,
            tags=data.get('tags', []),
            messages=messages
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        # Convert datetime objects to ISO strings
        result['created_at'] = self.created_at.isoformat()
        result['updated_at'] = self.updated_at.isoformat()
        if result['messages']:
            for msg in result['messages']:
                if 'created_at' in msg:
                    msg['created_at'] = msg['created_at'].isoformat() if isinstance(msg['created_at'], datetime) else msg['created_at']
        return result
    
    def save_to_file(self, directory: str) -> str:
        """Save session to individual JSON file"""
        os.makedirs(directory, exist_ok=True)
        filename = f"session_{self.id}.json"
        filepath = os.path.join(directory, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        
        return filepath

# Note: Ratings and Annotations are not available in the current API schema
# These would need to be implemented if/when those endpoints become available

@dataclass
class SessionStats:
    """Calculated statistics for a session"""
    session_id: str
    message_count: int
    user_message_count: int
    assistant_message_count: int
    total_user_words: int
    average_user_words: float
    session_duration_minutes: Optional[float]
    
    @classmethod
    def from_session(cls, session: Session) -> 'SessionStats':
        """Calculate stats from a session with messages"""
        if not session.messages:
            return cls(
                session_id=session.id,
                message_count=0,
                user_message_count=0,
                assistant_message_count=0,
                total_user_words=0,
                average_user_words=0.0,
                session_duration_minutes=None
            )
        
        user_messages = [m for m in session.messages if m.role == 'user']
        assistant_messages = [m for m in session.messages if m.role == 'assistant']
        
        total_user_words = sum(m.word_count for m in user_messages)
        average_user_words = total_user_words / len(user_messages) if user_messages else 0.0
        
        # Calculate session duration
        duration_minutes = None
        if session.messages and len(session.messages) > 1:
            first_msg = min(session.messages, key=lambda m: m.created_at)
            last_msg = max(session.messages, key=lambda m: m.created_at)
            duration = last_msg.created_at - first_msg.created_at
            duration_minutes = duration.total_seconds() / 60
        
        return cls(
            session_id=session.id,
            message_count=len(session.messages),
            user_message_count=len(user_messages),
            assistant_message_count=len(assistant_messages),
            total_user_words=total_user_words,
            average_user_words=average_user_words,
            session_duration_minutes=duration_minutes
        )

@dataclass
class DashboardData:
    """Container for all dashboard data based on actual API capabilities"""
    sessions: List[Session]
    session_stats: List[SessionStats]
    
    def get_session_count(self) -> int:
        """Get total number of sessions"""
        return len(self.sessions)
    
    def get_sessions_by_experiment(self) -> Dict[str, List[Session]]:
        """Group sessions by experiment name"""
        result = {}
        for session in self.sessions:
            exp_name = session.experiment.name
            if exp_name not in result:
                result[exp_name] = []
            result[exp_name].append(session)
        return result
    
    def get_sessions_by_date(self) -> Dict[str, int]:
        """Get session counts by date"""
        result = {}
        for session in self.sessions:
            date_key = session.created_at.date().isoformat()
            result[date_key] = result.get(date_key, 0) + 1
        return result
    
    def get_user_word_counts(self) -> List[int]:
        """Get word counts for all user messages across all sessions"""
        word_counts = []
        for session in self.sessions:
            if session.messages:
                for msg in session.messages:
                    if msg.role == 'user':
                        word_counts.append(msg.word_count)
        return word_counts
    
    def get_median_user_words(self) -> float:
        """Get median word count for user messages"""
        word_counts = self.get_user_word_counts()
        if not word_counts:
            return 0.0
        sorted_counts = sorted(word_counts)
        n = len(sorted_counts)
        if n % 2 == 0:
            return (sorted_counts[n//2 - 1] + sorted_counts[n//2]) / 2
        return sorted_counts[n//2]
    
    def get_version_comparison(self) -> Dict[int, Dict[str, Any]]:
        """Compare metrics across experiment versions"""
        version_data = {}
        for session in self.sessions:
            version = session.experiment.version_number
            if version not in version_data:
                version_data[version] = {
                    'session_count': 0,
                    'experiment_name': session.experiment.name,
                    'sessions': []
                }
            version_data[version]['session_count'] += 1
            version_data[version]['sessions'].append(session)
        return version_data