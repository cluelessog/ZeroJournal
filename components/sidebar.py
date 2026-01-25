"""
Sidebar components for ZeroJournal dashboard
Extracted from app.py for better modularity
"""

import streamlit as st
import pandas as pd
from typing import Optional, Tuple, List
from services import sector_mapper
from services import metrics_calculator as mc
from utils.formatters import format_currency
from utils.logger import logger
from utils.version import get_deployment_info, get_version_string


def render_file_upload() -> Tuple[Optional[object], Optional[object]]:
    """
    Render file upload section in sidebar.
    
    Returns:
        Tuple of (tradebook_file, pnl_file) uploader objects
    """
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
    
    return tradebook_file, pnl_file


def render_navigation_buttons() -> None:
    """
    Render navigation buttons (Re-upload, MAE/MFE, Back to Dashboard) in sidebar.
    """
    # Re-upload button at top of sidebar
    if st.sidebar.button("🔄 Re-upload Files", use_container_width=True, type="secondary", key="reupload_btn"):
        # Clear all session state
        st.session_state.tradebook_data = None
        st.session_state.pnl_data = None
        st.session_state.total_charges = 0.0
        st.session_state.filtered_tradebook = None
        st.session_state.filtered_pnl = None
        st.session_state.current_page = 'main'
        if 'mae_mfe_data' in st.session_state:
            st.session_state.mae_mfe_data = None
        st.rerun()
    
    # MAE/MFE Analysis button at top of sidebar
    if st.session_state.current_page == 'mae_mfe':
        if st.sidebar.button("🏠 Back to Dashboard", use_container_width=True, type="primary", key="back_to_dashboard_btn"):
            st.session_state.current_page = 'main'
            st.rerun()
    else:
        if st.sidebar.button("🎯 MAE/MFE Analysis", use_container_width=True, type="primary", key="mae_mfe_btn"):
            st.session_state.current_page = 'mae_mfe'
            st.rerun()
    
    st.sidebar.markdown("---")


def render_portfolio_settings() -> float:
    """
    Render portfolio settings section in sidebar.
    
    Returns:
        float: Initial capital value
    """
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
    
    return initial_capital


def render_filters(df_tradebook: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, Optional[pd.Timestamp], Optional[pd.Timestamp], List[str]]:
    """
    Render filters section in sidebar and apply filters to data.
    
    Args:
        df_tradebook: Full tradebook DataFrame
        
    Returns:
        Tuple of (filtered_tradebook, filtered_pnl, start_date, end_date, selected_symbols)
    """
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
        filtered_pnl_by_date = st.session_state.pnl_data.copy()
        
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
        
        return filtered_tradebook, filtered_pnl, start_date, end_date, selected_symbols
    else:
        return df_tradebook, st.session_state.pnl_data, None, None, []


def render_export_section(
    filtered_tradebook: pd.DataFrame,
    filtered_pnl: pd.DataFrame,
    start_date: Optional[pd.Timestamp],
    end_date: Optional[pd.Timestamp]
) -> Tuple[float, float, float, float, float, pd.DataFrame, pd.DataFrame]:
    """
    Render export section in sidebar and calculate metrics.
    
    Args:
        filtered_tradebook: Filtered tradebook DataFrame
        filtered_pnl: Filtered P&L DataFrame
        start_date: Start date for export filename
        end_date: End date for export filename
        
    Returns:
        Tuple of (win_rate, profit_factor, avg_holding_period, sharpe_ratio, max_drawdown, daily_pnl, cumulative_pnl)
    """
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
            # Initialize turnover variables to avoid NameError
            filtered_turnover = 0.0
            total_turnover = 0.0
            
            # Calculate proportional charges based on filtered turnover vs total turnover
            if st.session_state.tradebook_data is not None and len(st.session_state.tradebook_data) > 0:
                # Calculate turnover for filtered data
                filtered_turnover = mc.calculate_daily_turnover(filtered_tradebook)['Turnover'].sum() if len(filtered_tradebook) > 0 else 0
                
                # Calculate total turnover from all data
                total_turnover_df = mc.calculate_daily_turnover(st.session_state.tradebook_data)
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
            if total_turnover > 0:
                st.session_state.charge_allocation_ratio = (filtered_turnover / total_turnover * 100)
            else:
                st.session_state.charge_allocation_ratio = 0
        
        # Calculate metrics (safely handle empty dataframes)
        # Use FIFO-matched trades for consistent win rate and profit factor calculation
        if has_tradebook_data:
            # Get matched trades for win rate and profit factor calculation
            matched_trades = mc.match_trades_with_pnl(filtered_tradebook)
            if len(matched_trades) > 0:
                wins = sum(1 for _, pnl, _ in matched_trades if pnl > 0)
                win_rate = (wins / len(matched_trades)) * 100
                
                # Calculate profit factor from matched trades (not aggregated P&L)
                winning_trades = [pnl for _, pnl, _ in matched_trades if pnl > 0]
                losing_trades = [pnl for _, pnl, _ in matched_trades if pnl < 0]
                
                gross_profit = sum(winning_trades) if len(winning_trades) > 0 else 0
                gross_loss = abs(sum(losing_trades)) if len(losing_trades) > 0 else 0
                
                if gross_loss > 0:
                    profit_factor = gross_profit / gross_loss
                else:
                    profit_factor = float('inf') if gross_profit > 0 else 0.0
            else:
                win_rate = 0.0
                profit_factor = 0.0
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
            if start_date and end_date:
                if hasattr(start_date, 'date'):
                    date_str = f"{start_date.date()}_{end_date.date()}"
                else:
                    date_str = f"{start_date}_{end_date}"
            else:
                date_str = "all_data"
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
            if start_date and end_date:
                if hasattr(start_date, 'date'):
                    date_str = f"{start_date.date()}_{end_date.date()}"
                else:
                    date_str = f"{start_date}_{end_date}"
            else:
                date_str = "all_data"
            st.sidebar.download_button(
                label="📥 Export P&L (CSV)",
                data=csv_pnl,
                file_name=f"pnl_filtered_{date_str}.csv",
                mime="text/csv"
            )
        else:
            st.sidebar.info("No P&L data to export")
        
        return win_rate, profit_factor, avg_holding_period, sharpe_ratio, max_drawdown, daily_pnl, cumulative_pnl
    else:
        st.sidebar.info("Upload files to enable export")
        # Set default values for metrics to avoid NameError
        return 0.0, 0.0, 0.0, 0.0, 0.0, pd.DataFrame(columns=['Date', 'PnL']), pd.DataFrame(columns=['Date', 'Cumulative P&L'])


def render_version_info() -> None:
    """
    Render version and deployment information in the sidebar footer.
    """
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📋 Version Info")
    
    try:
        version_info = get_deployment_info()
        
        with st.sidebar.expander("ℹ️ Deployment Details", expanded=False):
            st.markdown(f"""
            **Application:** {version_info['app_name']}  
            **Version:** {version_info['version']}  
            **Commit:** `{version_info['commit_hash']}`  
            **Deployed:** {version_info['deployment_date']}  
            **Environment:** {version_info['environment']}
            """)
        
        # Compact version display
        st.sidebar.caption(f"Version {get_version_string()}")
    except Exception as e:
        logger.error(f"Error displaying version info: {e}")
        st.sidebar.caption("Version 1.5.0")
