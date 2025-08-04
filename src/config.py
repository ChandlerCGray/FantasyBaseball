"""
Configuration and constants for the Fantasy Baseball App
"""

# =============================================================================
# App Configuration
# =============================================================================
POSITIONS = ["C", "1B", "2B", "3B", "SS", "OF", "DH", "P"]
DEFAULT_TEAM = "Land of 10,000 Rakes"

# =============================================================================
# Muted Rainbow Color Palette
# =============================================================================
COLORS = {
    "primary": "#6B73FF",      # Muted blue
    "secondary": "#9B59B6",    # Muted purple  
    "success": "#52C41A",      # Muted green
    "warning": "#FA8C16",      # Muted orange
    "danger": "#FF4D4F",       # Muted red
    "info": "#1890FF",         # Muted cyan
    "light": "#F0F2F6",        # Light gray
    "dark": "#2C3E50",         # Dark blue-gray
    "muted": "#95A5A6",        # Muted gray
    "teal": "#20B2AA",         # Muted teal
    "pink": "#E91E63",         # Muted pink
    "indigo": "#6366F1"        # Muted indigo
}

# =============================================================================
# Streamlit Configuration
# =============================================================================
PAGE_CONFIG = {
    "page_title": "Fantasy Baseball Hub",
    "layout": "wide",
    "initial_sidebar_state": "auto",
    "menu_items": None  # Hide the hamburger menu
}

# =============================================================================
# Data Processing Constants
# =============================================================================
UPGRADE_THRESHOLDS = {
    "HIGH": 0.5,
    "MEDIUM": 0.25,
    "LOW": 0.1
}

PITCHER_ROLES = {"P", "SP", "RP", "CL", "PITCHER"}
HITTER_ROLES = {"C", "1B", "2B", "3B", "SS", "OF", "DH"}

POSITION_VARIATIONS = {
    "UTIL": "DH",
    "OUTFIELD": "OF",
    "FIRST": "1B",
    "SECOND": "2B",
    "THIRD": "3B",
    "SHORT": "SS",
    "CATCHER": "C"
}