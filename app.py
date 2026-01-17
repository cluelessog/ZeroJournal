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

# Page config
st.set_page_config(
    page_title="ZeroJournal - Trading Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
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
    df_pnl, error_pnl = read_pnl(pnl_file)
    
    if error_tb:
        return None, None, error_tb, error_pnl
    if error_pnl:
        return df_tradebook, None, error_tb, error_pnl
    
    return df_tradebook, df_pnl, None, None


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


# Main Header
st.markdown('<h1 class="main-header">📈 ZeroJournal - Trading Dashboard</h1>', unsafe_allow_html=True)

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

# Load data when files are uploaded
if tradebook_file is not None and pnl_file is not None:
    with st.spinner("Loading and parsing Excel files..."):
        df_tb, df_pnl, error_tb, error_pnl = load_data(tradebook_file, pnl_file)
        
        if error_tb or error_pnl:
            st.error(f"Error loading files: {error_tb or error_pnl}")
            st.session_state.tradebook_data = None
            st.session_state.pnl_data = None
        else:
            st.session_state.tradebook_data = df_tb
            st.session_state.pnl_data = df_pnl
            st.sidebar.success("✓ Files loaded successfully!")
else:
    st.session_state.tradebook_data = None
    st.session_state.pnl_data = None

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

# Sidebar - Filters Section
st.sidebar.header("🔍 Filters")

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
    
    # Get symbols from date-filtered tradebook for consistency
    # This ensures P&L matches the symbols that actually appear in the date range
    symbols_in_date_range = sorted(filtered_tradebook['Symbol'].unique().tolist())
    
    # Get all available symbols for the multiselect
    available_symbols = sorted(df_tradebook['Symbol'].unique().tolist())
    
    selected_symbols = st.sidebar.multiselect(
        "Filter by Symbol",
        options=available_symbols,
        default=available_symbols,
        help="Select symbols to include in analysis"
    )
    
    # Filter by symbols - ensure both datasets are filtered consistently
    if selected_symbols:
        # Filter by selected symbols - both datasets filtered by same symbols
        filtered_tradebook = filtered_tradebook[filtered_tradebook['Symbol'].isin(selected_symbols)]
        filtered_pnl = df_pnl[df_pnl['Symbol'].isin(selected_symbols)].copy()
    else:
        # When no symbols selected, show empty datasets to ensure consistency
        # This prevents mismatch where tradebook is date-filtered but P&L is unfiltered
        filtered_tradebook = filtered_tradebook.iloc[0:0].copy()
        filtered_pnl = df_pnl.iloc[0:0].copy()
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
    
    # P&L Analysis Section
    st.header("📈 P&L Analysis")
    
    # Equity Curve
    if len(daily_pnl) > 0:
        equity_curve = mc.get_equity_curve(daily_pnl, initial_value=0)
        
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
        win_rate_by_symbol = mc.get_win_rate_by_symbol(filtered_pnl)
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
    
    # Trade Duration Distribution
    st.subheader("Trade Duration Distribution")
    duration_dist = mc.get_trade_duration_distribution(filtered_tradebook)
    if len(duration_dist) > 0:
        fig_dist = px.histogram(
            x=duration_dist,
            nbins=30,
            title='Distribution of Trade Holding Periods',
            labels={'x': 'Holding Period (Days)', 'count': 'Number of Trades'}
        )
        fig_dist.update_layout(height=400, xaxis_title="Holding Period (Days)", yaxis_title="Number of Trades")
        st.plotly_chart(fig_dist, use_container_width=True)
    else:
        st.info("No trade duration data available")

else:
    st.warning("No data available. Please upload files in the sidebar.")
