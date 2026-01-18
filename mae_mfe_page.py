"""
MAE/MFE Analysis Page Module
This is not in the pages/ folder to avoid auto-discovery
It will be conditionally loaded via st.Page()
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

from services import metrics_calculator as mc

# Cached function for fetching historical data (Optimization 1: Aggressive Caching)
@st.cache_data(ttl=1800, show_spinner=False)  # Cache for 30 minutes
def fetch_historical_data_cached(symbol, start_date, end_date, interval, segment='EQ'):
    """
    Cached wrapper for fetching historical data from openchart.
    This prevents re-fetching the same data multiple times.
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE-EQ', 'TCS')
        start_date: Start date (datetime, Timestamp, or date)
        end_date: End date (datetime, Timestamp, or date)
        interval: Data interval ('5m', '1d', etc.)
        segment: Market segment (default 'EQ')
        
    Returns:
        DataFrame with historical data or empty DataFrame if failed
    """
    try:
        from openchart import NSEData
        openchart_nse = NSEData()
        
        # Convert dates to pd.Timestamp (openchart expects pd.Timestamp, not date objects)
        # Match the format used in the non-cached version
        if isinstance(start_date, pd.Timestamp):
            start_date_obj = start_date
        elif isinstance(start_date, datetime):
            start_date_obj = pd.Timestamp(start_date)
        elif isinstance(start_date, str):
            start_date_obj = pd.to_datetime(start_date)
        else:
            # date object - convert to pd.Timestamp
            start_date_obj = pd.Timestamp(start_date) if hasattr(start_date, 'year') else pd.to_datetime(start_date)
            
        if isinstance(end_date, pd.Timestamp):
            end_date_obj = end_date
        elif isinstance(end_date, datetime):
            end_date_obj = pd.Timestamp(end_date)
        elif isinstance(end_date, str):
            end_date_obj = pd.to_datetime(end_date)
        else:
            # date object - convert to pd.Timestamp
            end_date_obj = pd.Timestamp(end_date) if hasattr(end_date, 'year') else pd.to_datetime(end_date)
        
        # Add 1 day to end_date (matching non-cached version)
        from datetime import timedelta
        end_date_obj = end_date_obj + timedelta(days=1)
        
        # Fetch data using pd.Timestamp format (same as non-cached version)
        hist_data = openchart_nse.historical(
            symbol=symbol,
            segment=segment,
            start=start_date_obj,
            end=end_date_obj,
            interval=interval
        )
        
        if not hist_data.empty:
            # Normalize column names
            hist_data.columns = [col.title() for col in hist_data.columns]
            return hist_data
        else:
            return pd.DataFrame()
    except Exception as e:
        print(f"Error in cached fetch for {symbol}: {e}")
        return pd.DataFrame()

def show():
    """Display MAE/MFE Analysis page content"""
    
    # Custom CSS for better styling
    st.markdown("""
        <style>
        .main-header {
            font-size: 48px;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        .sub-header {
            font-size: 18px;
            color: #666;
            margin-bottom: 30px;
        }
        .info-box {
            background: #f0f7ff;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #2196F3;
            margin: 20px 0;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<h1 class="main-header">🎯 MAE/MFE Analysis</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Maximum Adverse Excursion & Maximum Favorable Excursion - Optimize Your Stops and Targets</p>', unsafe_allow_html=True)
    
    # Check if data is available from main app
    if 'filtered_tradebook' not in st.session_state or st.session_state.filtered_tradebook is None:
        st.warning("⚠️ **No Data Available!** Please upload your tradebook data on the main dashboard first.")
        
        # Add a prominent button to go back to home
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🏠 Go to Home Page to Upload Files", use_container_width=True, type="primary"):
                st.session_state.current_page = 'main'
                st.rerun()
        
        # Add educational content
        st.markdown("---")
        st.markdown("### 📚 What is MAE/MFE Analysis?")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **MAE (Maximum Adverse Excursion)**
            - How far the price went **against** you during the trade
            - Helps determine optimal stop loss placement
            - Identifies if you're giving trades enough room
            - Shows typical drawdown before a trade works out
            
            **Example:** You buy at ₹100, price drops to ₹95, then rallies to ₹110 where you sell.
            - Your MAE is 5% (₹100 → ₹95)
            - This is the maximum you were underwater
            """)
        
        with col2:
            st.markdown("""
            **MFE (Maximum Favorable Excursion)**
            - How far the price went **in your favor** during the trade
            - Helps set profit targets
            - Shows if you're exiting winners too early
            - Identifies optimal exit points
            
            **Example:** Same trade - buy at ₹100, price hits ₹115 peak, you sell at ₹110.
            - Your MFE is 15% (₹100 → ₹115)
            - Your Exit Efficiency is 66.7% (captured ₹10 of ₹15 move)
            """)
        
        st.markdown("---")
        st.info("💡 **Pro Tip:** Upload your tradebook on the main page to start analyzing your MAE/MFE patterns and optimize your trading strategy!")
        
        return
    
    # Get filtered tradebook
    filtered_tradebook = st.session_state.filtered_tradebook
    
    st.markdown("---")
    
    # Sidebar info
    with st.sidebar:
        st.markdown("### 📊 Analysis Settings")
        st.info(f"**Trades Available:** {len(filtered_tradebook)}")
        
        if 'mae_mfe_data' in st.session_state and st.session_state.mae_mfe_data is not None:
            st.success(f"✅ MAE/MFE data cached for {len(st.session_state.mae_mfe_data)} trades")
            if st.button("🔄 Recalculate", use_container_width=True):
                st.session_state.mae_mfe_data = None
                st.rerun()
    
    # Initialize session state for MAE/MFE data
    if 'mae_mfe_data' not in st.session_state:
        st.session_state.mae_mfe_data = None
    
    # Main content
    if st.session_state.mae_mfe_data is None:
        # Show explanation and calculate button
        st.markdown("""
        <div class="info-box">
        <h3>📖 Understanding MAE/MFE Analysis</h3>
        
        <p><strong>Maximum Adverse Excursion (MAE)</strong> measures how far the price moved against you during each trade. 
        This helps you understand if your stop losses are too tight or if you're giving trades enough room to breathe.</p>
        
        <p><strong>Maximum Favorable Excursion (MFE)</strong> measures the peak profit available during each trade. 
        This reveals if you're exiting winners too early and helps optimize your profit targets.</p>
        
        <p><strong>Exit Efficiency</strong> shows what percentage of the available profit you actually captured. 
        Higher efficiency means you're timing your exits well.</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button("🚀 Calculate MAE/MFE for All Trades", use_container_width=True):
                try:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Progress callback function
                    def update_progress(progress, message):
                        progress_bar.progress(progress / 100)
                        status_text.text(message)
                    
                    status_text.text("Starting MAE/MFE calculation...")
                    progress_bar.progress(0)
                    
                    # Pass the cached fetch function for optimization
                    mae_mfe_df = mc.calculate_mae_mfe_for_trades(
                        filtered_tradebook, 
                        progress_callback=update_progress,
                        fetch_function=fetch_historical_data_cached
                    )
                    
                    progress_bar.progress(95)
                    status_text.text("Finalizing results...")
                    
                    if len(mae_mfe_df) > 0:
                        st.session_state.mae_mfe_data = mae_mfe_df
                        progress_bar.progress(100)
                        status_text.empty()
                        st.success(f"✅ Successfully calculated MAE/MFE for {len(mae_mfe_df)} trades!")
                        st.rerun()
                    else:
                        progress_bar.empty()
                        status_text.empty()
                        st.error("❌ No MAE/MFE data could be calculated.")
                        
                        # Show diagnostic information
                        buy_count = len(filtered_tradebook[filtered_tradebook['Trade Type'].str.lower() == 'buy'])
                        sell_count = len(filtered_tradebook[filtered_tradebook['Trade Type'].str.lower() == 'sell'])
                        unique_symbols = filtered_tradebook['Symbol'].unique()
                        
                        st.markdown(f"""
                        **Diagnostic Information:**
                        - Total trades: {len(filtered_tradebook)}
                        - Buy trades: {buy_count}
                        - Sell trades: {sell_count}
                        - Unique symbols: {len(unique_symbols)}
                        - Sample symbols: {', '.join(list(unique_symbols[:5]))}
                        """)
                        
                        st.markdown("""
                        **Possible reasons:**
                        1. **NSE API unavailable** - The NSE data service may be temporarily down
                        2. **Symbol format mismatch** - Stock symbols in your tradebook may not match NSE listings
                        3. **Historical data unavailable** - Some stocks may be delisted or renamed
                        4. **No completed trades** - Ensure you have buy-sell pairs in your data
                        5. **Data fetch failures** - Both NSE API and openchart failed to fetch data
                        
                        **Troubleshooting:**
                        - Check your internet connection
                        - Verify symbol names match NSE format (e.g., "RELIANCE", "TCS")
                        - Check the terminal/console for detailed error messages
                        - Try again in a few moments
                        - Ensure trades have both buy and sell entries
                        """)
                except Exception as e:
                    st.error(f"❌ Error calculating MAE/MFE: {str(e)}")
        
        # Show benefits
        st.markdown("---")
        st.markdown("### 🎯 What You'll Learn")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **🛑 Stop Loss Optimization**
            - Find your optimal stop distance
            - Avoid getting stopped out prematurely
            - Give trades room to work
            """)
        
        with col2:
            st.markdown("""
            **💰 Profit Target Setting**
            - Identify typical profit potential
            - Set realistic targets
            - Avoid leaving money on table
            """)
        
        with col3:
            st.markdown("""
            **📈 Exit Timing**
            - Measure exit efficiency
            - Identify early exit patterns
            - Learn to let winners run
            """)
    
    else:
        # Display MAE/MFE results
        mae_mfe_df = st.session_state.mae_mfe_data
        
        # Key metrics
        st.markdown("### 📊 Key Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_mae = mae_mfe_df['MAE %'].mean()
            st.metric("Average MAE", f"{avg_mae:.2f}%")
        
        with col2:
            avg_mfe = mae_mfe_df['MFE %'].mean()
            st.metric("Average MFE", f"{avg_mfe:.2f}%")
        
        with col3:
            avg_efficiency = mae_mfe_df['Exit Efficiency %'].mean()
            st.metric("Exit Efficiency", f"{avg_efficiency:.1f}%")
        
        with col4:
            optimal_stop = mae_mfe_df['MAE %'].quantile(0.75)
            st.metric("Optimal Stop Loss", f"{optimal_stop:.2f}%")
        
        st.markdown("---")
        
        # MAE vs MFE Scatter Plot
        st.markdown("### 📊 MAE vs MFE Scatter Plot")
        
        fig = go.Figure()
        
        winners = mae_mfe_df[mae_mfe_df['Exit P&L %'] > 0]
        losers = mae_mfe_df[mae_mfe_df['Exit P&L %'] <= 0]
        
        if len(winners) > 0:
            fig.add_trace(go.Scatter(
                x=winners['MAE %'], y=winners['MFE %'],
                mode='markers', name='Winners',
                marker=dict(color='green', size=10, opacity=0.6),
                text=winners['Symbol']
            ))
        
        if len(losers) > 0:
            fig.add_trace(go.Scatter(
                x=losers['MAE %'], y=losers['MFE %'],
                mode='markers', name='Losers',
                marker=dict(color='red', size=10, opacity=0.6),
                text=losers['Symbol']
            ))
        
        fig.update_layout(
            xaxis_title='MAE % (Against You)',
            yaxis_title='MFE % (In Your Favor)',
            height=600,
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Insights
        st.markdown("---")
        st.markdown("### 💡 Key Insights")
        
        mae_75th = mae_mfe_df['MAE %'].quantile(0.75)
        mfe_median = mae_mfe_df['MFE %'].median()
        
        st.info(f"📍 **Stop Loss:** Set stops at {mae_75th:.2f}% to avoid 75% of adverse moves")
        st.info(f"🎯 **Profit Target:** Target {mfe_median:.2f}% (median favorable move)")
        
        if avg_efficiency < 50:
            st.warning(f"⚠️ **Low Efficiency ({avg_efficiency:.1f}%):** You're exiting winners too early. Use trailing stops!")
        elif avg_efficiency > 70:
            st.success(f"✅ **Excellent Efficiency ({avg_efficiency:.1f}%):** Great exit timing!")
        
        # Data table
        st.markdown("---")
        with st.expander("📋 View Detailed Data"):
            st.dataframe(mae_mfe_df, use_container_width=True, height=400)
            
            csv = mae_mfe_df.to_csv(index=False)
            st.download_button(
                "📥 Download CSV",
                data=csv,
                file_name=f"mae_mfe_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
