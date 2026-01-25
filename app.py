"""
ZeroJournal - Trading Dashboard for Swing Traders
Main Streamlit application
Version: 1.5.0 - Enhanced MAE/MFE Analysis & Data Validation
"""

import streamlit as st
import pandas as pd

from services.excel_reader import read_tradebook, read_pnl
from services import metrics_calculator as mc
from services import sector_mapper
from utils.logger import logger

# Import components
from components.sidebar import (
    render_file_upload,
    render_navigation_buttons,
    render_portfolio_settings,
    render_filters,
    render_export_section
)

# Import page modules
from pages import mae_mfe_page
from pages import dashboard

# Page config
st.set_page_config(
    page_title="ZeroJournal - Trading Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Material Design Advanced CSS
st.markdown("""
<style>
    /* Import Roboto Font - Material Design Standard */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700;900&family=Roboto+Mono:wght@400;500;600&display=swap');
    
    /* Root Variables - Material Design Color Palette */
    :root {
        --md-primary: #1976d2;
        --md-primary-dark: #1565c0;
        --md-primary-light: #42a5f5;
        --md-secondary: #dc004e;
        --md-success: #4caf50;
        --md-warning: #ff9800;
        --md-error: #f44336;
        --md-info: #2196f3;
        --md-surface: #ffffff;
        --md-background: #f5f5f5;
        --md-text-primary: #212121;
        --md-text-secondary: #757575;
        --md-divider: #e0e0e0;
    }
    
    /* Main container styling - Material Design Elevation */
    .main {
        background: linear-gradient(135deg, #1976d2 0%, #1565c0 50%, #0d47a1 100%);
        background-attachment: fixed;
    }
    
    /* Content area - Material Design Card */
    .block-container {
        padding: 2rem 2.5rem;
        background: var(--md-surface);
        border-radius: 16px;
        margin: 1.5rem auto;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12), 0 2px 8px rgba(0, 0, 0, 0.08);
    }
    
    /* Headers - Material Design Typography */
    h1, h2, h3 {
        font-family: 'Roboto', sans-serif;
        font-weight: 500;
        letter-spacing: 0.015em;
        color: var(--md-text-primary);
    }
    
    h1 {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1976d2;
        margin-bottom: 2rem;
        line-height: 1.2;
    }
    
    h2 {
        font-size: 1.75rem;
        font-weight: 600;
        color: var(--md-text-primary);
        margin-top: 2.5rem;
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid var(--md-divider);
    }
    
    h3 {
        font-size: 1.25rem;
        font-weight: 500;
        color: var(--md-text-secondary);
        margin-top: 1rem;
    }
    
    /* Material Design Elevation - Metrics Container */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08), 0 1px 4px rgba(0, 0, 0, 0.04);
        border-left: 4px solid var(--md-primary);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12), 0 2px 8px rgba(0, 0, 0, 0.08);
    }
    
    /* Metrics styling - Material Design */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: var(--md-primary);
        font-family: 'Roboto', sans-serif;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.875rem;
        font-weight: 500;
        color: var(--md-text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-family: 'Roboto', sans-serif;
    }
    
    /* Metric delta styling */
    [data-testid="stMetricDelta"] {
        font-size: 0.95rem;
        font-weight: 600;
    }
    
    [data-testid="stMetricDelta"] svg {
        display: inline;
    }
    
    /* Material Design Alerts */
    .stAlert {
        border-radius: 8px;
        border: none;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        font-family: 'Roboto', sans-serif;
        font-weight: 400;
        padding: 1rem 1.25rem;
    }
    
    /* Success alert - Material Green */
    .stSuccess {
        background-color: #e8f5e9 !important;
        color: #1b5e20 !important;
        border-left: 4px solid var(--md-success) !important;
    }
    
    /* Info alert - Material Blue */
    .stInfo {
        background-color: #e3f2fd !important;
        color: #0d47a1 !important;
        border-left: 4px solid var(--md-info) !important;
    }
    
    /* Warning alert - Material Orange */
    .stWarning {
        background-color: #fff3e0 !important;
        color: #e65100 !important;
        border-left: 4px solid var(--md-warning) !important;
    }
    
    /* Error alert - Material Red */
    .stError {
        background-color: #ffebee !important;
        color: #b71c1c !important;
        border-left: 4px solid var(--md-error) !important;
    }
    
    /* Material Design Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1976d2 0%, #1565c0 50%, #0d47a1 100%);
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: white;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: white !important;
    }
    
    [data-testid="stSidebar"] label {
        color: white !important;
        font-weight: 500;
        font-family: 'Roboto', sans-serif;
        font-size: 0.875rem;
        letter-spacing: 0.05em;
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4 {
        color: white !important;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: white !important;
    }
    
    /* Sidebar input fields - Dark text on white background */
    [data-testid="stSidebar"] input {
        background: rgba(255, 255, 255, 0.95) !important;
        color: #212121 !important;
        border: 1px solid rgba(255, 255, 255, 0.5) !important;
        font-weight: 500 !important;
    }
    
    [data-testid="stSidebar"] input::placeholder {
        color: rgba(0, 0, 0, 0.5) !important;
    }
    
    /* Date input text visibility */
    [data-testid="stSidebar"] [data-baseweb="input"] input {
        color: #212121 !important;
    }
    
    /* Sidebar checkbox text - Fix white on white */
    [data-testid="stSidebar"] .stCheckbox label {
        color: white !important;
    }
    
    [data-testid="stSidebar"] .stCheckbox p {
        color: white !important;
    }
    
    /* Sidebar number input label - Fix white on white */
    [data-testid="stSidebar"] [data-testid="stNumberInput"] label {
        color: white !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stNumberInput"] p {
        color: white !important;
    }
    
    /* Sidebar metric labels and values - Fix visibility */
    [data-testid="stSidebar"] [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.15) !important;
        padding: 1rem !important;
        border-radius: 8px !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stMetricLabel"] {
        color: white !important;
        font-weight: 500 !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stMetricValue"] {
        color: white !important;
        font-size: 1.5rem !important;
        font-weight: 700 !important;
    }
    
    /* Material Design Buttons */
    .stButton button {
        background: var(--md-primary);
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        font-family: 'Roboto', sans-serif;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        transition: background-color 0.2s ease, box-shadow 0.2s ease;
    }
    
    .stButton button:hover {
        background: var(--md-primary-dark);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
    }
    
    /* Material Design Download buttons */
    [data-testid="stSidebar"] .stDownloadButton button {
        background: rgba(255, 255, 255, 0.12) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 4px;
        padding: 0.625rem 1rem;
        font-weight: 500;
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        width: 100%;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        transition: background-color 0.2s ease, box-shadow 0.2s ease;
        font-family: 'Roboto', sans-serif;
    }
    
    [data-testid="stSidebar"] .stDownloadButton button:hover {
        background: rgba(255, 255, 255, 0.2) !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
    }
    
    /* Selectbox dropdown - Scrollable */
    [data-baseweb="popover"] {
        max-height: 400px !important;
    }
    
    [data-baseweb="popover"] > div {
        max-height: 400px !important;
        overflow-y: auto !important;
    }
    
    [data-baseweb="select"] ul {
        max-height: 350px !important;
        overflow-y: auto !important;
        scrollbar-width: thin !important;
    }
    
    /* Style selectbox options */
    [role="option"] {
        padding: 12px 16px !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.15) !important;
    }
    
    [role="option"]:hover {
        background-color: rgba(255, 255, 255, 0.2) !important;
    }
    
    /* Scrollbar styling */
    [data-baseweb="select"] ul::-webkit-scrollbar {
        width: 8px !important;
    }
    
    [data-baseweb="select"] ul::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1) !important;
    }
    
    [data-baseweb="select"] ul::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.5) !important;
        border-radius: 4px !important;
    }
    
    [data-baseweb="select"] ul::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.7) !important;
    }
    
    [data-testid="stSidebar"] .stDownloadButton button:active {
        transform: translateY(0);
    }
    
    /* Material Design Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        padding: 0;
        border-bottom: 1px solid var(--md-divider);
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 0;
        padding: 1rem 2rem;
        background-color: transparent;
        font-weight: 500;
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-family: 'Roboto', sans-serif;
        color: var(--md-text-secondary);
        border-bottom: 2px solid transparent;
        transition: color 0.2s ease, border-color 0.2s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: var(--md-primary);
        background-color: rgba(25, 118, 210, 0.04);
    }
    
    .stTabs [aria-selected="true"] {
        color: var(--md-primary);
        border-bottom: 2px solid var(--md-primary);
        background-color: transparent;
    }
    
    /* Material Design Dataframe */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        border: 1px solid var(--md-divider);
        font-family: 'Roboto', sans-serif;
    }
    
    .dataframe thead th {
        background-color: #f5f5f5 !important;
        color: var(--md-text-primary) !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.05em;
    }
    
    .dataframe tbody tr:hover {
        background-color: rgba(25, 118, 210, 0.04) !important;
    }
    
    /* Material Design Plotly charts */
    .js-plotly-plot {
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        overflow: hidden;
        border: 1px solid var(--md-divider);
    }
    
    /* Material Design File uploader */
    [data-testid="stFileUploader"] {
        border-radius: 4px;
        border: 2px dashed rgba(255, 255, 255, 0.4);
        padding: 1rem;
        background: rgba(255, 255, 255, 0.08);
        transition: border-color 0.2s ease, background-color 0.2s ease;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: rgba(255, 255, 255, 0.7);
        background: rgba(255, 255, 255, 0.12);
    }
    
    /* Material Design Expander */
    .streamlit-expanderHeader {
        border-radius: 4px;
        font-weight: 500;
        font-family: 'Roboto', sans-serif;
        background-color: rgba(255, 255, 255, 0.08);
        transition: background-color 0.2s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background-color: rgba(255, 255, 255, 0.15);
    }
    
    /* Material Design Number input */
    [data-testid="stNumberInput"] input {
        border-radius: 4px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        font-weight: 500;
        font-family: 'Roboto Mono', monospace;
        background: rgba(255, 255, 255, 0.95);
        color: #212121;
    }
    
    [data-testid="stNumberInput"] input:focus {
        border-color: rgba(255, 255, 255, 1);
        box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.3);
    }
    
    /* Sidebar number input - Dark text */
    [data-testid="stSidebar"] [data-testid="stNumberInput"] input {
        background: rgba(255, 255, 255, 0.95) !important;
        color: #212121 !important;
    }
    
    /* Selectbox - Material Design */
    [data-testid="stSelectbox"] label {
        font-weight: 500;
        font-size: 0.875rem;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data(tradebook_file, pnl_file):
    """
    Load and parse Excel files.
    Cached to avoid re-reading files on every rerun.
    """
    tradebook_file.seek(0)  # Reset file pointer
    pnl_file.seek(0)  # Reset file pointer
    
    df_tradebook, error_tb = read_tradebook(tradebook_file)
    df_pnl, error_pnl, total_charges = read_pnl(pnl_file)
    
    if error_tb:
        return None, None, error_tb, error_pnl, 0.0
    if error_pnl:
        return df_tradebook, None, error_tb, error_pnl, 0.0
    
    return df_tradebook, df_pnl, None, None, total_charges


# Main Header with modern styling
st.markdown("""
<div style="text-align: center; padding: 1rem 0 2rem 0;">
    <h1 style="font-size: 3rem; margin-bottom: 0.5rem;">📈 ZeroJournal</h1>
    <p style="font-size: 1.2rem; color: #718096; font-weight: 500;">Advanced Trading Analytics Dashboard</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state FIRST (before any checks)
if 'tradebook_data' not in st.session_state:
    st.session_state.tradebook_data = None
if 'pnl_data' not in st.session_state:
    st.session_state.pnl_data = None
if 'total_charges' not in st.session_state:
    st.session_state.total_charges = 0.0
if 'initial_capital' not in st.session_state:
    st.session_state.initial_capital = 0.0
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'main'
if 'filtered_tradebook' not in st.session_state:
    st.session_state.filtered_tradebook = None
if 'filtered_pnl' not in st.session_state:
    st.session_state.filtered_pnl = None

# Sidebar - File Upload Section (only show if no files are loaded)
if st.session_state.tradebook_data is None or st.session_state.pnl_data is None:
    tradebook_file, pnl_file = render_file_upload()
else:
    render_navigation_buttons()
    tradebook_file = None
    pnl_file = None

# Load data when files are uploaded (only if not already loaded)
if tradebook_file is not None and pnl_file is not None and st.session_state.tradebook_data is None:
    with st.spinner("Loading and parsing Excel files..."):
        df_tb, df_pnl, error_tb, error_pnl, total_charges = load_data(tradebook_file, pnl_file)
        
        if error_tb or error_pnl:
            st.error(f"Error loading files: {error_tb or error_pnl}")
            st.session_state.tradebook_data = None
            st.session_state.pnl_data = None
            st.session_state.total_charges = 0.0
        else:
            st.session_state.tradebook_data = df_tb
            st.session_state.pnl_data = df_pnl
            st.session_state.total_charges = total_charges
            
            # Optimization 2: Pre-initialize NSE data (only once per session)
            if not st.session_state.get('master_loaded', False):
                try:
                    from openchart import NSEData
                    # Just initialize to warm up the connection
                    nse_data = NSEData()
                    st.session_state.master_loaded = True
                    logger.info("NSE data initialized successfully")
                except ImportError:
                    # openchart not available, skip
                    st.session_state.master_loaded = True
                except Exception as e:
                    logger.error(f"Error initializing NSE data: {e}")
                    st.session_state.master_loaded = True  # Mark as attempted to avoid retry
            
            st.rerun()  # Rerun to hide file uploaders

# Get data from session state
df_tradebook = st.session_state.tradebook_data
df_pnl = st.session_state.pnl_data

# Check if data is loaded
if df_tradebook is None or df_pnl is None:
    st.info("👈 Please upload both Excel files in the sidebar to begin analysis.")
    st.markdown("""
    ### Getting Started
    
    1. Upload your **Tradebook** Excel file (from Zerodha)
    2. Upload your **P&L Statement** Excel file (from Zerodha)
    3. The dashboard will automatically analyze your trading data
    
    ### Features
    
    - 📊 Performance Metrics (Win Rate, Profit Factor, Sharpe Ratio, etc.)
    - 📈 Interactive P&L Charts (Daily/Weekly/Monthly trends)
    - 📉 Equity Curve Visualization
    - 🏆 Top Winners/Losers Analysis
    - 📋 Trade Analysis (Win rate by symbol, holding periods)
    - 💾 Export filtered data to CSV/Excel
    """)
    st.stop()

# Dashboard-specific sidebar sections (only show on main dashboard page)
if st.session_state.current_page != 'mae_mfe':
    # Sidebar - Portfolio Settings
    initial_capital = render_portfolio_settings()
    
    # Sidebar - Filters Section
    filtered_tradebook, filtered_pnl, start_date, end_date, selected_symbols = render_filters(df_tradebook)
    
    # Export Section
    win_rate, profit_factor, avg_holding_period, sharpe_ratio, max_drawdown, daily_pnl, cumulative_pnl = render_export_section(
        filtered_tradebook, filtered_pnl, start_date, end_date
    )
else:
    # Initialize default values when on MAE/MFE page to avoid NameError
    # Note: These won't be used since st.stop() is called, but initialized for safety
    filtered_tradebook = df_tradebook if df_tradebook is not None else None
    filtered_pnl = df_pnl if df_pnl is not None else None
    start_date = None
    end_date = None
    selected_symbols = []
    initial_capital = st.session_state.initial_capital  # Use session state value
    # Initialize metrics to avoid NameError (though they won't be used due to st.stop())
    win_rate = 0.0
    profit_factor = 0.0
    avg_holding_period = 0.0
    sharpe_ratio = 0.0
    max_drawdown = 0.0
    daily_pnl = pd.DataFrame(columns=['Date', 'PnL'])
    cumulative_pnl = pd.DataFrame(columns=['Date', 'Cumulative P&L'])

# Store filtered data in session state BEFORE any page navigation
if filtered_tradebook is not None and filtered_pnl is not None:
    st.session_state.filtered_tradebook = filtered_tradebook
    st.session_state.filtered_pnl = filtered_pnl

# Show appropriate page based on session state
if st.session_state.current_page == 'mae_mfe':
    mae_mfe_page.show()
    st.stop()

# Main Content - Dashboard
if filtered_tradebook is not None and filtered_pnl is not None:
    dashboard.show(
        filtered_tradebook=filtered_tradebook,
        filtered_pnl=filtered_pnl,
        win_rate=win_rate,
        profit_factor=profit_factor,
        avg_holding_period=avg_holding_period,
        sharpe_ratio=sharpe_ratio,
        max_drawdown=max_drawdown,
        daily_pnl=daily_pnl,
        cumulative_pnl=cumulative_pnl,
        initial_capital=initial_capital
    )
else:
    st.warning("No data available. Please upload files in the sidebar.")
