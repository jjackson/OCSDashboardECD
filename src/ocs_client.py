"""
OpenChatStudio API Client
Simple HTTP client for fetching data from OpenChatStudio API
"""

import requests
import time
from typing import Dict, List, Optional, Any
import constants

class OCSClientError(Exception):
    """Custom exception for OCS API client errors"""
    pass

class OCSClient:
    """Simple client for OpenChatStudio API following Coverage project patterns"""
    
    def __init__(self, api_key: str, base_url: str = None, project_id: str = None):
        self.api_key = api_key
        self.base_url = base_url or constants.DEFAULT_API_BASE_URL
        self.project_id = project_id
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            'X-API-KEY': self.api_key,
            'Accept': 'application/json',
            'User-Agent': constants.USER_AGENT
        })
        
        # Add project header if specified
        if self.project_id:
            self.session.headers.update({
                'X-Project-ID': self.project_id
            })
        
    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            # Try different common health/status endpoints
            endpoints_to_try = ['/health', '/status', '/ping', '/api/health', '/']
            
            for endpoint in endpoints_to_try:
                try:
                    response = self._make_request('GET', endpoint)
                    if response.status_code in [200, 401]:  # 401 means auth issue but API is reachable
                        return True
                except:
                    continue
            return False
        except:
            return False
    
    def test_auth(self) -> tuple[bool, str]:
        """Test API authentication and return status with message"""
        try:
            # Try to access a protected endpoint that should exist
            endpoints_to_try = ['/bots', '/assistants', '/sessions', '/conversations']
            
            for endpoint in endpoints_to_try:
                try:
                    response = self._make_request('GET', endpoint)
                    if response.status_code == 200:
                        data = response.json()
                        return True, f"✅ Authentication successful! Found {len(data) if isinstance(data, list) else 1} item(s) at {endpoint}"
                    elif response.status_code == 401:
                        return False, "❌ Authentication failed - check your API key"
                    elif response.status_code == 403:
                        return False, "❌ Access forbidden - check your API key permissions"
                except Exception as e:
                    continue
            
            return False, "❌ Could not find any accessible endpoints"
            
        except Exception as e:
            return False, f"❌ Connection error: {e}"
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> requests.Response:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                timeout=60
            )
            
            if response.status_code == 429:  # Rate limited
                retry_after = int(response.headers.get('Retry-After', 60))
                print(f"⏳ Rate limited, waiting {retry_after} seconds...")
                time.sleep(retry_after)
                return self._make_request(method, endpoint, params, data)
            
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            raise OCSClientError(f"API request failed: {e}")
    
    def _paginate(self, endpoint: str, params: Dict = None, max_pages: int = None) -> List[Dict]:
        """Handle paginated API responses using cursor-based pagination"""
        all_results = []
        page_num = 1
        params = params or {}
        next_url = None
        
        while True:
            # For first request, use endpoint with params
            if next_url is None:
                params.update({'page_size': constants.PAGE_SIZE})
                response = self._make_request('GET', endpoint, params=params)
            else:
                # For subsequent requests, use the next URL directly
                # Extract just the query parameters from the next URL
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(next_url)
                next_params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
                response = self._make_request('GET', endpoint, params=next_params)
            
            data = response.json()
            
            # Handle cursor-based pagination response format
            if 'results' in data:
                results = data['results']
                next_url = data.get('next')
                has_next = next_url is not None
            elif isinstance(data, list):
                results = data
                has_next = len(results) == constants.PAGE_SIZE
                next_url = None
            else:
                results = [data]
                has_next = False
                next_url = None
            
            all_results.extend(results)
            
            # Show progress after each page
            print(f"  Fetched page {page_num}: {len(results)} items (total: {len(all_results)})")
            
            # Break if we hit max pages limit or no more results
            if not has_next or len(results) == 0 or (max_pages and page_num >= max_pages):
                break
                
            page_num += 1
            
        return all_results
    
    def _paginate_with_callback(self, endpoint: str, callback_fn, params: Dict = None, max_pages: int = None) -> int:
        """Handle paginated API responses with callback for each page using cursor-based pagination"""
        total_processed = 0
        page_num = 1
        params = params or {}
        next_url = None
        
        while True:
            # For first request, use endpoint with params
            if next_url is None:
                params.update({'page_size': constants.PAGE_SIZE})
                response = self._make_request('GET', endpoint, params=params)
            else:
                # For subsequent requests, use the next URL directly
                # Extract just the query parameters from the next URL
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(next_url)
                next_params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
                response = self._make_request('GET', endpoint, params=next_params)
            
            data = response.json()
            
            # Handle cursor-based pagination response format
            if 'results' in data:
                results = data['results']
                next_url = data.get('next')
                has_next = next_url is not None
            elif isinstance(data, list):
                results = data
                has_next = len(results) == constants.PAGE_SIZE
                next_url = None
            else:
                results = [data]
                has_next = False
                next_url = None
            
            # Process this page's results with callback
            processed_count = callback_fn(results, page_num, total_processed)
            total_processed += processed_count
            
            # Show progress after each page
            print(f"  Processed page {page_num}: {processed_count} items (total: {total_processed})")
            
            # Break if we hit max pages limit or no more results
            if not has_next or len(results) == 0 or (max_pages and page_num >= max_pages):
                break
                
            page_num += 1
            
        return total_processed
    
    def get_sessions(self, experiment_ids: List[str] = None, bot_id: str = None, version: str = None, coaching_method: str = None, max_pages: int = None) -> List[Dict]:
        """Get chat sessions with optional filters"""
        params = {}
        if bot_id:
            params['bot_id'] = bot_id
        if version:
            params['version'] = version
        if coaching_method:
            params['coaching_method'] = coaching_method
            
        # Limit initial fetch to avoid timeouts
        all_sessions = self._paginate('/sessions', params, max_pages=max_pages)
        
        # Filter by experiment IDs if specified
        if experiment_ids:
            filtered_sessions = []
            for session in all_sessions:
                if session.get('experiment', {}).get('id') in experiment_ids:
                    filtered_sessions.append(session)
            return filtered_sessions
            
        return all_sessions
    
    def get_sessions_streaming(self, callback_fn, experiment_ids: List[str] = None, bot_id: str = None, version: str = None, coaching_method: str = None, max_pages: int = None) -> int:
        """Get chat sessions with callback processing for each page"""
        params = {}
        if bot_id:
            params['bot_id'] = bot_id
        if version:
            params['version'] = version
        if coaching_method:
            params['coaching_method'] = coaching_method
        
        def filter_callback(sessions_data, page, total_processed):
            # Filter by experiment IDs if specified
            if experiment_ids:
                filtered_sessions = []
                for session in sessions_data:
                    if session.get('experiment', {}).get('id') in experiment_ids:
                        filtered_sessions.append(session)
                sessions_data = filtered_sessions
            
            # Process with user callback
            return callback_fn(sessions_data, page, total_processed)
        
        return self._paginate_with_callback('/sessions', filter_callback, params, max_pages=max_pages)
    
    def get_target_experiments(self) -> Dict[str, str]:
        """Get experiment IDs for target experiments defined in constants"""
        experiments = self.get_experiments()
        target_map = {}
        
        for experiment in experiments:
            exp_name = experiment.get('name', '')
            for target_name in constants.TARGET_EXPERIMENTS:
                if target_name in exp_name or exp_name in target_name:
                    target_map[target_name] = experiment.get('id')
                    break
        
        return target_map
    
    def get_session_details(self, session_id: str) -> Dict:
        """Get detailed information for a specific session"""
        response = self._make_request('GET', f'/sessions/{session_id}')
        return response.json()
    
    def get_messages(self, session_id: str) -> List[Dict]:
        """Get messages for a specific session"""
        return self._paginate(f'/sessions/{session_id}/messages')
    
    def get_annotations(self, session_id: str = None) -> List[Dict]:
        """Get annotations, optionally filtered by session"""
        endpoint = '/annotations'
        params = {}
        if session_id:
            params['session_id'] = session_id
            
        return self._paginate(endpoint, params)
    
    def get_experiments(self) -> List[Dict]:
        """Get list of available experiments/bots"""
        return self._paginate('/experiments')
    
    def get_bots(self) -> List[Dict]:
        """Get list of available bots/assistants (alias for experiments)"""
        return self.get_experiments()
    
    def get_bot_versions(self, bot_id: str) -> List[Dict]:
        """Get versions for a specific bot"""
        return self._paginate(f'/bots/{bot_id}/versions')
    
    def get_ratings(self, session_id: str = None) -> List[Dict]:
        """Get FLW ratings, optionally filtered by session"""
        endpoint = '/ratings'
        params = {}
        if session_id:
            params['session_id'] = session_id
            
        return self._paginate(endpoint, params)
