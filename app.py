"""
ZeroJournal - Trading Dashboard for Swing Traders
Main Streamlit application
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io

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

# Modern Custom CSS
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Main container styling */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-attachment: fixed;
    }
    
    /* Content area */
    .block-container {
        padding: 2rem 3rem;
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        margin: 2rem auto;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
    }
    
    /* Headers */
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        color: #1a202c;
    }
    
    h1 {
        font-size: 2.5rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    
    h2 {
        font-size: 1.8rem;
        color: #2d3748;
        border-bottom: 3px solid #667eea;
        padding-bottom: 0.5rem;
        margin-top: 2rem;
        margin-bottom: 1.5rem;
    }
    
    h3 {
        font-size: 1.3rem;
        color: #4a5568;
    }
    
    /* Metrics styling */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem;
        font-weight: 600;
        color: #4a5568;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Info/Warning/Success boxes */
    .stAlert {
        border-radius: 12px;
        border: none;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        font-family: 'Inter', sans-serif;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: white;
    }
    
    [data-testid="stSidebar"] label {
        color: white !important;
        font-weight: 600;
    }
    
    /* Buttons */
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: transform 0.2s;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Download buttons in sidebar - Neon style */
    [data-testid="stSidebar"] .stDownloadButton button {
        background: rgba(255, 255, 255, 0.15) !important;
        color: white !important;
        border: 2px solid rgba(255, 255, 255, 0.8);
        border-radius: 12px;
        padding: 0.7rem 1.5rem;
        font-weight: 700;
        font-size: 0.95rem;
        transition: all 0.3s;
        width: 100%;
        margin: 0.5rem 0;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
    }
    
    [data-testid="stSidebar"] .stDownloadButton button:hover {
        background: rgba(255, 255, 255, 0.25) !important;
        border-color: white;
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(255, 255, 255, 0.3), 
                    0 0 20px rgba(255, 255, 255, 0.2);
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
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        background-color: #f7fafc;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
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
    st.sidebar.metric("Total Charges", format_currency(st.session_state.total_charges))

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
            with st.spinner("Fetching sector information... This may take a moment."):
                unique_symbols = df_tradebook['Symbol'].unique()
                
                # Show progress
                progress_bar = st.sidebar.progress(0)
                status_text = st.sidebar.empty()
                
                def update_progress(current, total):
                    progress = current / total
                    progress_bar.progress(progress)
                    status_text.text(f"Fetching sectors: {current}/{total}")
                
                sector_map = sector_mapper.get_sectors_for_symbols(unique_symbols, update_progress)
                st.session_state.sector_map = sector_map
                st.session_state.sectors_fetched = True
                
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()
                st.sidebar.success(f"✓ Fetched sectors for {len(sector_map)} symbols")
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
    if enable_sector_filter and 'sector_map' in st.session_state and st.session_state.sector_map:
        sector_map = st.session_state.sector_map
        available_sectors = sorted(set(sector_map.values()))
        available_sectors = [s for s in available_sectors if s != 'Unknown']
        
        if available_sectors:
            # Add "All Sectors" as the first option
            sector_options = ["All Sectors"] + available_sectors
            
            # Initialize selected sector in session state
            if 'selected_sector' not in st.session_state:
                st.session_state.selected_sector = "All Sectors"
            
            # Get the index for the current selection
            try:
                sector_index = sector_options.index(st.session_state.selected_sector)
            except ValueError:
                sector_index = 0
                st.session_state.selected_sector = "All Sectors"
            
            selected_sector = st.sidebar.selectbox(
                "Filter by Sector",
                options=sector_options,
                index=sector_index,
                key="sector_selectbox",
                help="Select a specific sector to filter (All Sectors = show all)"
            )
            
            # Update session state when selection changes
            if selected_sector != st.session_state.selected_sector:
                st.session_state.selected_sector = selected_sector
            
            # Convert to list format for filtering logic
            if selected_sector == "All Sectors":
                selected_sectors = []
            else:
                selected_sectors = [selected_sector]
        else:
            selected_sectors = []
    else:
        selected_sectors = []
    
    # Symbol Filter (independent) - Single Select
    # Add "All Stocks" as the first option
    symbol_options = ["All Stocks"] + all_available_symbols
    
    # Initialize selected symbol in session state
    if 'selected_symbol' not in st.session_state:
        st.session_state.selected_symbol = "All Stocks"
    
    # Reset button for symbol selection
    if st.sidebar.button("🔄 Reset", key="reset_symbol_btn", use_container_width=True, help="Reset to show all symbols"):
        st.session_state.selected_symbol = "All Stocks"
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
    
    # Distribute charges pro-rata by daily turnover
    if len(daily_pnl) > 0 and st.session_state.total_charges > 0:
        daily_pnl = mc.distribute_charges_pro_rata(
            daily_pnl, 
            filtered_tradebook, 
            st.session_state.total_charges,
            dp_charges_dict=None  # Can be enhanced to extract DP charge dates
        )
    
    # Calculate metrics (safely handle empty dataframes)
    if has_pnl_data:
        win_rate = mc.calculate_win_rate(filtered_pnl)
        profit_factor = mc.calculate_profit_factor(filtered_pnl)
    else:
        win_rate = 0.0
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

# Main Content - Performance Metrics
st.header("📊 Performance Metrics")

if filtered_tradebook is not None and filtered_pnl is not None:
    # Check if we have any data to display
    has_data = len(filtered_tradebook) > 0 or len(filtered_pnl) > 0
    
    if not has_data:
        st.warning("⚠️ No data available for the selected filters. Please adjust your date range or symbol filters.")
        st.stop()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Win Rate", f"{win_rate:.2f}%", delta=None)
    
    with col2:
        pf_display = f"{profit_factor:.2f}" if profit_factor != float('inf') else "∞"
        st.metric("Profit Factor", pf_display, delta=None)
    
    with col3:
        st.metric("Avg Holding Period", f"{avg_holding_period:.1f} days", delta=None)
    
    with col4:
        st.metric("Sharpe Ratio", f"{sharpe_ratio:.2f}", delta=None)
    
    with col5:
        st.metric("Max Drawdown", format_currency(max_drawdown), delta=None)
    
    # Trading Style Recommendations at the top
    if len(filtered_tradebook) > 0:
        sentiment_data = mc.calculate_holding_sentiment(filtered_tradebook)
        if sentiment_data['recommendation'] and (sentiment_data['best_style'] or sentiment_data['worst_style']):
            st.markdown("---")
            st.markdown("### 💡 Actionable Insights")
            st.info(sentiment_data['recommendation'])
    
    # P&L Analysis Section
    st.header("📈 P&L Analysis")
    
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
    
    # Top Winners/Losers
    st.header("🏆 Top Winners & Losers")
    
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
    
    # Trade Analysis Section
    st.header("📋 Trade Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Win Rate by Symbol")
        win_rate_by_symbol = mc.get_win_rate_by_symbol(filtered_pnl, filtered_tradebook)
        if len(win_rate_by_symbol) > 0:
            fig_win_rate = px.bar(
                win_rate_by_symbol.head(20),
                x='Win Rate %',
                y='Symbol',
                orientation='h',
                title='Win Rate by Symbol (Top 20)',
                labels={'Win Rate %': 'Win Rate (%)', 'Symbol': 'Symbol'}
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
    
    # Trading Style Performance Analysis - Main Section
    st.header("📊 Trading Style Performance")
    st.markdown("---")
    sentiment_data = mc.calculate_holding_sentiment(filtered_tradebook)
    
    total_analyzed = (sentiment_data['intraday']['count'] + 
                     sentiment_data['btst']['count'] + 
                     sentiment_data['velocity']['count'] + 
                     sentiment_data['swing']['count'] + 
                     sentiment_data['pure_swing']['count'])
    
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
            st.markdown("**Pure Swing (>1 day)**")
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
