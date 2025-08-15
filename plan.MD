# OCS Dashboard Project Plan

## Step 1: OpenChatStudio API Client (Similar to Coverage project approach)

**Background:**
OpenChatStudio is our open source AI chat agent platform. This dashboard will analyze transcripts recorded from AI coaching sessions between the bot and field workers (FLWs). These session transcripts are then tagged and annotated by Dimagi staff to evaluate coaching quality and effectiveness.

**References:**
- API docs: https://chatbots.dimagi.com/api/docs/
- Schema: https://github.com/dimagi/open-chat-studio/blob/main/api-schema.yml
- **Template repo**: https://github.com/jjackson/Coverage

## Framework Alignment with Coverage Project

**Use the same tools and patterns as the Coverage repository:**
- Same project structure (root-level entry points, src/ organization)
- Same dependency management approach (requirements.txt with version pinning)
- Same HTML generation patterns (if Coverage uses templates/static generation)
- Same configuration approach (.env files, constants.py)
- Same documentation style and README format
- Same build/deployment approach if applicable

**Key principle: Maintain consistency with existing Coverage codebase for easier maintenance and familiarity**

## Project Structure (matching Coverage repo pattern)

**Root files:**
- `requirements.txt` - Dependencies  
- `constants.py` - API URLs, default values
- `run_dashboard.py` - Main entry point (like run_coverage.py)
- `.env` - API credentials (gitignored)

**src/ directory:**
- `ocs_client.py` - API client class
- `models.py` - Data models 
- `dashboard_generator.py` - HTML generation
- `utils.py` - Helper functions

## Simple Implementation Plan

### 1. API Client (`src/ocs_client.py`)
- Single class `OCSClient` 
- Use `requests` library (keep it simple)
- Methods: `get_assistants()`, `get_conversations()`, `get_messages()`, etc.
- Handle auth with bearer token from `.env`
- Basic error handling and pagination

### 2. Data Models (`src/models.py`) 
- Simple Python dataclasses or basic classes
- Just the fields we need for dashboard
- No complex validation initially - get it working first

### 3. Entry Point (`run_dashboard.py`)
- Load config from `.env`
- Fetch data using OCSClient
- Generate HTML files to `output/` directory
- Auto-open in browser (like Coverage project)

### 4. Dependencies (`requirements.txt`)
```
requests
jinja2
python-dotenv
```

## Dashboard Requirements

### Goal
Build a dashboard that the team can use to monitor the success of new ECD OCS bot versions and analyze session tagging. We'd like to compare key metrics across versions to determine if new bot versions are in fact improving the coaching quality.

### Important Metrics

**Number of Sessions:**
- Total sessions
- Sessions over time (by session start date)

**FLW Rating:**
- Number of sessions rated
- % of sessions rated  
- Median rating from FLW (1-5 scale)

**User Engagement:**
- Median words by users (overall)
- Histogram of user word counts

**Annotations:**
- Total number of transcripts annotated
- Total number of transcripts annotated, disaggregated by coaching method
- % annotated of total sessions
- % unacceptable vs acceptable ratings
- % refrigerator example usage

**Visual Charts:**
- User engagement pie chart
- User knowledge pie chart

### Correlations to Explore
- FLW rating vs refrigerator example usage
- FLW rating vs human word count
- Human word count vs refrigerator example usage
- (More correlations to be added)

### Dashboard Filters (Apply Across All Charts)
- Bot/experiment ID
- Version ranges (ability to select from Vn to Vn)
- Coaching method (tag-based filtering)

### API Endpoints Needed
Based on these requirements, we'll need to identify endpoints for:
- Sessions/conversations with timestamps and ratings
- User messages with word counts
- Annotations and tags
- Bot version information
- Coaching method tags

This simplified approach gets us a working prototype quickly, then we can enhance it.


