"""
CSS Styles and UI styling for the Fantasy Baseball App
"""

from config import COLORS

def get_custom_css():
    """Return the custom CSS for the app"""
    expandable_css = get_expandable_tile_css().replace("<style>", "").replace("</style>", "")
    return f"""
<style>
    {expandable_css}
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Main container styling */
    .main .block-container {{
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 1400px;
        font-family: 'Inter', sans-serif;
    }}
    
    /* Sidebar styling */
    .css-1d391kg {{
        padding-top: 1rem;
        display: block !important;
        visibility: visible !important;
    }}
    
    /* Mobile-specific styling */
    @media (max-width: 768px) {{
        .main .block-container {{
            padding-top: 0.5rem;
            padding-bottom: 1rem;
            max-width: 100%;
        }}
        
        .tile {{
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 8px;
        }}
        
        .tile-rainbow-1, .tile-rainbow-2, .tile-rainbow-3, 
        .tile-rainbow-4, .tile-rainbow-5, .tile-rainbow-6 {{
            padding: 0.5rem;
            margin: 0.3rem 0;
            border-radius: 6px;
        }}
        
        /* Make buttons more touch-friendly */
        .stButton > button {{
            min-height: 44px;
            font-size: 16px;
        }}
        
        /* Improve mobile navigation */
        .mobile-nav {{
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            border-radius: 12px;
            padding: 1rem;
            margin: 1rem 0;
            border: 1px solid rgba(226, 232, 240, 0.8);
        }}
    }}
    
    /* Custom tile styling with muted rainbow 3D effects */
    .tile {{
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 6px 25px rgba(0, 0, 0, 0.1), 0 2px 8px rgba(0, 0, 0, 0.06);
        border: 1px solid rgba(226, 232, 240, 0.8);
        border-left: 4px solid {COLORS['primary']};
        transition: all 0.3s ease;
        position: relative;
    }}
    
    .tile:hover {{
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15), 0 4px 12px rgba(0, 0, 0, 0.08);
        border-left-width: 6px;
    }}
    
    /* Muted Rainbow Tile Variations with 3D Effects and Condensed Spacing */
    .tile-rainbow-1 {{
        background: linear-gradient(135deg, #ffffff 0%, #f0f9ff 100%);
        border-left: 3px solid #0ea5e9;
        box-shadow: 0 2px 8px rgba(14, 165, 233, 0.1), 0 1px 3px rgba(14, 165, 233, 0.05);
        border-radius: 6px;
        padding: 0.6rem;
        margin: 0.4rem 0;
        transition: all 0.2s ease;
        position: relative;
    }}
    
    .tile-rainbow-1:hover {{
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(14, 165, 233, 0.25), 0 4px 12px rgba(14, 165, 233, 0.12);
        border-left-color: #0284c7;
        border-left-width: 6px;
    }}
    
    .tile-rainbow-2 {{
        background: linear-gradient(135deg, #ffffff 0%, #f0fdf4 100%);
        border-left: 3px solid #22c55e;
        box-shadow: 0 2px 8px rgba(34, 197, 94, 0.1), 0 1px 3px rgba(34, 197, 94, 0.05);
        border-radius: 6px;
        padding: 0.6rem;
        margin: 0.4rem 0;
        transition: all 0.2s ease;
        position: relative;
    }}
    
    .tile-rainbow-2:hover {{
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(34, 197, 94, 0.25), 0 4px 12px rgba(34, 197, 94, 0.12);
        border-left-color: #16a34a;
        border-left-width: 6px;
    }}
    
    .tile-rainbow-3 {{
        background: linear-gradient(135deg, #ffffff 0%, #fefce8 100%);
        border-left: 3px solid #eab308;
        box-shadow: 0 2px 8px rgba(234, 179, 8, 0.1), 0 1px 3px rgba(234, 179, 8, 0.06);
        border-radius: 6px;
        padding: 0.6rem;
        margin: 0.4rem 0;
        transition: all 0.2s ease;
        position: relative;
    }}
    
    .tile-rainbow-3:hover {{
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(234, 179, 8, 0.25), 0 4px 12px rgba(234, 179, 8, 0.12);
        border-left-color: #ca8a04;
        border-left-width: 6px;
    }}
    
    .tile-rainbow-4 {{
        background: linear-gradient(135deg, #ffffff 0%, #fef2f2 100%);
        border-left: 3px solid #ef4444;
        box-shadow: 0 2px 8px rgba(239, 68, 68, 0.1), 0 1px 3px rgba(239, 68, 68, 0.05);
        border-radius: 6px;
        padding: 0.6rem;
        margin: 0.4rem 0;
        transition: all 0.2s ease;
        position: relative;
    }}
    
    .tile-rainbow-4:hover {{
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(239, 68, 68, 0.25), 0 4px 12px rgba(239, 68, 68, 0.12);
        border-left-color: #dc2626;
        border-left-width: 6px;
    }}
    
    .tile-rainbow-5 {{
        background: linear-gradient(135deg, #ffffff 0%, #faf5ff 100%);
        border-left: 4px solid #a855f7;
        box-shadow: 0 4px 15px rgba(168, 85, 247, 0.12), 0 2px 6px rgba(168, 85, 247, 0.06);
        border-radius: 8px;
        padding: 0.9rem;
        margin: 0.6rem 0;
        transition: all 0.3s ease;
        position: relative;
    }}
    
    .tile-rainbow-5:hover {{
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(168, 85, 247, 0.25), 0 4px 12px rgba(168, 85, 247, 0.12);
        border-left-color: #9333ea;
        border-left-width: 6px;
    }}
    
    .tile-rainbow-6 {{
        background: linear-gradient(135deg, #ffffff 0%, #fff7ed 100%);
        border-left: 4px solid #f97316;
        box-shadow: 0 4px 15px rgba(249, 115, 22, 0.12), 0 2px 6px rgba(249, 115, 22, 0.06);
        border-radius: 8px;
        padding: 0.9rem;
        margin: 0.6rem 0;
        transition: all 0.3s ease;
        position: relative;
    }}
    
    .tile-rainbow-6:hover {{
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(249, 115, 22, 0.25), 0 4px 12px rgba(249, 115, 22, 0.12);
        border-left-color: #ea580c;
        border-left-width: 6px;
    }}
    
    .tile-rainbow-7 {{
        background: linear-gradient(135deg, #ffffff 0%, #ecfdf5 100%);
        border-left: 4px solid #10b981;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.12), 0 2px 6px rgba(16, 185, 129, 0.06);
        border-radius: 8px;
        padding: 0.9rem;
        margin: 0.6rem 0;
        transition: all 0.3s ease;
        position: relative;
    }}
    
    .tile-rainbow-7:hover {{
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(16, 185, 129, 0.25), 0 4px 12px rgba(16, 185, 129, 0.12);
        border-left-color: #059669;
        border-left-width: 6px;
    }}
    
    .tile-rainbow-8 {{
        background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%);
        border-left: 4px solid #64748b;
        box-shadow: 0 4px 15px rgba(100, 116, 139, 0.12), 0 2px 6px rgba(100, 116, 139, 0.06);
        border-radius: 8px;
        padding: 0.9rem;
        margin: 0.6rem 0;
        transition: all 0.3s ease;
        position: relative;
    }}
    
    .tile-rainbow-8:hover {{
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(100, 116, 139, 0.25), 0 4px 12px rgba(100, 116, 139, 0.12);
        border-left-color: #475569;
        border-left-width: 6px;
    }}
    
    /* Priority tiles with high contrast and condensed spacing */
    .tile-high {{
        background: linear-gradient(135deg, #1e3a8a 0%, #3730a3 100%);
        color: white !important;
        padding: 1rem;
        margin: 0.6rem 0;
        border-radius: 8px;
    }}
    
    .tile-high * {{
        color: white !important;
    }}
    
    .tile-medium {{
        background: linear-gradient(135deg, #be185d 0%, #9f1239 100%);
        color: white !important;
        padding: 1rem;
        margin: 0.6rem 0;
        border-radius: 8px;
    }}
    
    .tile-medium * {{
        color: white !important;
    }}
    
    .tile-low {{
        background: linear-gradient(135deg, #0369a1 0%, #0284c7 100%);
        color: white !important;
        padding: 1.5rem;
        margin: 1rem 0;
    }}
    
    .tile-low * {{
        color: white !important;
    }}
    
    .tile-success {{
        background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
        color: {COLORS['dark']} !important;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 2px solid #16a34a;
    }}
    
    .tile-success * {{
        color: {COLORS['dark']} !important;
    }}
    
    .tile-warning {{
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        color: {COLORS['dark']} !important;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 2px solid #d97706;
    }}
    
    .tile-warning * {{
        color: {COLORS['dark']} !important;
    }}
    
    .tile-info {{
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
        color: {COLORS['dark']} !important;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 2px solid #2563eb;
    }}
    
    .tile-info * {{
        color: {COLORS['dark']} !important;
    }}
    
    /* Player card styling with consistent spacing */
    .player-card {{
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
        border-left: 4px solid {COLORS['primary']};
        transition: all 0.2s ease;
    }}
    
    .player-card:hover {{
        box-shadow: 0 6px 24px rgba(0, 0, 0, 0.12);
        transform: translateX(4px);
    }}
    
    .player-name {{
        font-size: 1.1rem;
        font-weight: 600;
        color: {COLORS['dark']};
        margin-bottom: 0.25rem;
    }}
    
    .player-stats {{
        font-size: 0.9rem;
        color: {COLORS['muted']};
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;
    }}
    
    .stat-badge {{
        background: {COLORS['light']};
        padding: 0.25rem 0.5rem;
        border-radius: 8px;
        font-size: 0.8rem;
        font-weight: 500;
    }}
    
    /* Position badges */
    .pos-C {{ background: linear-gradient(45deg, #FF6B6B, #FF8E8E); }}
    .pos-1B {{ background: linear-gradient(45deg, #4ECDC4, #44A08D); }}
    .pos-2B {{ background: linear-gradient(45deg, #45B7D1, #96C93D); }}
    .pos-3B {{ background: linear-gradient(45deg, #F7DC6F, #F4D03F); }}
    .pos-SS {{ background: linear-gradient(45deg, #BB8FCE, #8E44AD); }}
    .pos-OF {{ background: linear-gradient(45deg, #85C1E9, #3498DB); }}
    .pos-DH {{ background: linear-gradient(45deg, #F8C471, #E67E22); }}
    .pos-P {{ background: linear-gradient(45deg, #82E0AA, #27AE60); }}
    
    /* Mobile responsive */
    @media (max-width: 768px) {{
        .main .block-container {{
            padding-left: 1rem;
            padding-right: 1rem;
        }}
        
        .tile {{
            padding: 1rem;
            margin: 0.25rem 0;
        }}
        
        .player-stats {{
            flex-direction: column;
            gap: 0.5rem;
        }}
    }}
    
    /* Custom metric styling */
    .custom-metric {{
        text-align: center;
        padding: 1rem;
        border-radius: 12px;
        margin: 0.5rem;
    }}
    
    .metric-value {{
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }}
    
    .metric-label {{
        font-size: 0.9rem;
        opacity: 0.8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    /* Tab styling with better contrast */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 4px;
        background: rgba(248, 250, 252, 0.8);
        padding: 0.25rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        border-radius: 8px;
        padding: 0.75rem 1.25rem;
        background: transparent;
        border: none;
        color: {COLORS['dark']};
        font-weight: 500;
        transition: all 0.2s ease;
    }}
    
    .stTabs [data-baseweb="tab"]:hover {{
        background: rgba(99, 102, 241, 0.1);
        color: {COLORS['primary']};
    }}
    
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);
        color: white !important;
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
    }}
    
    /* Sidebar navigation styling */
    .sidebar-nav {{
        background: white;
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
        border: 1px solid rgba(226, 232, 240, 0.8);
    }}
    
    .nav-item {{
        display: block;
        padding: 0.75rem 1rem;
        margin: 0.25rem 0;
        border-radius: 8px;
        text-decoration: none;
        color: {COLORS['dark']};
        font-weight: 500;
        transition: all 0.2s ease;
        cursor: pointer;
        border: none;
        background: transparent;
        width: 100%;
        text-align: left;
    }}
    
    .nav-item:hover {{
        background: rgba(99, 102, 241, 0.1);
        color: {COLORS['primary']};
        transform: translateX(2px);
    }}
    
    .nav-item.active {{
        background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);
        color: white;
        font-weight: 600;
    }}
    
    /* Better spacing for content */
    .content-section {{
        margin: 2rem 0;
    }}
    
    .section-header {{
        color: {COLORS['dark']};
        font-weight: 600;
        margin-bottom: 1.5rem;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid {COLORS['light']};
    }}
    
    /* Global spacing utilities */
    .spacing-standard {{
        margin: 1rem 0;
        padding: 1.5rem;
    }}
    
    .spacing-large {{
        margin: 2rem 0;
        padding: 2rem;
    }}
    
    .spacing-small {{
        margin: 0.5rem 0;
        padding: 1rem;
    }}
    
    /* Improved metric tiles with consistent spacing */
    .metric-tile {{
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0.5rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        border: 1px solid rgba(226, 232, 240, 0.8);
        text-align: center;
        transition: all 0.2s ease;
    }}
    
    .metric-tile:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
    }}
    
    /* Hide default Streamlit tabs completely */
    .stTabs {{
        display: none !important;
    }}
    
    /* Hide any remaining tab elements */
    [data-testid="stTabs"] {{
        display: none !important;
    }}
    
    /* Hide tab list */
    [data-baseweb="tab-list"] {{
        display: none !important;
    }}
    
    /* Hide tab panels */
    [data-baseweb="tab-panel"] {{
        display: none !important;
    }}
    
    /* Hide Streamlit navigation menu */
    .css-1rs6os {{
        display: none !important;
    }}
    
    /* Hide main menu */
    #MainMenu {{
        display: none !important;
    }}
    
    /* Hide Streamlit header */
    header[data-testid="stHeader"] {{
        display: none !important;
    }}
    
    /* Hide footer */
    footer {{
        display: none !important;
    }}
    
    /* Hide "Deploy" button */
    .css-1rs6os .css-1rs6os {{
        display: none !important;
    }}
    
    /* Only hide Streamlit's auto-generated navigation */
    [data-testid="stSidebarNav"] {{
        display: none !important;
    }}
    
    /* Better text contrast */
    .high-contrast {{
        color: {COLORS['dark']} !important;
        font-weight: 600;
    }}
    
    .medium-contrast {{
        color: {COLORS['muted']} !important;
        font-weight: 500;
    }}
    
    /* Ensure all text in colored tiles has proper contrast */
    .tile-high, .tile-medium, .tile-low {{
        color: white !important;
    }}
    
    .tile-high *, .tile-medium *, .tile-low * {{
        color: white !important;
    }}
    
    .tile-success, .tile-warning, .tile-info {{
        color: {COLORS['dark']} !important;
    }}
    
    .tile-success *, .tile-warning *, .tile-info * {{
        color: {COLORS['dark']} !important;
    }}
    
    /* Fix any remaining contrast issues */
    .recommendation-section h3 {{
        color: {COLORS['dark']} !important;
    }}
    
    .priority-title {{
        color: {COLORS['dark']} !important;
    }}
    
    /* Ensure readable text on all backgrounds */
    .tile h1, .tile h2, .tile h3, .tile h4, .tile h5, .tile h6 {{
        color: inherit !important;
    }}
    
    .tile p, .tile span, .tile div {{
        color: inherit !important;
    }}
    
    /* Section separators */
    .section-divider {{
        height: 2px;
        background: linear-gradient(90deg, {COLORS['primary']} 0%, transparent 100%);
        margin: 2rem 0;
        border-radius: 1px;
    }}
    
    /* Improved recommendation tiles with consistent spacing */
    .recommendation-section {{
        background: white;
        border-radius: 16px;
        padding: 2rem;
        margin: 2rem 0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        border: 1px solid rgba(226, 232, 240, 0.8);
    }}
    
    .priority-header {{
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 2rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid {COLORS['light']};
    }}
    
    .priority-icon {{
        font-size: 1.5rem;
    }}
    
    .priority-title {{
        font-size: 1.25rem;
        font-weight: 600;
        color: {COLORS['dark']};
        margin: 0;
    }}
</style>
"""

