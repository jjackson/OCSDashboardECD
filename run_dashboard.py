#!/usr/bin/env python3
"""
OCS Dashboard Generator
Main entry point for generating OpenChatStudio analytics dashboard.

Usage:
    python run_dashboard.py                    # Generate dashboard
    python run_dashboard.py test               # Test API connection
    python run_dashboard.py download           # Download all session data
    python run_dashboard.py download --limit 100  # Download limited sessions
"""

import os
import sys
import json
import argparse
import webbrowser
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ocs_client import OCSClient
from dashboard_generator import DashboardGenerator
from models import Session
from data_utils import create_timestamped_data_dir, list_data_directories, get_data_directory_info
import constants



def download_sessions(limit=None):
    """Download session metadata to data directory."""
    print("OCS Session Download")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check for required environment variables
    api_key = os.getenv('OCS_API_KEY')
    if not api_key:
        print("Error: OCS_API_KEY environment variable is required")
        print("Please create a .env file with your API key")
        return 1
    
    # Initialize API client
    base_url = os.getenv('OCS_API_BASE_URL', constants.DEFAULT_API_BASE_URL)
    project_id = os.getenv('OCS_PROJECT_ID')
    
    print(f"API Base URL: {base_url}")
    if project_id:
        print(f"Project ID: {project_id}")
    
    client = OCSClient(api_key, base_url, project_id)
    
    try:
        print("Connecting to OpenChatStudio API...")
        
        # Move existing data to timestamped folder if any exists

        
        # Create new timestamped data directory
        timestamped_dir = create_timestamped_data_dir()
        sessions_dir = timestamped_dir / "sessions"
        
        print(f"Data will be saved to: {sessions_dir}")
        
        # Initialize counters
        saved_count = 0
        ecd_count = 0
        sessions_processed = 0
        
        def process_sessions_page(sessions_data, page, total_processed):
            """Process a page of sessions and write to disk immediately"""
            nonlocal saved_count, ecd_count, sessions_processed
            page_saved = 0
            page_ecd = 0
            
            for session_data in sessions_data:
                try:
                    # Parse session with models
                    session = Session.from_api_data(session_data)
                    
                    # Save to individual JSON file immediately
                    filepath = session.save_to_file(str(sessions_dir))
                    page_saved += 1
                    
                    # Count ECD sessions
                    if 'ecd' in session.experiment.name.lower():
                        page_ecd += 1
                    
                    sessions_processed += 1
                    
                    # If we have a limit and reached it, break
                    if limit and sessions_processed >= limit:
                        break
                        
                except Exception as e:
                    print(f"\n    Warning: Failed to process session {session_data.get('id', 'unknown')}: {e}")
            
            # Update global counters
            saved_count += page_saved
            ecd_count += page_ecd
            
            return page_saved
        
        # Download sessions with streaming
        if limit:
            print(f"Downloading first {limit} sessions...")
            max_pages = max(1, (limit + constants.PAGE_SIZE - 1) // constants.PAGE_SIZE)  # Ceiling division
            total_fetched = client.get_sessions_streaming(process_sessions_page, max_pages=max_pages)
        else:
            print("Downloading ALL sessions (this may take a while)...")
            total_fetched = client.get_sessions_streaming(process_sessions_page, max_pages=None)
        
        # Summary
        print("Data download complete!")
        print(f"Total sessions processed: {sessions_processed}")
        print(f"Successfully saved: {saved_count}")
        print(f"ECD sessions: {ecd_count}")
        print(f"Location: {sessions_dir}")
        

        
        return 0
        
    except Exception as e:
        print(f"Error downloading data: {e}")
        import traceback
        traceback.print_exc()
        return 1

def download_messages(limit=None):
    """Download message content for existing sessions."""
    print("OCS Messages Download")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check for required environment variables
    api_key = os.getenv('OCS_API_KEY')
    if not api_key:
        print("Error: OCS_API_KEY environment variable is required")
        print("Please create a .env file with your API key")
        return 1
    
    # Initialize API client
    base_url = os.getenv('OCS_API_BASE_URL', constants.DEFAULT_API_BASE_URL)
    project_id = os.getenv('OCS_PROJECT_ID')
    
    print(f"API Base URL: {base_url}")
    if project_id:
        print(f"Project ID: {project_id}")
    
    client = OCSClient(api_key, base_url, project_id)
    
    try:
        # Find the latest sessions directory
        from data_utils import get_latest_sessions_dir
        sessions_dir = get_latest_sessions_dir()
        
        if not sessions_dir:
            print("Error: No session data found. Please run 'download-sessions' first.")
            return 1
        
        print(f"Loading sessions from: {sessions_dir}")
        
        # Load existing sessions
        session_files = list(sessions_dir.glob("session_*.json"))
        if limit:
            session_files = session_files[:limit]
            print(f"Found {len(session_files)} session files (limited to {limit})")
        else:
            print(f"Found {len(session_files)} session files")
        
        if not session_files:
            print("No session files found. Please run 'download-sessions' first.")
            return 1
        
        # Create messages directory
        messages_dir = sessions_dir.parent / "messages"
        messages_dir.mkdir(exist_ok=True)
        
        print(f"Messages will be saved to: {messages_dir}")
        
        # Download messages for each session
        downloaded_count = 0
        skipped_count = 0
        error_count = 0
        
        for i, session_file in enumerate(session_files):
            try:
                # Extract session ID from filename
                session_id = session_file.stem.replace('session_', '')
                
                # Check if messages already exist
                message_file = messages_dir / f"messages_{session_id}.json"
                if message_file.exists():
                    skipped_count += 1
                    continue
                
                print(f"Downloading messages for session {i+1}/{len(session_files)}: {session_id}")
                
                # Fetch session details with messages
                session_detail = client.get_session_details(session_id)
                
                # Save messages to file
                with open(message_file, 'w', encoding='utf-8') as f:
                    json.dump(session_detail, f, indent=2, ensure_ascii=False)
                
                downloaded_count += 1
                
                # Progress update every 10 sessions
                if (i + 1) % 10 == 0:
                    print(f"  Progress: {i+1}/{len(session_files)} sessions processed")
                
            except Exception as e:
                print(f"  Warning: Failed to download messages for {session_id}: {e}")
                error_count += 1
        
        # Summary
        print("\nMessage download complete!")
        print(f"Downloaded: {downloaded_count}")
        print(f"Skipped (already exist): {skipped_count}")
        print(f"Errors: {error_count}")
        print(f"Location: {messages_dir}")
        
        return 0
        
    except Exception as e:
        print(f"Error downloading messages: {e}")
        import traceback
        traceback.print_exc()
        return 1

def generate_dashboard():
    """Generate dashboard from existing or fresh data."""
    print("OCS Dashboard Generator")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check for required environment variables
    api_key = os.getenv('OCS_API_KEY')
    if not api_key:
        print("Error: OCS_API_KEY environment variable is required")
        print("Please create a .env file with your API key")
        return 1
    
    # Initialize API client
    base_url = os.getenv('OCS_API_BASE_URL', constants.DEFAULT_API_BASE_URL)
    project_id = os.getenv('OCS_PROJECT_ID')
    
    if project_id:
        print(f"Using project: {project_id}")
    
    client = OCSClient(api_key, base_url, project_id)
    
    try:
        print("Connecting to OpenChatStudio API...")
        
        # Create output directory
        output_dir = Path(constants.OUTPUT_DIR)
        output_dir.mkdir(exist_ok=True)
        
        print(f"Generating dashboard to {output_dir}...")
        
        # Initialize dashboard generator
        generator = DashboardGenerator(client, output_dir)
        
        # Generate dashboard
        dashboard_path = generator.generate_dashboard()
        
        print(f"Dashboard generated: {dashboard_path}")
        
        # Open in browser
        if os.path.exists(dashboard_path):
            webbrowser.open(f"file://{os.path.abspath(dashboard_path)}")
            print("Dashboard opened in browser")
        
        return 0
        
    except Exception as e:
        print(f"Error generating dashboard: {e}")
        import traceback
        traceback.print_exc()
        return 1

def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description='OCS Dashboard Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_dashboard.py                           # Generate dashboard
  python run_dashboard.py download-sessions         # Download session metadata
  python run_dashboard.py download-sessions --limit 100  # Download first 100 sessions
  python run_dashboard.py download-messages         # Download message content for existing sessions
        """
    )
    
    parser.add_argument(
        'command', 
        nargs='?', 
        choices=['download-sessions', 'download-messages', 'generate'],
        default='generate',
        help='Command to run (default: generate)'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of sessions to process (for download-sessions and download-messages commands)'
    )
    
    args = parser.parse_args()
    
    # Route to appropriate function
    if args.command == 'download-sessions':
        return download_sessions(args.limit)
    elif args.command == 'download-messages':
        return download_messages(args.limit)
    else:  # generate or default
        return generate_dashboard()

if __name__ == "__main__":
    sys.exit(main())