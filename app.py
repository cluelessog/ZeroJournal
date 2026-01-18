"""
ZeroJournal - Trading Dashboard for Swing Traders
Main Streamlit application
Version: 1.4.0 - Advanced Metrics & Performance Trends
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
from streamlit_elements import elements, mui, html

from services.excel_reader import read_tradebook, read_pnl
from services import metrics_calculator as mc
from services import sector_mapper

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


def format_currency(value):
    """Format value as Indian Rupee currency."""
    if pd.isna(value):
        return "₹0.00"
    return f"₹{value:,.2f}"


def format_percentage(value):
    """Format value as percentage."""
    if pd.isna(value):
        return "0.00%"
    return f"{value:.2f}%"


# Main Header with modern styling
st.markdown("""
<div style="text-align: center; padding: 1rem 0 2rem 0;">
    <h1 style="font-size: 3rem; margin-bottom: 0.5rem;">📈 ZeroJournal</h1>
    <p style="font-size: 1.2rem; color: #718096; font-weight: 500;">Advanced Trading Analytics Dashboard</p>
</div>
""", unsafe_allow_html=True)

# Sidebar - File Upload Section
st.sidebar.header("📁 File Upload")

tradebook_file = st.sidebar.file_uploader(
    "Upload Tradebook Excel File",
    type=['xlsx', 'xls'],
    help="Upload your Zerodha tradebook Excel file"
)

pnl_file = st.sidebar.file_uploader(
    "Upload P&L Statement Excel File",
    type=['xlsx', 'xls'],
    help="Upload your Zerodha P&L statement Excel file"
)

# File format instructions
with st.sidebar.expander("ℹ️ File Format Info"):
    st.info("""
    **Expected Format:**
    - Zerodha tradebook and P&L Excel files
    - Files should have standard Zerodha export format
    
    **Required Columns:**
    - Tradebook: Symbol, ISIN, Trade Date, Trade Type, Quantity, Price
    - P&L: Symbol, ISIN, Quantity, Buy Value, Sell Value, Realized P&L
    """)

# Initialize session state
if 'tradebook_data' not in st.session_state:
    st.session_state.tradebook_data = None
if 'pnl_data' not in st.session_state:
    st.session_state.pnl_data = None
if 'total_charges' not in st.session_state:
    st.session_state.total_charges = 0.0
if 'initial_capital' not in st.session_state:
    st.session_state.initial_capital = 0.0

# Load data when files are uploaded
if tradebook_file is not None and pnl_file is not None:
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
            st.sidebar.success("✓ Files loaded successfully!")
else:
    st.session_state.tradebook_data = None
    st.session_state.pnl_data = None
    st.session_state.total_charges = 0.0

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

# Sidebar - Portfolio Settings
st.sidebar.header("💰 Portfolio Settings")

initial_capital = st.sidebar.number_input(
    "Initial Capital (₹)",
    min_value=0.0,
    value=float(st.session_state.initial_capital) if st.session_state.initial_capital > 0 else 0.0,
    step=1000.0,
    help="Enter your starting capital amount"
)
st.session_state.initial_capital = initial_capital

show_charges = st.sidebar.checkbox(
    "Show Total Charges",
    value=True,
    help="Display total charges paid"
)

if show_charges and st.session_state.total_charges > 0:
    st.sidebar.metric("Total Charges (All Trades)", format_currency(st.session_state.total_charges))
    
    # Show proportional charge allocation if filters are active
    if 'filtered_charges' in st.session_state and st.session_state.get('filtered_charges', 0) < st.session_state.total_charges:
        filtered_charges = st.session_state.filtered_charges
        ratio = st.session_state.get('charge_allocation_ratio', 0)
        st.sidebar.info(f"📊 Filtered charges: {format_currency(filtered_charges)} ({ratio:.1f}% of total)")
        st.sidebar.caption("Charges allocated proportionally by turnover")

# Sidebar - Filters Section
st.sidebar.header("🔍 Filters")

# Initialize enable_sector_filter
enable_sector_filter = False

# Optional: Enable Sector Filtering
if df_tradebook is not None:
    enable_sector_filter = st.sidebar.checkbox(
        "🏢 Enable Sector Filter",
        value=False,
        help="Fetch sector information from Yahoo Finance (may take a moment)"
    )
    
    if enable_sector_filter:
        if 'sector_map' not in st.session_state or not st.session_state.get('sectors_fetched', False):
            try:
                with st.spinner("Fetching sector information... This may take a moment."):
                    unique_symbols = df_tradebook['Symbol'].unique()
                    
                    # Show progress
                    progress_bar = st.sidebar.progress(0)
                    status_text = st.sidebar.empty()
                    
                    def update_progress(current, total):
                        progress = current / total
                        progress_bar.progress(progress)
                        status_text.markdown(f'<p style="color: white; font-weight: 500;">Fetching sectors: {current}/{total}</p>', unsafe_allow_html=True)
                    
                    sector_map = sector_mapper.get_sectors_for_symbols(unique_symbols, update_progress)
                    st.session_state.sector_map = sector_map
                    st.session_state.sectors_fetched = True
                    
                    # Clear progress indicators
                    progress_bar.empty()
                    status_text.empty()
                    st.sidebar.success(f"✓ Fetched sectors for {len(sector_map)} symbols")
            except Exception as e:
                st.sidebar.error(f"⚠️ Error fetching sectors: {str(e)}")
                st.session_state.sector_map = {}
                st.session_state.sectors_fetched = False
    else:
        # Clear sector data if disabled
        if 'sector_map' in st.session_state:
            del st.session_state.sector_map
            st.session_state.sectors_fetched = False

# Date range filter
if df_tradebook is not None:
    min_date = df_tradebook['Trade Date'].min().date()
    max_date = df_tradebook['Trade Date'].max().date()
    
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        help="Select date range for analysis"
    )
    
    # Handle single date selection
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        # Ensure start_date <= end_date
        if start_date > end_date:
            start_date, end_date = end_date, start_date
    else:
        start_date = min_date
        end_date = max_date
    
    # Filter by date range
    filtered_tradebook = df_tradebook[
        (df_tradebook['Trade Date'].dt.date >= start_date) &
        (df_tradebook['Trade Date'].dt.date <= end_date)
    ].copy()
    
    # Get all available symbols for independent filtering
    all_available_symbols = sorted(df_tradebook['Symbol'].unique().tolist())
    
    # Initialize independent filters
    selected_sectors = []
    selected_symbols = []
    
    # Sector Filter (independent, optional) - Single Select
    if enable_sector_filter:
        if 'sector_map' in st.session_state and st.session_state.sector_map:
            sector_map = st.session_state.sector_map
            available_sectors = sorted(set(sector_map.values()))
            available_sectors = [s for s in available_sectors if s != 'Unknown']
            
            if available_sectors:
                # Add "All Sectors" as the first option
                sector_options = ["All Sectors"] + available_sectors
                
                # Initialize selected sector in session state
                if 'selected_sector' not in st.session_state:
                    st.session_state.selected_sector = "All Sectors"
                
                # Use a different key approach to force refresh on reset
                selected_sector = st.sidebar.selectbox(
                    "Filter by Sector",
                    options=sector_options,
                    index=sector_options.index(st.session_state.selected_sector) if st.session_state.selected_sector in sector_options else 0,
                    key="sector_selectbox_" + str(st.session_state.get('filter_reset_counter', 0)),
                    help="Select a specific sector to filter (All Sectors = show all)"
                )
                
                # Update session state when selection changes
                st.session_state.selected_sector = selected_sector
                
                # Convert to list format for filtering logic
                if selected_sector == "All Sectors":
                    selected_sectors = []
                else:
                    selected_sectors = [selected_sector]
            else:
                st.sidebar.warning("⚠️ No sectors found. All symbols marked as 'Unknown'.")
                selected_sectors = []
        else:
            st.sidebar.info("ℹ️ Enable sector filter to fetch sector data.")
            selected_sectors = []
    else:
        selected_sectors = []
    
    # Symbol Filter (independent) - Single Select
    # Add "All Stocks" as the first option
    symbol_options = ["All Stocks"] + all_available_symbols
    
    # Initialize selected symbol in session state
    if 'selected_symbol' not in st.session_state:
        st.session_state.selected_symbol = "All Stocks"
    
    # Reset button for all filters (symbol + sector)
    if st.sidebar.button("🔄 Reset Filters", key="reset_filters_btn", use_container_width=True, help="Reset all filters (sector & symbol)"):
        st.session_state.selected_symbol = "All Stocks"
        st.session_state.selected_sector = "All Sectors"
        # Increment counter to force widget refresh
        if 'filter_reset_counter' not in st.session_state:
            st.session_state.filter_reset_counter = 0
        st.session_state.filter_reset_counter += 1
        st.rerun()
    
    # Get the index for the current selection
    try:
        current_index = symbol_options.index(st.session_state.selected_symbol)
    except ValueError:
        current_index = 0
        st.session_state.selected_symbol = "All Stocks"
    
    selected_symbol = st.sidebar.selectbox(
        "Filter by Symbol",
        options=symbol_options,
        index=current_index,
        key="symbol_selectbox",
        help="Select a specific symbol to filter (All Stocks = show all)"
    )
    
    # Update session state when selection changes
    if selected_symbol != st.session_state.selected_symbol:
        st.session_state.selected_symbol = selected_symbol
    
    # Convert to list format for filtering logic
    if selected_symbol == "All Stocks":
        selected_symbols = []
    else:
        selected_symbols = [selected_symbol]
    
    # Apply BOTH filters independently to the date-filtered data
    # Start with date-filtered data
    filtered_by_date = filtered_tradebook.copy()
    filtered_pnl_by_date = df_pnl.copy()
    
    # Apply sector filter (if enabled and sector selected)
    if enable_sector_filter and selected_sectors and 'sector_map' in st.session_state:
        sector_map = st.session_state.sector_map
        # selected_sectors is now a list with one sector or empty
        symbols_in_selected_sectors = [sym for sym in all_available_symbols 
                                      if sector_map.get(sym, 'Unknown') in selected_sectors]
        filtered_by_date = filtered_by_date[filtered_by_date['Symbol'].isin(symbols_in_selected_sectors)]
        filtered_pnl_by_date = filtered_pnl_by_date[filtered_pnl_by_date['Symbol'].isin(symbols_in_selected_sectors)]
    
    # Apply symbol filter (if symbols selected)
    if selected_symbols:
        # Filter by selected symbols
        filtered_tradebook = filtered_by_date[filtered_by_date['Symbol'].isin(selected_symbols)]
        filtered_pnl = filtered_pnl_by_date[filtered_pnl_by_date['Symbol'].isin(selected_symbols)].copy()
    else:
        # When no symbols selected (empty/reset state), show ALL stocks
        # This ensures all stocks are displayed by default
        filtered_tradebook = filtered_by_date.copy()
        filtered_pnl = filtered_pnl_by_date.copy()
    
    # Show filter status - Active Filters Indicator
    st.sidebar.markdown("---")
    st.sidebar.subheader("📌 Active Filters")
    
    active_filters = []
    if start_date and end_date:
        active_filters.append(f"📅 Date: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    if enable_sector_filter and selected_sectors:
        active_filters.append(f"🏢 Sector: {selected_sectors[0]}")
    if selected_symbols:
        active_filters.append(f"📊 Symbol: {selected_symbols[0]}")
    
    if active_filters:
        for filter_text in active_filters:
            st.sidebar.info(filter_text)
        
        # Show filtered data stats
        unique_symbols_count = len(filtered_tradebook['Symbol'].unique()) if len(filtered_tradebook) > 0 else 0
        st.sidebar.success(f"✓ {len(filtered_tradebook)} trades | {unique_symbols_count} symbols")
    else:
        st.sidebar.info("ℹ️ No filters active - showing all data")
        unique_symbols_count = len(filtered_tradebook['Symbol'].unique()) if len(filtered_tradebook) > 0 else 0
        st.sidebar.success(f"Total: {len(filtered_tradebook)} trades | {unique_symbols_count} symbols")
else:
    filtered_tradebook = df_tradebook
    filtered_pnl = df_pnl
    start_date = None
    end_date = None
    selected_symbols = []

# Export Section
st.sidebar.header("💾 Export Data")

# Calculate metrics for filtered data
if filtered_tradebook is not None and filtered_pnl is not None:
    # Check if dataframes are empty
    has_tradebook_data = len(filtered_tradebook) > 0
    has_pnl_data = len(filtered_pnl) > 0
    
    # Get daily P&L for filtered data
    if has_pnl_data and has_tradebook_data:
        daily_pnl = mc.get_daily_pnl_from_pnl_data(filtered_pnl, filtered_tradebook)
    else:
        daily_pnl = pd.DataFrame(columns=['Date', 'PnL'])
    
    if len(daily_pnl) == 0 and has_tradebook_data:
        # Fallback to tradebook-based calculation
        daily_pnl = mc.get_daily_pnl(filtered_tradebook)
    
    # Distribute charges pro-rata by daily turnover (proportional to filtered data)
    if len(daily_pnl) > 0 and st.session_state.total_charges > 0:
        # Calculate proportional charges based on filtered turnover vs total turnover
        if df_tradebook is not None and len(df_tradebook) > 0:
            # Calculate turnover for filtered data
            filtered_turnover = mc.calculate_daily_turnover(filtered_tradebook)['Turnover'].sum() if len(filtered_tradebook) > 0 else 0
            
            # Calculate total turnover from all data
            total_turnover_df = mc.calculate_daily_turnover(df_tradebook)
            total_turnover = total_turnover_df['Turnover'].sum() if len(total_turnover_df) > 0 else 0
            
            # Proportional charges for filtered data
            if total_turnover > 0:
                proportional_charges = st.session_state.total_charges * (filtered_turnover / total_turnover)
            else:
                proportional_charges = 0
        else:
            proportional_charges = st.session_state.total_charges
        
        daily_pnl = mc.distribute_charges_pro_rata(
            daily_pnl, 
            filtered_tradebook, 
            proportional_charges,
            dp_charges_dict=None  # Can be enhanced to extract DP charge dates
        )
        
        # Store charge info for display
        st.session_state.filtered_charges = proportional_charges
        st.session_state.charge_allocation_ratio = (filtered_turnover / total_turnover * 100) if total_turnover > 0 else 0
    
    # Calculate metrics (safely handle empty dataframes)
    # Use FIFO-matched trades for consistent win rate calculation
    if has_tradebook_data:
        # Get matched trades for win rate calculation
        matched_trades = mc.match_trades_with_pnl(filtered_tradebook)
        if len(matched_trades) > 0:
            wins = sum(1 for _, pnl, _ in matched_trades if pnl > 0)
            win_rate = (wins / len(matched_trades)) * 100
        else:
            win_rate = 0.0
    else:
        win_rate = 0.0
    
    # Profit factor still from P&L data (aggregated is fine for this metric)
    if has_pnl_data:
        profit_factor = mc.calculate_profit_factor(filtered_pnl)
    else:
        profit_factor = 0.0
    
    if has_tradebook_data:
        avg_holding_period = mc.calculate_avg_holding_period(filtered_tradebook)
    else:
        avg_holding_period = 0.0
    
    cumulative_pnl = mc.get_cumulative_pnl(daily_pnl)
    sharpe_ratio = mc.calculate_sharpe_ratio(daily_pnl)
    max_drawdown = mc.calculate_max_drawdown(cumulative_pnl)
    
    # Export filtered tradebook (only if data exists)
    if has_tradebook_data:
        csv_tb = filtered_tradebook.to_csv(index=False)
        date_str = f"{start_date}_{end_date}" if start_date and end_date else "all_data"
        st.sidebar.download_button(
            label="📥 Export Tradebook (CSV)",
            data=csv_tb,
            file_name=f"tradebook_filtered_{date_str}.csv",
            mime="text/csv"
        )
    else:
        st.sidebar.info("No tradebook data to export")
    
    # Export filtered P&L (only if data exists)
    if has_pnl_data:
        csv_pnl = filtered_pnl.to_csv(index=False)
        date_str = f"{start_date}_{end_date}" if start_date and end_date else "all_data"
        st.sidebar.download_button(
            label="📥 Export P&L (CSV)",
            data=csv_pnl,
            file_name=f"pnl_filtered_{date_str}.csv",
            mime="text/csv"
        )
    else:
        st.sidebar.info("No P&L data to export")
else:
    st.sidebar.info("Upload files to enable export")
    # Set default values for metrics to avoid NameError
    win_rate = 0.0
    profit_factor = 0.0
    avg_holding_period = 0.0
    sharpe_ratio = 0.0
    max_drawdown = 0.0
    daily_pnl = pd.DataFrame(columns=['Date', 'PnL'])
    cumulative_pnl = pd.DataFrame(columns=['Date', 'Cumulative P&L'])

# Main Content - Dashboard
if filtered_tradebook is not None and filtered_pnl is not None:
    # Check if we have any data to display
    has_data = len(filtered_tradebook) > 0 or len(filtered_pnl) > 0
    
    if not has_data:
        st.warning("⚠️ No data available for the selected filters. Please adjust your date range or symbol filters.")
        st.stop()
    
    # Key Insights Section (moved to top)
    if len(filtered_tradebook) > 0:
        st.markdown("---")
        st.markdown("### 💡 Key Insights")
        
        # Calculate advanced metrics for insights
        expectancy_data = mc.calculate_expectancy(filtered_tradebook)
        risk_reward_data = mc.calculate_risk_reward_ratio(filtered_tradebook)
        streaks_data = mc.calculate_consecutive_streaks(filtered_tradebook)
        
        exp_overall = expectancy_data['overall']['expectancy']
        exp_intraday = expectancy_data['intraday']['expectancy']
        exp_swing = expectancy_data['swing']['expectancy']
        rr_overall = risk_reward_data['overall']['ratio']
        
        insights = []
        
        # Expectancy insights
        if exp_overall > 0:
            insights.append(f"✅ **Positive Expectancy**: Your system has a positive edge of ₹{exp_overall:.2f} per trade.")
        else:
            insights.append(f"⚠️ **Negative Expectancy**: Your system loses ₹{abs(exp_overall):.2f} per trade on average. Review your strategy.")
        
        # Compare intraday vs swing
        if exp_intraday > exp_swing and exp_intraday > 0:
            insights.append(f"📊 **Intraday is more profitable** (₹{exp_intraday:.2f}) than Swing (₹{exp_swing:.2f}). Consider focusing on intraday.")
        elif exp_swing > exp_intraday and exp_swing > 0:
            insights.append(f"📊 **Swing is more profitable** (₹{exp_swing:.2f}) than Intraday (₹{exp_intraday:.2f}). Consider focusing on swing trades.")
        
        # Risk-Reward insights
        if rr_overall < 1.0:
            insights.append(f"⚠️ **Poor Risk-Reward**: Your average win (₹{risk_reward_data['overall']['avg_win']:.2f}) is smaller than average loss (₹{risk_reward_data['overall']['avg_loss']:.2f}). Let winners run longer!")
        elif rr_overall > 2.0:
            insights.append(f"✅ **Excellent Risk-Reward**: You're cutting losses and letting winners run. Keep it up!")
        
        # Streak insights
        if streaks_data['overall']['max_loss_streak'] > 5:
            insights.append(f"⚠️ **High Loss Streak**: You've had {streaks_data['overall']['max_loss_streak']} consecutive losses. Prepare mentally for such drawdowns.")
        
        # Trading Style Recommendations
        sentiment_data = mc.calculate_holding_sentiment(filtered_tradebook)
        if sentiment_data['recommendation'] and (sentiment_data['best_style'] or sentiment_data['worst_style']):
            insights.append(f"🎯 **Trading Style**: {sentiment_data['recommendation']}")
        
        for insight in insights:
            st.info(insight)
    
    st.markdown("---")
    
    # Quick Navigation Buttons - Material Design
    st.markdown("### 🧭 Quick Navigation")
    
    # Custom CSS for Material Design Navigation Buttons
    st.markdown("""
        <style>
        .nav-container {
            display: flex;
            gap: 16px;
            margin: 24px 0;
            flex-wrap: wrap;
            justify-content: space-between;
        }
        .nav-button {
            flex: 1;
            min-width: 180px;
            background: #ffffff;
            color: #1a1a1a;
            padding: 24px 20px;
            border-radius: 16px;
            text-align: center;
            text-decoration: none;
            font-weight: 500;
            font-size: 14px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08), 0 1px 4px rgba(0, 0, 0, 0.04);
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            cursor: pointer;
            border: 1px solid rgba(0, 0, 0, 0.05);
            position: relative;
            overflow: hidden;
        }
        .nav-button:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.12), 0 4px 8px rgba(0, 0, 0, 0.08);
            border-color: rgba(0, 0, 0, 0.1);
        }
        .nav-button:active {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1), 0 2px 4px rgba(0, 0, 0, 0.06);
        }
        .nav-button .icon {
            font-size: 32px;
            display: block;
            margin-bottom: 12px;
            transition: transform 0.2s ease;
        }
        .nav-button:hover .icon {
            transform: scale(1.1);
        }
        .nav-button .label {
            display: block;
            font-size: 14px;
            color: #424242;
            font-weight: 500;
            letter-spacing: 0.25px;
        }
        .nav-button-1 .icon {
            color: #6750A4;
        }
        .nav-button-1:hover {
            background: #F5F3FF;
        }
        .nav-button-2 .icon {
            color: #E91E63;
        }
        .nav-button-2:hover {
            background: #FCE4EC;
        }
        .nav-button-3 .icon {
            color: #2196F3;
        }
        .nav-button-3:hover {
            background: #E3F2FD;
        }
        .nav-button-4 .icon {
            color: #4CAF50;
        }
        .nav-button-4:hover {
            background: #E8F5E9;
        }
        .nav-button-5 .icon {
            color: #FF9800;
        }
        .nav-button-5:hover {
            background: #FFF3E0;
        }
        .nav-button-6 .icon {
            color: #00BCD4;
        }
        .nav-button-6:hover {
            background: #E0F7FA;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Navigation Buttons HTML
    st.markdown("""
        <div class="nav-container">
            <a href="#performance-metrics" class="nav-button nav-button-1">
                <span class="icon">📊</span>
                <span class="label">Performance Metrics</span>
            </a>
            <a href="#performance-trends" class="nav-button nav-button-6">
                <span class="icon">📈</span>
                <span class="label">Performance Trends</span>
            </a>
            <a href="#p-l-analysis" class="nav-button nav-button-2">
                <span class="icon">💹</span>
                <span class="label">P&L Analysis</span>
            </a>
            <a href="#top-winners-losers" class="nav-button nav-button-3">
                <span class="icon">🏆</span>
                <span class="label">Top Winners & Losers</span>
            </a>
            <a href="#trade-analysis" class="nav-button nav-button-4">
                <span class="icon">📋</span>
                <span class="label">Trade Analysis</span>
            </a>
            <a href="#trading-style-performance" class="nav-button nav-button-5">
                <span class="icon">⏱️</span>
                <span class="label">Trading Style</span>
            </a>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Section 1: Performance Metrics
    st.header("📊 Performance Metrics")
    st.markdown('<div id="performance-metrics"></div>', unsafe_allow_html=True)
    
    # Material-UI Grid Layout for Performance Metrics
    with elements("performance_metrics"):
        with mui.Grid(container=True, spacing=2):
            # Win Rate
            with mui.Grid(item=True, xs=12, sm=6, md=2.4):
                with mui.Paper(elevation=2, sx={"p": 2.5, "borderLeft": "4px solid #4caf50", "borderRadius": "8px", "height": "100%"}):
                    mui.Typography("Win Rate", variant="caption", sx={"color": "#757575", "textTransform": "uppercase", "letterSpacing": "0.1em", "fontWeight": 500, "fontSize": "0.75rem"})
                    mui.Typography(f"{win_rate:.2f}%", variant="h4", sx={"fontWeight": 700, "color": "#4caf50", "mt": 1, "fontSize": "1.75rem"})
            
            # Profit Factor
            with mui.Grid(item=True, xs=12, sm=6, md=2.4):
                pf_display = f"{profit_factor:.2f}" if profit_factor != float('inf') else "∞"
                with mui.Paper(elevation=2, sx={"p": 2.5, "borderLeft": "4px solid #2196f3", "borderRadius": "8px", "height": "100%"}):
                    mui.Typography("Profit Factor", variant="caption", sx={"color": "#757575", "textTransform": "uppercase", "letterSpacing": "0.1em", "fontWeight": 500, "fontSize": "0.75rem"})
                    mui.Typography(pf_display, variant="h4", sx={"fontWeight": 700, "color": "#2196f3", "mt": 1, "fontSize": "1.75rem"})
            
            # Avg Holding Period
            with mui.Grid(item=True, xs=12, sm=6, md=2.4):
                with mui.Paper(elevation=2, sx={"p": 2.5, "borderLeft": "4px solid #ff9800", "borderRadius": "8px", "height": "100%"}):
                    mui.Typography("Avg Holding", variant="caption", sx={"color": "#757575", "textTransform": "uppercase", "letterSpacing": "0.1em", "fontWeight": 500, "fontSize": "0.75rem"})
                    mui.Typography(f"{avg_holding_period:.1f}d", variant="h4", sx={"fontWeight": 700, "color": "#ff9800", "mt": 1, "fontSize": "1.75rem"})
            
            # Sharpe Ratio
            with mui.Grid(item=True, xs=12, sm=6, md=2.4):
                with mui.Paper(elevation=2, sx={"p": 2.5, "borderLeft": "4px solid #9c27b0", "borderRadius": "8px", "height": "100%"}):
                    mui.Typography("Sharpe Ratio", variant="caption", sx={"color": "#757575", "textTransform": "uppercase", "letterSpacing": "0.1em", "fontWeight": 500, "fontSize": "0.75rem"})
                    mui.Typography(f"{sharpe_ratio:.2f}", variant="h4", sx={"fontWeight": 700, "color": "#9c27b0", "mt": 1, "fontSize": "1.75rem"})
            
            # Max Drawdown
            with mui.Grid(item=True, xs=12, sm=6, md=2.4):
                with mui.Paper(elevation=2, sx={"p": 2.5, "borderLeft": "4px solid #f44336", "borderRadius": "8px", "height": "100%"}):
                    mui.Typography("Max Drawdown", variant="caption", sx={"color": "#757575", "textTransform": "uppercase", "letterSpacing": "0.1em", "fontWeight": 500, "fontSize": "0.75rem"})
                    mui.Typography(format_currency(max_drawdown), variant="h4", sx={"fontWeight": 700, "color": "#f44336", "mt": 1, "fontSize": "1.5rem"})
    
    # Advanced Metrics Section - Expectancy, Risk-Reward, Streaks
    st.markdown("---")
    st.subheader("🎯 Advanced Performance Metrics")
    
    if len(filtered_tradebook) > 0:
        # Calculate advanced metrics
        expectancy_data = mc.calculate_expectancy(filtered_tradebook)
        risk_reward_data = mc.calculate_risk_reward_ratio(filtered_tradebook)
        streaks_data = mc.calculate_consecutive_streaks(filtered_tradebook)
        
        # Create three columns for the three metric types
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### 💰 Expectancy (₹/Trade)")
            st.caption("Expected value per trade - must be positive for profitability")
            
            # Overall
            exp_overall = expectancy_data['overall']['expectancy']
            exp_color = "🟢" if exp_overall > 0 else "🔴"
            st.metric(
                "Overall", 
                f"₹{exp_overall:.2f}",
                delta=None,
                help="(Win Rate × Avg Win) - (Loss Rate × Avg Loss)"
            )
            
            # Intraday
            exp_intraday = expectancy_data['intraday']['expectancy']
            exp_intraday_color = "🟢" if exp_intraday > 0 else "🔴"
            st.metric(
                f"{exp_intraday_color} Intraday", 
                f"₹{exp_intraday:.2f}",
                help=f"Avg Win: ₹{expectancy_data['intraday']['avg_win']:.2f} | Avg Loss: ₹{expectancy_data['intraday']['avg_loss']:.2f}"
            )
            
            # Swing
            exp_swing = expectancy_data['swing']['expectancy']
            exp_swing_color = "🟢" if exp_swing > 0 else "🔴"
            st.metric(
                f"{exp_swing_color} Swing", 
                f"₹{exp_swing:.2f}",
                help=f"Avg Win: ₹{expectancy_data['swing']['avg_win']:.2f} | Avg Loss: ₹{expectancy_data['swing']['avg_loss']:.2f}"
            )
        
        with col2:
            st.markdown("#### ⚖️ Risk-Reward Ratio")
            st.caption("Avg Win ÷ Avg Loss - higher is better (>1.5 ideal)")
            
            # Overall
            rr_overall = risk_reward_data['overall']['ratio']
            rr_display = f"{rr_overall:.2f}" if rr_overall != float('inf') else "∞"
            rr_color = "🟢" if rr_overall > 1.5 else "🟡" if rr_overall > 1.0 else "🔴"
            st.metric(
                "Overall", 
                rr_display,
                delta=None,
                help=f"Avg Win: ₹{risk_reward_data['overall']['avg_win']:.2f} | Avg Loss: ₹{risk_reward_data['overall']['avg_loss']:.2f}"
            )
            
            # Intraday
            rr_intraday = risk_reward_data['intraday']['ratio']
            rr_intraday_display = f"{rr_intraday:.2f}" if rr_intraday != float('inf') else "∞"
            rr_intraday_color = "🟢" if rr_intraday > 1.5 else "🟡" if rr_intraday > 1.0 else "🔴"
            st.metric(
                f"{rr_intraday_color} Intraday", 
                rr_intraday_display,
                help=f"Avg Win: ₹{risk_reward_data['intraday']['avg_win']:.2f} | Avg Loss: ₹{risk_reward_data['intraday']['avg_loss']:.2f}"
            )
            
            # Swing
            rr_swing = risk_reward_data['swing']['ratio']
            rr_swing_display = f"{rr_swing:.2f}" if rr_swing != float('inf') else "∞"
            rr_swing_color = "🟢" if rr_swing > 1.5 else "🟡" if rr_swing > 1.0 else "🔴"
            st.metric(
                f"{rr_swing_color} Swing", 
                rr_swing_display,
                help=f"Avg Win: ₹{risk_reward_data['swing']['avg_win']:.2f} | Avg Loss: ₹{risk_reward_data['swing']['avg_loss']:.2f}"
            )
        
        with col3:
            st.markdown("#### 🔥 Consecutive Streaks")
            st.caption("Longest winning and losing streaks")
            
            # Overall
            st.markdown(f"**Overall**")
            st.markdown(f"✅ Max Win Streak: **{streaks_data['overall']['max_win_streak']}** trades")
            st.markdown(f"❌ Max Loss Streak: **{streaks_data['overall']['max_loss_streak']}** trades")
            st.markdown(f"📊 Current: **{streaks_data['overall']['current_streak']}** ({streaks_data['overall']['current_type']})")
            
            st.markdown("---")
            
            # Intraday
            st.markdown(f"**Intraday**")
            st.markdown(f"✅ Win: **{streaks_data['intraday']['max_win_streak']}** | ❌ Loss: **{streaks_data['intraday']['max_loss_streak']}**")
            
            # Swing
            st.markdown(f"**Swing**")
            st.markdown(f"✅ Win: **{streaks_data['swing']['max_win_streak']}** | ❌ Loss: **{streaks_data['swing']['max_loss_streak']}**")
        
    
    # Performance Trends Section - Time Series Analysis
    st.markdown("---")
    st.header("📊 Performance Trends Over Time")
    st.markdown('<div id="performance-trends"></div>', unsafe_allow_html=True)
    st.caption("Analyze how your trading metrics have evolved over time to identify improvement or degradation")
    
    if len(filtered_tradebook) > 0:
        # Priority 1: Rolling Expectancy Chart
        st.subheader("📈 Rolling Expectancy (20-Trade Window)")
        st.markdown("""
        This chart shows your **expected profit per trade** calculated over rolling 20-trade windows.
        - **Above zero line** = profitable system
        - **Upward trend** = improving performance
        - **Downward trend** = degrading strategy or changing market conditions
        """)
        
        rolling_exp = mc.calculate_rolling_expectancy(filtered_tradebook, window=20)
        
        if len(rolling_exp) > 0:
            fig_rolling = go.Figure()
            
            # Overall expectancy
            fig_rolling.add_trace(go.Scatter(
                x=rolling_exp['trade_number'],
                y=rolling_exp['expectancy_overall'],
                name='Overall',
                mode='lines',
                line=dict(color='#1976d2', width=3),
                hovertemplate='Trade #%{x}<br>Expectancy: ₹%{y:.2f}<extra></extra>'
            ))
            
            # Intraday expectancy (if available)
            if rolling_exp['expectancy_intraday'].notna().any():
                fig_rolling.add_trace(go.Scatter(
                    x=rolling_exp['trade_number'],
                    y=rolling_exp['expectancy_intraday'],
                    name='Intraday',
                    mode='lines',
                    line=dict(color='#ff9800', width=2, dash='dot'),
                    hovertemplate='Trade #%{x}<br>Intraday Expectancy: ₹%{y:.2f}<extra></extra>'
                ))
            
            # Swing expectancy (if available)
            if rolling_exp['expectancy_swing'].notna().any():
                fig_rolling.add_trace(go.Scatter(
                    x=rolling_exp['trade_number'],
                    y=rolling_exp['expectancy_swing'],
                    name='Swing',
                    mode='lines',
                    line=dict(color='#4caf50', width=2, dash='dash'),
                    hovertemplate='Trade #%{x}<br>Swing Expectancy: ₹%{y:.2f}<extra></extra>'
                ))
            
            # Zero line
            fig_rolling.add_hline(y=0, line_dash="solid", line_color="red", 
                                 annotation_text="Break-even", 
                                 annotation_position="right")
            
            # Set y-axis range with padding for better visibility
            all_expectancy_values = rolling_exp['expectancy_overall'].dropna().tolist()
            if rolling_exp['expectancy_intraday'].notna().any():
                all_expectancy_values.extend(rolling_exp['expectancy_intraday'].dropna().tolist())
            if rolling_exp['expectancy_swing'].notna().any():
                all_expectancy_values.extend(rolling_exp['expectancy_swing'].dropna().tolist())
            
            if len(all_expectancy_values) > 0:
                y_min = min(all_expectancy_values)
                y_max = max(all_expectancy_values)
                y_range = y_max - y_min
                # Add 30% padding on each side
                y_axis_min = y_min - (y_range * 0.3) if y_range > 0 else y_min - 100
                y_axis_max = y_max + (y_range * 0.3) if y_range > 0 else y_max + 100
            else:
                y_axis_min = None
                y_axis_max = None
            
            fig_rolling.update_layout(
                title='Rolling 20-Trade Expectancy',
                xaxis_title='Trade Number',
                yaxis_title='Expectancy (₹)',
                yaxis=dict(range=[y_axis_min, y_axis_max]) if y_axis_min is not None else {},
                hovermode='x unified',
                showlegend=True,
                height=550,
                template='plotly_white'
            )
            
            st.plotly_chart(fig_rolling, use_container_width=True)
            
            # Insights
            current_exp = rolling_exp.iloc[-1]['expectancy_overall']
            first_exp = rolling_exp.iloc[0]['expectancy_overall']
            trend = "improving" if current_exp > first_exp else "declining"
            trend_icon = "📈" if current_exp > first_exp else "📉"
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current 20-Trade Expectancy", f"₹{current_exp:.2f}")
            with col2:
                st.metric("Initial 20-Trade Expectancy", f"₹{first_exp:.2f}")
            with col3:
                delta = current_exp - first_exp
                st.metric("Trend", f"{trend_icon} {trend.capitalize()}", delta=f"₹{delta:.2f}")
        else:
            st.info("Need at least 20 completed trades to show rolling expectancy. Keep trading!")
        
        st.markdown("---")
        
        # Priority 2: Monthly Expectancy Comparison
        st.subheader("📅 Monthly Expectancy Comparison")
        st.markdown("""
        Compare your **Intraday vs Swing** performance month by month.
        - Identify which months you perform best
        - Spot seasonal patterns
        - See if you're consistently improving
        """)
        
        monthly_exp = mc.calculate_monthly_expectancy(filtered_tradebook)
        
        if len(monthly_exp) > 0:
            fig_monthly = go.Figure()
            
            # Intraday bars
            intraday_data = monthly_exp[monthly_exp['expectancy_intraday'].notna()]
            if len(intraday_data) > 0:
                fig_monthly.add_trace(go.Bar(
                    x=intraday_data['month'],
                    y=intraday_data['expectancy_intraday'],
                    name='Intraday',
                    marker_color='#ff9800',
                    hovertemplate='%{x|%b %Y}<br>Intraday: ₹%{y:.2f}<br>Trades: ' + 
                                 intraday_data['trade_count_intraday'].astype(str) + '<extra></extra>'
                ))
            
            # Swing bars
            swing_data = monthly_exp[monthly_exp['expectancy_swing'].notna()]
            if len(swing_data) > 0:
                fig_monthly.add_trace(go.Bar(
                    x=swing_data['month'],
                    y=swing_data['expectancy_swing'],
                    name='Swing',
                    marker_color='#4caf50',
                    hovertemplate='%{x|%b %Y}<br>Swing: ₹%{y:.2f}<br>Trades: ' + 
                                 swing_data['trade_count_swing'].astype(str) + '<extra></extra>'
                ))
            
            # Overall line
            fig_monthly.add_trace(go.Scatter(
                x=monthly_exp['month'],
                y=monthly_exp['expectancy_overall'],
                name='Overall',
                mode='lines+markers',
                line=dict(color='#1976d2', width=3),
                marker=dict(size=8),
                hovertemplate='%{x|%b %Y}<br>Overall: ₹%{y:.2f}<extra></extra>'
            ))
            
            # Zero line
            fig_monthly.add_hline(y=0, line_dash="solid", line_color="red", 
                                 annotation_text="Break-even")
            
            fig_monthly.update_layout(
                title='Monthly Expectancy: Intraday vs Swing',
                xaxis_title='Month',
                yaxis_title='Expectancy (₹)',
                barmode='group',
                hovermode='x unified',
                showlegend=True,
                height=500,
                template='plotly_white'
            )
            
            st.plotly_chart(fig_monthly, use_container_width=True)
            
            # Monthly insights
            best_month = monthly_exp.loc[monthly_exp['expectancy_overall'].idxmax()]
            worst_month = monthly_exp.loc[monthly_exp['expectancy_overall'].idxmin()]
            
            col1, col2 = st.columns(2)
            with col1:
                st.success(f"🏆 **Best Month**: {best_month['month'].strftime('%B %Y')} (₹{best_month['expectancy_overall']:.2f})")
            with col2:
                st.error(f"📉 **Worst Month**: {worst_month['month'].strftime('%B %Y')} (₹{worst_month['expectancy_overall']:.2f})")
        else:
            st.info("No monthly data available yet.")
        
        st.markdown("---")
        
        # Priority 3: Cumulative Metrics Dashboard
        st.subheader("📊 Cumulative Performance Evolution")
        st.markdown("""
        Watch how your metrics **stabilize over time** as you accumulate more trades.
        Shows your **learning curve** and overall trajectory.
        """)
        
        cumulative_metrics = mc.calculate_cumulative_metrics(filtered_tradebook)
        
        if len(cumulative_metrics) > 0:
            # Create 2x2 grid of charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Cumulative Win Rate
                fig_wr = go.Figure()
                fig_wr.add_trace(go.Scatter(
                    x=cumulative_metrics['trade_number'],
                    y=cumulative_metrics['win_rate'],
                    mode='lines',
                    line=dict(color='#2196f3', width=2),
                    fill='tozeroy',
                    fillcolor='rgba(33, 150, 243, 0.1)',
                    hovertemplate='Trade #%{x}<br>Win Rate: %{y:.1f}%<extra></extra>'
                ))
                fig_wr.add_hline(y=50, line_dash="dash", line_color="gray", 
                                annotation_text="50%")
                
                # Set y-axis range for better visibility (0-100% with padding)
                wr_values = cumulative_metrics['win_rate'].dropna().tolist()
                if len(wr_values) > 0:
                    wr_min = max(0, min(wr_values) - 10)
                    wr_max = min(100, max(wr_values) + 10)
                    y_axis_range = [wr_min, wr_max]
                else:
                    y_axis_range = [0, 100]
                
                fig_wr.update_layout(
                    title='Cumulative Win Rate',
                    xaxis_title='Trade Number',
                    yaxis_title='Win Rate (%)',
                    yaxis=dict(range=y_axis_range),
                    height=400,
                    template='plotly_white',
                    showlegend=False
                )
                st.plotly_chart(fig_wr, use_container_width=True)
            
            with col2:
                # Cumulative Profit Factor
                fig_pf = go.Figure()
                pf_data = cumulative_metrics[cumulative_metrics['profit_factor'].notna()].copy()
                
                # Cap extreme values for better visualization (display max 5)
                pf_data['profit_factor_display'] = pf_data['profit_factor'].clip(upper=5)
                
                fig_pf.add_trace(go.Scatter(
                    x=pf_data['trade_number'],
                    y=pf_data['profit_factor_display'],
                    mode='lines',
                    line=dict(color='#9c27b0', width=2),
                    fill='tozeroy',
                    fillcolor='rgba(156, 39, 176, 0.1)',
                    customdata=pf_data['profit_factor'],
                    hovertemplate='Trade #%{x}<br>Profit Factor: %{customdata:.2f}<extra></extra>'
                ))
                fig_pf.add_hline(y=1.0, line_dash="dash", line_color="red", 
                                annotation_text="Break-even", annotation_position="right")
                fig_pf.add_hline(y=2.0, line_dash="dash", line_color="green", 
                                annotation_text="Good (2.0)", annotation_position="right")
                fig_pf.update_layout(
                    title='Cumulative Profit Factor (capped at 5 for visibility)',
                    xaxis_title='Trade Number',
                    yaxis_title='Profit Factor',
                    yaxis=dict(range=[0, 5]),
                    height=400,
                    template='plotly_white',
                    showlegend=False
                )
                st.plotly_chart(fig_pf, use_container_width=True)
            
            col3, col4 = st.columns(2)
            
            with col3:
                # Cumulative Risk-Reward
                fig_rr = go.Figure()
                rr_data = cumulative_metrics[cumulative_metrics['risk_reward'].notna()].copy()
                
                # Filter extreme outliers for better visualization (cap at 5 for display)
                rr_data['risk_reward_display'] = rr_data['risk_reward'].clip(upper=5)
                
                fig_rr.add_trace(go.Scatter(
                    x=rr_data['trade_number'],
                    y=rr_data['risk_reward_display'],
                    mode='lines',
                    line=dict(color='#ff5722', width=2),
                    fill='tozeroy',
                    fillcolor='rgba(255, 87, 34, 0.1)',
                    customdata=rr_data['risk_reward'],
                    hovertemplate='Trade #%{x}<br>R:R Ratio: %{customdata:.2f}<extra></extra>'
                ))
                fig_rr.add_hline(y=1.0, line_dash="dash", line_color="red", 
                                annotation_text="1:1", annotation_position="right")
                fig_rr.add_hline(y=1.5, line_dash="dash", line_color="green", 
                                annotation_text="Ideal (1.5)", annotation_position="right")
                
                # Set y-axis range with sensible limits (0 to 5)
                rr_values = rr_data['risk_reward_display'].tolist()
                if len(rr_values) > 0:
                    rr_min = 0
                    rr_max = min(5, max(rr_values) * 1.1)  # Cap at 5 maximum
                    y_axis_range = [rr_min, max(rr_max, 2.0)]  # At least show up to 2.0
                else:
                    y_axis_range = [0, 3]
                
                fig_rr.update_layout(
                    title='Cumulative Risk-Reward Ratio (capped at 5 for visibility)',
                    xaxis_title='Trade Number',
                    yaxis_title='R:R Ratio',
                    yaxis=dict(range=y_axis_range),
                    height=400,
                    template='plotly_white',
                    showlegend=False
                )
                st.plotly_chart(fig_rr, use_container_width=True)
            
            with col4:
                # Cumulative Expectancy
                fig_exp = go.Figure()
                fig_exp.add_trace(go.Scatter(
                    x=cumulative_metrics['trade_number'],
                    y=cumulative_metrics['expectancy'],
                    mode='lines',
                    line=dict(color='#4caf50', width=2),
                    fill='tozeroy',
                    fillcolor='rgba(76, 175, 80, 0.1)',
                    hovertemplate='Trade #%{x}<br>Expectancy: ₹%{y:.2f}<extra></extra>'
                ))
                fig_exp.add_hline(y=0, line_dash="solid", line_color="red", 
                                 annotation_text="Break-even")
                
                # Set y-axis range with padding for better visibility
                exp_values = cumulative_metrics['expectancy'].dropna().tolist()
                if len(exp_values) > 0:
                    exp_min = min(exp_values)
                    exp_max = max(exp_values)
                    exp_range = exp_max - exp_min
                    # Add 30% padding on each side
                    y_axis_min = exp_min - (exp_range * 0.3) if exp_range > 0 else exp_min - 50
                    y_axis_max = exp_max + (exp_range * 0.3) if exp_range > 0 else exp_max + 50
                else:
                    y_axis_min = -100
                    y_axis_max = 100
                
                fig_exp.update_layout(
                    title='Cumulative Expectancy',
                    xaxis_title='Trade Number',
                    yaxis_title='Expectancy (₹)',
                    yaxis=dict(range=[y_axis_min, y_axis_max]),
                    height=400,
                    template='plotly_white',
                    showlegend=False
                )
                st.plotly_chart(fig_exp, use_container_width=True)
            
            # Final metrics summary
            final = cumulative_metrics.iloc[-1]
            st.markdown("### 📋 Current Cumulative Metrics")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Win Rate", f"{final['win_rate']:.1f}%")
            with col2:
                pf_display = f"{final['profit_factor']:.2f}" if pd.notna(final['profit_factor']) else "N/A"
                st.metric("Profit Factor", pf_display)
            with col3:
                rr_display = f"{final['risk_reward']:.2f}" if pd.notna(final['risk_reward']) else "N/A"
                st.metric("Risk-Reward", rr_display)
            with col4:
                st.metric("Expectancy", f"₹{final['expectancy']:.2f}")
        else:
            st.info("No cumulative data available yet.")
    
    # Section 2: P&L Analysis
    st.markdown("---")
    st.header("📈 P&L Analysis")
    st.markdown('<div id="p-l-analysis"></div>', unsafe_allow_html=True)
    
    # Equity Curve
    if len(daily_pnl) > 0:
        equity_curve = mc.get_equity_curve(daily_pnl, initial_value=initial_capital)
        
        fig_equity = px.line(
            equity_curve,
            x='Date',
            y='Equity',
            title='Interactive Equity Curve',
            labels={'Equity': 'Portfolio Value (₹)', 'Date': 'Date'}
        )
        fig_equity.update_traces(line_color='#1f77b4', line_width=2)
        fig_equity.update_layout(
            hovermode='x unified',
            xaxis_title="Date",
            yaxis_title="Portfolio Value (₹)",
            height=400
        )
        st.plotly_chart(fig_equity, use_container_width=True)
        
        # Daily/Weekly/Monthly P&L Tabs
        tab1, tab2, tab3, tab4 = st.tabs(["Daily P&L", "Weekly P&L", "Monthly P&L", "Cumulative P&L"])
        
        with tab1:
            fig_daily = px.bar(
                daily_pnl,
                x='Date',
                y='PnL',
                title='Daily P&L Trend',
                labels={'PnL': 'P&L (₹)', 'Date': 'Date'},
                color='PnL',
                color_continuous_scale=['red', 'green']
            )
            fig_daily.update_layout(height=400, xaxis_title="Date", yaxis_title="P&L (₹)")
            st.plotly_chart(fig_daily, use_container_width=True)
        
        with tab2:
            weekly_pnl = mc.get_weekly_pnl(daily_pnl)
            if len(weekly_pnl) > 0:
                fig_weekly = px.bar(
                    weekly_pnl,
                    x='Week',
                    y='PnL',
                    title='Weekly P&L Trend',
                    labels={'PnL': 'P&L (₹)', 'Week': 'Week'},
                    color='PnL',
                    color_continuous_scale=['red', 'green']
                )
                fig_weekly.update_layout(height=400, xaxis_title="Week", yaxis_title="P&L (₹)")
                st.plotly_chart(fig_weekly, use_container_width=True)
            else:
                st.info("No weekly data available")
        
        with tab3:
            monthly_pnl = mc.get_monthly_pnl(daily_pnl)
            if len(monthly_pnl) > 0:
                fig_monthly = px.bar(
                    monthly_pnl,
                    x='Month',
                    y='PnL',
                    title='Monthly P&L Trend',
                    labels={'PnL': 'P&L (₹)', 'Month': 'Month'},
                    color='PnL',
                    color_continuous_scale=['red', 'green']
                )
                fig_monthly.update_layout(height=400, xaxis_title="Month", yaxis_title="P&L (₹)")
                st.plotly_chart(fig_monthly, use_container_width=True)
            else:
                st.info("No monthly data available")
        
        with tab4:
            if len(cumulative_pnl) > 0:
                fig_cumulative = px.line(
                    cumulative_pnl,
                    x='Date',
                    y='Cumulative P&L',
                    title='Cumulative P&L Over Time',
                    labels={'Cumulative P&L': 'Cumulative P&L (₹)', 'Date': 'Date'}
                )
                fig_cumulative.update_traces(line_color='#2ca02c', line_width=2)
                fig_cumulative.update_layout(height=400, xaxis_title="Date", yaxis_title="Cumulative P&L (₹)")
                st.plotly_chart(fig_cumulative, use_container_width=True)
            else:
                st.info("No cumulative P&L data available")
    
    # Section 3: Top Winners/Losers
    st.markdown("---")
    st.header("🏆 Top Winners & Losers")
    st.markdown('<div id="top-winners-losers"></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top 10 Winners")
        if len(filtered_pnl) > 0 and 'Realized P&L' in filtered_pnl.columns:
            top_count = min(10, len(filtered_pnl))
            top_winners = filtered_pnl.nlargest(top_count, 'Realized P&L')[
                ['Symbol', 'Quantity', 'Buy Value', 'Sell Value', 'Realized P&L', 'Realized P&L Pct.']
            ]
            top_winners['Realized P&L'] = top_winners['Realized P&L'].apply(format_currency)
            top_winners['Buy Value'] = top_winners['Buy Value'].apply(format_currency)
            top_winners['Sell Value'] = top_winners['Sell Value'].apply(format_currency)
            top_winners['Realized P&L Pct.'] = top_winners['Realized P&L Pct.'].apply(format_percentage)
            st.dataframe(top_winners, use_container_width=True, hide_index=True)
        else:
            st.info("No winners data available")
    
    with col2:
        st.subheader("Top 10 Losers")
        if len(filtered_pnl) > 0 and 'Realized P&L' in filtered_pnl.columns:
            top_count = min(10, len(filtered_pnl))
            top_losers = filtered_pnl.nsmallest(top_count, 'Realized P&L')[
                ['Symbol', 'Quantity', 'Buy Value', 'Sell Value', 'Realized P&L', 'Realized P&L Pct.']
            ]
            top_losers['Realized P&L'] = top_losers['Realized P&L'].apply(format_currency)
            top_losers['Buy Value'] = top_losers['Buy Value'].apply(format_currency)
            top_losers['Sell Value'] = top_losers['Sell Value'].apply(format_currency)
            top_losers['Realized P&L Pct.'] = top_losers['Realized P&L Pct.'].apply(format_percentage)
            st.dataframe(top_losers, use_container_width=True, hide_index=True)
        else:
            st.info("No losers data available")
    
    # Section 4: Trade Analysis
    st.markdown("---")
    st.header("📋 Trade Analysis")
    st.markdown('<div id="trade-analysis"></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Win Rate by Symbol (20 Worst)")
        win_rate_by_symbol = mc.get_win_rate_by_symbol(filtered_pnl, filtered_tradebook)
        if len(win_rate_by_symbol) > 0:
            # Get top 20 stocks with worst win rate
            worst_performers = win_rate_by_symbol.nsmallest(20, 'Win Rate %')
            fig_win_rate = px.bar(
                worst_performers,
                x='Win Rate %',
                y='Symbol',
                orientation='h',
                title='Top 20 Stocks with Worst Win Rate',
                labels={'Win Rate %': 'Win Rate (%)', 'Symbol': 'Symbol'},
                color='Win Rate %',
                color_continuous_scale=['#f44336', '#ff9800', '#ffc107']
            )
            fig_win_rate.update_layout(height=600, xaxis_title="Win Rate (%)", yaxis_title="Symbol")
            st.plotly_chart(fig_win_rate, use_container_width=True)
        else:
            st.info("No data available")
    
    with col2:
        st.subheader("Average Holding Period by Stock")
        holding_periods = mc.get_avg_holding_period_by_stock(filtered_tradebook)
        if len(holding_periods) > 0:
            fig_holding = px.bar(
                holding_periods.head(20),
                x='Avg Holding Period (Days)',
                y='Symbol',
                orientation='h',
                title='Average Holding Period by Stock (Top 20)',
                labels={'Avg Holding Period (Days)': 'Days', 'Symbol': 'Symbol'}
            )
            fig_holding.update_layout(height=600, xaxis_title="Average Holding Period (Days)", yaxis_title="Symbol")
            st.plotly_chart(fig_holding, use_container_width=True)
        else:
            st.info("No data available")
    
    # Section 5: Trading Style Performance
    st.markdown("---")
    st.header("⏱️ Trading Style Performance")
    st.markdown('<div id="trading-style-performance"></div>', unsafe_allow_html=True)
    sentiment_data = mc.calculate_holding_sentiment(filtered_tradebook)
    
    # Calculate correct total (Pure Swing is a superset, not a separate category)
    total_analyzed = (sentiment_data['intraday']['count'] + 
                     sentiment_data['btst']['count'] + 
                     sentiment_data['velocity']['count'] + 
                     sentiment_data['swing']['count'])
    
    # Explanation for trade count difference
    total_entries = len(filtered_tradebook) if len(filtered_tradebook) > 0 else 0
    buy_count = len(filtered_tradebook[filtered_tradebook['Trade Type'] == 'buy']) if len(filtered_tradebook) > 0 else 0
    sell_count = len(filtered_tradebook[filtered_tradebook['Trade Type'] == 'sell']) if len(filtered_tradebook) > 0 else 0
    
    if total_analyzed > 0:
        # Show distribution across categories
        cat_breakdown = []
        if sentiment_data['intraday']['count'] > 0:
            cat_breakdown.append(f"Intraday: {sentiment_data['intraday']['count']}")
        if sentiment_data['btst']['count'] > 0:
            cat_breakdown.append(f"BTST: {sentiment_data['btst']['count']}")
        if sentiment_data['velocity']['count'] > 0:
            cat_breakdown.append(f"Velocity: {sentiment_data['velocity']['count']}")
        if sentiment_data['swing']['count'] > 0:
            cat_breakdown.append(f"Swing: {sentiment_data['swing']['count']}")
        
        if cat_breakdown:
            st.caption(f"📊 {' | '.join(cat_breakdown)} | Pure Swing: {sentiment_data['pure_swing']['count']}")
    
    if total_analyzed > 0:
        # Display metrics for each trading style
        st.subheader("Performance by Trading Style")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown("**Intraday (0 days)**")
            st.metric("Trades", sentiment_data['intraday']['count'])
            st.metric("Win Rate", f"{sentiment_data['intraday']['win_rate']:.1f}%")
            st.metric("Avg P&L", format_currency(sentiment_data['intraday']['avg_pnl']))
        
        with col2:
            st.markdown("**BTST (1 day)**")
            st.metric("Trades", sentiment_data['btst']['count'])
            st.metric("Win Rate", f"{sentiment_data['btst']['win_rate']:.1f}%")
            st.metric("Avg P&L", format_currency(sentiment_data['btst']['avg_pnl']))
        
        with col3:
            st.markdown("**Velocity (2-4 days)**")
            st.metric("Trades", sentiment_data['velocity']['count'])
            st.metric("Win Rate", f"{sentiment_data['velocity']['win_rate']:.1f}%")
            st.metric("Avg P&L", format_currency(sentiment_data['velocity']['avg_pnl']))
        
        with col4:
            st.markdown("**Swing (>4 days)**")
            st.metric("Trades", sentiment_data['swing']['count'])
            st.metric("Win Rate", f"{sentiment_data['swing']['win_rate']:.1f}%")
            st.metric("Avg P&L", format_currency(sentiment_data['swing']['avg_pnl']))
        
        with col5:
            st.markdown("**Pure Swing (>0 day)**")
            st.metric("Trades", sentiment_data['pure_swing']['count'])
            st.metric("Win Rate", f"{sentiment_data['pure_swing']['win_rate']:.1f}%")
            st.metric("Avg P&L", format_currency(sentiment_data['pure_swing']['avg_pnl']))
        
        # Trade Duration Distribution
        st.markdown("---")
        st.subheader("Distribution of Trade Holding Periods")
        duration_dist = mc.get_trade_duration_distribution(filtered_tradebook)
        if len(duration_dist) > 0:
            fig_dist = px.histogram(
                x=duration_dist,
                nbins=30,
                title='Trade Duration Distribution',
                labels={'x': 'Holding Period (Days)', 'count': 'Number of Trades'}
            )
            fig_dist.update_layout(height=400, xaxis_title="Holding Period (Days)", yaxis_title="Number of Trades")
            st.plotly_chart(fig_dist, use_container_width=True)
        else:
            st.info("No trade duration data available")
    else:
        st.info("Insufficient trade data for trading style analysis")

else:
    st.warning("No data available. Please upload files in the sidebar.")