def get_hero_section():
    """Return the hero section HTML with better spacing and contrast"""
    return """
    <div style="background: linear-gradient(135deg, #6B73FF 0%, #9B59B6 100%); 
                padding: 2.5rem 2rem; border-radius: 16px; margin-bottom: 2rem; text-align: center;
                box-shadow: 0 8px 32px rgba(107, 115, 255, 0.3);">
        <h1 style="color: white; margin: 0; font-size: 2.75rem; font-weight: 700; 
                   text-shadow: 0 2px 4px rgba(0,0,0,0.1); font-family: 'Inter', sans-serif;">
            ⚾ Fantasy Baseball Hub
        </h1>
        <p style="color: rgba(255,255,255,0.95); margin: 1rem 0 0 0; font-size: 1.2rem; 
                  font-weight: 400; text-shadow: 0 1px 2px rgba(0,0,0,0.1);">
            Smart Add/Drop Recommendations & Team Analysis
        </p>
    </div>
    """
def get_expandable_tile_css():
    """Return CSS for expandable tiles"""
    return """
<style>
    /* Expandable tile styles */
    .tile-expandable {
        transition: all 0.3s ease;
        cursor: pointer;
        overflow: hidden;
    }
    
    .tile-expanded {
        max-height: none;
    }
    
    .tile-collapsed {
        max-height: 120px;
        overflow: hidden;
    }
    
    .expand-indicator {
        text-align: center;
        font-size: 1.2rem;
        opacity: 0.7;
        margin-top: 0.5rem;
    }
    
    .expanded-content {
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px dashed rgba(203, 213, 225, 0.8);
        animation: fadeIn 0.3s ease-in-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
</style>
"""