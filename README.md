# OCSDashboardECD
Static dashboard generator for OpenChatStudio data. This project analyzes AI coaching sessions between bots and field workers (FLWs), providing insights into bot performance, session patterns, and annotation-based quality metrics.

## Overview
- **Purpose**: Monitor ECD bot performance and analyze session metadata and annotations
- **Data Source**: OpenChatStudio API (session metadata with annotation tags)
- **Output**: Static HTML dashboard with interactive charts using Plotly
- **Current Status**: ✅ Working dashboard with session analysis capabilities

## Quick Start

### 1. **Setup Virtual Environment** (Recommended)
   ```bash
   # Run the setup script (creates venv and installs dependencies)
   python setup.py
   
   # Activate virtual environment
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

### 2. **Configure API Access**
   ```bash
   # Edit .env file with your OpenChatStudio API key
   # The setup script creates a template for you
   ```

### 3. **Download Data**
   ```bash
   # Download all session data to timestamped data directory
   python run_dashboard.py download
   
   # Download limited sessions for testing
   python run_dashboard.py download --limit 1000
   ```

### 4. **Generate Dashboard**
   ```bash
   # Generate dashboard from downloaded data
   python run_dashboard.py
   ```

The dashboard will be generated in the `output/index.html` file and automatically opened in your browser.

## Dashboard Features

### ✅ **Current Metrics Available**
- **Session Overview**: Total sessions, experiments count, teams count, date ranges
- **Session Trends**: Sessions over time line chart
- **Experiment Analysis**: Sessions by experiment (horizontal bar chart)
- **Team Distribution**: Sessions by team (pie chart)
- **Annotation Analysis**: Quality tags when available in session data

### ✅ **Available Data**
- **Session Metadata**: IDs, timestamps, participant info, experiment details
- **Experiment Versions**: Version tracking and comparison across experiments
- **Quality Annotations**: Manual tags for bot performance, engagement, coaching quality
- **Team Organization**: Session distribution across different teams

### 📊 **Annotation Categories**
- **Bot Performance**: `bot_performance_good`, `bot_performance_bad`
- **User Engagement**: `engagement_good`, `engagement_bad` 
- **Coaching Quality**: `coaching_good`, `coaching_bad`, `coaching_undetermined`
- **Content Quality**: `safe`, `accurate`
- **User Knowledge**: `user_knowledge_good`, `user_knowledge_bad`

### ❌ **Currently Not Available** (Requires Additional API Calls)
- FLW ratings (1-5 scale)
- Message content and word counts
- Detailed conversation analysis

## Configuration

The setup script creates a `.env` file template. Edit it with your values:

```bash
# Required: Your OpenChatStudio API key
OCS_API_KEY=your_api_key_here

# Optional: API base URL (default shown)
OCS_API_BASE_URL=https://chatbots.dimagi.com/api

# Optional: Specific project ID to analyze
OCS_PROJECT_ID=your_project_id_here
```

### Getting Your API Key
1. Log into OpenChatStudio at https://chatbots.dimagi.com
2. Go to your user profile page
3. Generate an API key
4. Copy it to your `.env` file

**Note**: The API uses `X-API-KEY` header authentication, not Bearer token authentication.

## Commands

```bash
# Setup and activation
python setup.py                           # Initial setup with venv
python activate.py                        # Show activation commands

# API operations  
python run_dashboard.py download          # Download all session data
python run_dashboard.py download --limit 100  # Download limited sessions
python run_dashboard.py                   # Generate dashboard (default)

# Help
python run_dashboard.py --help            # Show all options
```

## Project Structure
```
├── run_dashboard.py          # Main entry point with CLI args
├── setup.py                  # Virtual environment setup
├── activate.py              # Cross-platform activation helper
├── requirements.txt          # Dependencies with version pinning
├── constants.py             # Configuration constants
├── .env                     # API credentials (created by setup)
├── env.example              # Environment template
├── venv/                    # Virtual environment (created by setup)
├── data/
│   └── YYYYMMDD_HHMMSS/     # Timestamped data directories
│       └── sessions/        # Downloaded session JSON files
├── output/
│   └── index.html           # Generated dashboard
└── src/
    ├── ocs_client.py        # OpenChatStudio API client
    ├── models.py            # Data models (Session, Experiment, etc.)
    ├── dashboard_generator.py # HTML dashboard generation with Plotly
    └── data_utils.py        # Data directory management utilities
```

## Data Architecture

### Session Data Structure
Each session contains:
- **Identifiers**: Unique session ID, participant identifier
- **Timestamps**: Created/updated timestamps for temporal analysis
- **Experiment Info**: Name, version, URL with full version history
- **Team Info**: Organizing team name and slug
- **Annotations**: Quality tags when manually reviewed
- **Participant**: Identifier (often email or anonymous ID)

### Timestamped Storage
- Data stored in `data/YYYYMMDD_HHMMSS/sessions/` directories
- Each session saved as individual JSON file: `session_{id}.json`
- Preserves historical downloads and enables data versioning

## Requirements
- **Python 3.8+** (3.10+ recommended)
- **OpenChatStudio API access key** with session read permissions
- **Internet connection** for initial data download
- **Virtual environment** (recommended for isolation)

## Similar Projects
This project follows the same structure and patterns as the [Coverage repository](https://github.com/jjackson/Coverage) for consistency and maintainability.