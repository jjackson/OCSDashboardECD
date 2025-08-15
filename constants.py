# OpenChatStudio Dashboard Constants

# API Configuration
DEFAULT_API_BASE_URL = "https://chatbots.dimagi.com/api"
API_VERSION = "v1"
USER_AGENT = "OCSDashboardECD/1.0"

# Environment variable names
API_KEY_ENV = "OCS_API_KEY"
PROJECT_ID_ENV = "OCS_PROJECT_ID"

# Dashboard Configuration
OUTPUT_DIR = "output"
TEMPLATE_DIR = "templates"
STATIC_DIR = "static"
DATA_DIR = "data"
# SESSIONS_DIR will be dynamically determined based on timestamp folders

# Chart Configuration
DEFAULT_CHART_HEIGHT = 400
DEFAULT_CHART_WIDTH = 800

# Rating Scale
FLW_RATING_MIN = 1
FLW_RATING_MAX = 5

# Pagination (OpenChatStudio uses cursor-based pagination)
PAGE_SIZE = 500  # Updated to download more files at once

# Target Experiments for Dashboard (experiments with active sessions)
TARGET_EXPERIMENTS = [
    "ECD Coach - Nigeria (Connect Experiments)",
    "ECD Control Bot - Nigeria - Connect Experiments", 
    "weekly survey pipeline - Nigeria -[Connect Experiments]"
]

# Experiment IDs (from active sessions)
EXPERIMENT_IDS = {
    "ECD Coach - Nigeria (Connect Experiments)": "e2b4855f-8550-47ff-87d2-d92018676ff3",
    "ECD Control Bot - Nigeria - Connect Experiments": "1027993a-40c9-4484-a5fb-5c7e034dadcd",
    "weekly survey pipeline - Nigeria -[Connect Experiments]": "3f2f429e-317c-4237-ac39-d5fedacdcfc8"
}
