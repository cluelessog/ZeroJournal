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
# Normalize dates to ensure consistent cache keys across environments
@st.cache_data(ttl=1800, show_spinner=False)  # Cache for 30 minutes
def fetch_historical_data_cached(symbol, start_date, end_date, interval, segment='EQ'):
    """
    Cached wrapper for fetching historical data from openchart.
    This prevents re-fetching the same data multiple times.
    
    Dates are normalized to date-only strings to ensure consistent cache keys
    across different environments (local vs deployed).
    
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
        
        # Dates are now normalized to ISO strings by caller for consistent cache keys
        # Convert ISO date strings to pd.Timestamp for openchart
        # Handle both string (ISO format) and date object inputs for backward compatibility
        if isinstance(start_date, str):
            start_date_obj = pd.Timestamp(start_date)
        elif isinstance(start_date, pd.Timestamp):
            start_date_obj = start_date
        elif isinstance(start_date, datetime):
            start_date_obj = pd.Timestamp(start_date)
        else:
            # date object or other - normalize to ISO string first
            start_date_obj = pd.Timestamp(pd.to_datetime(start_date).date().isoformat())
        
        if isinstance(end_date, str):
            end_date_obj = pd.Timestamp(end_date)
        elif isinstance(end_date, pd.Timestamp):
            end_date_obj = end_date
        elif isinstance(end_date, datetime):
            end_date_obj = pd.Timestamp(end_date)
        else:
            # date object or other - normalize to ISO string first
            end_date_obj = pd.Timestamp(pd.to_datetime(end_date).date().isoformat())
        
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
    
    # Check if data is available from main app (use full tradebook, not filtered)
    if 'tradebook_data' not in st.session_state or st.session_state.tradebook_data is None:
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
    
    # Get full tradebook (all stocks, not filtered) - ensures consistency between local and deployed
    tradebook = st.session_state.tradebook_data
    
    st.markdown("---")
    
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
                    # Using full tradebook (all stocks) - ensures consistency between local and deployed
                    mae_mfe_df = mc.calculate_mae_mfe_for_trades(
                        tradebook, 
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
                        buy_count = len(tradebook[tradebook['Trade Type'].str.lower() == 'buy'])
                        sell_count = len(tradebook[tradebook['Trade Type'].str.lower() == 'sell'])
                        unique_symbols = tradebook['Symbol'].unique()
                        
                        st.markdown(f"""
                        **Diagnostic Information:**
                        - Total trades: {len(tradebook)}
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
        
        # Calculate metrics for enhanced visualization
        mae_75th = mae_mfe_df['MAE %'].quantile(0.75)
        mfe_median = mae_mfe_df['MFE %'].median()
        mae_mfe_df['P&L Magnitude'] = abs(mae_mfe_df['Exit P&L %'])
        
        # MAE vs MFE Scatter Plot - Enhanced Version
        st.markdown("### 📊 MAE vs MFE Scatter Plot")
        
        # Separate by winners and losers
        winners = mae_mfe_df[mae_mfe_df['Exit P&L %'] > 0].copy()
        losers = mae_mfe_df[mae_mfe_df['Exit P&L %'] <= 0].copy()
        
        # Create enhanced scatter plot
        fig = go.Figure()
        
        # Winners - Color by Exit Efficiency, Size by P&L magnitude
        if len(winners) > 0:
            # Normalize size to range 8-30 based on P&L magnitude
            if winners['P&L Magnitude'].max() > winners['P&L Magnitude'].min():
                winners_size = 8 + ((winners['P&L Magnitude'] - winners['P&L Magnitude'].min()) / 
                                  (winners['P&L Magnitude'].max() - winners['P&L Magnitude'].min()) * 22)
            else:
                winners_size = 15  # Default size if all values are same
            
            fig.add_trace(go.Scatter(
                x=winners['MAE %'],
                y=winners['MFE %'],
                mode='markers',
                name='Winners',
                marker=dict(
                    color=winners['Exit Efficiency %'],
                    colorscale='Greens',
                    size=winners_size,
                    sizemin=8,
                    sizemode='diameter',
                    opacity=0.7,
                    colorbar=dict(
                        title="Exit Efficiency %",
                        x=1.15,
                        len=0.5,
                        y=0.5
                    ),
                    line=dict(width=1, color='darkgreen')
                ),
                text=[f"<b>{row['Symbol']}</b><br>" +
                      f"MAE: {row['MAE %']:.2f}%<br>" +
                      f"MFE: {row['MFE %']:.2f}%<br>" +
                      f"P&L: {row['Exit P&L %']:.2f}%<br>" +
                      f"Efficiency: {row['Exit Efficiency %']:.1f}%<br>" +
                      f"Holding: {row['Holding Days']} days<br>" +
                      f"Entry: ₹{row['Entry Price']:.2f}<br>" +
                      f"Exit: ₹{row['Exit Price']:.2f}"
                      for _, row in winners.iterrows()],
                hovertemplate='%{text}<extra></extra>',
                customdata=winners[['Symbol', 'Exit P&L %', 'Exit Efficiency %', 'Holding Days']].values
            ))
        
        # Losers - Color by MAE magnitude (red scale), Size by loss magnitude
        if len(losers) > 0:
            # Normalize size to range 8-30 based on P&L magnitude
            if losers['P&L Magnitude'].max() > losers['P&L Magnitude'].min():
                losers_size = 8 + ((losers['P&L Magnitude'] - losers['P&L Magnitude'].min()) / 
                                  (losers['P&L Magnitude'].max() - losers['P&L Magnitude'].min()) * 22)
            else:
                losers_size = 15  # Default size if all values are same
            
            fig.add_trace(go.Scatter(
                x=losers['MAE %'],
                y=losers['MFE %'],
                mode='markers',
                name='Losers',
                marker=dict(
                    color=losers['MAE %'],  # Darker red = worse MAE
                    colorscale='Reds',
                    size=losers_size,
                    sizemin=8,
                    sizemode='diameter',
                    opacity=0.7,
                    colorbar=dict(
                        title="MAE % (Loss Severity)",
                        x=1.15,
                        len=0.5,
                        y=0.0
                    ),
                    line=dict(width=1, color='darkred')
                ),
                text=[f"<b>{row['Symbol']}</b><br>" +
                      f"MAE: {row['MAE %']:.2f}%<br>" +
                      f"MFE: {row['MFE %']:.2f}%<br>" +
                      f"P&L: {row['Exit P&L %']:.2f}%<br>" +
                      f"Efficiency: {row['Exit Efficiency %']:.1f}%<br>" +
                      f"Holding: {row['Holding Days']} days<br>" +
                      f"Entry: ₹{row['Entry Price']:.2f}<br>" +
                      f"Exit: ₹{row['Exit Price']:.2f}"
                      for _, row in losers.iterrows()],
                hovertemplate='%{text}<extra></extra>',
                customdata=losers[['Symbol', 'Exit P&L %', 'Exit Efficiency %', 'Holding Days']].values
            ))
        
        # Add reference lines for optimal zones
        # Vertical line: Optimal Stop Loss (75th percentile MAE)
        fig.add_vline(
            x=mae_75th,
            line_dash="dash",
            line_color="orange",
            annotation_text=f"Optimal Stop: {mae_75th:.2f}%",
            annotation_position="top",
            annotation=dict(font_size=10, font_color="orange")
        )
        
        # Horizontal line: Median MFE (typical profit potential)
        fig.add_hline(
            y=mfe_median,
            line_dash="dash",
            line_color="blue",
            annotation_text=f"Median MFE: {mfe_median:.2f}%",
            annotation_position="right",
            annotation=dict(font_size=10, font_color="blue")
        )
        
        # Add quadrant annotations
        max_mae = mae_mfe_df['MAE %'].max()
        max_mfe = mae_mfe_df['MFE %'].max()
        
        # Quadrant labels
        fig.add_annotation(
            x=max_mae * 0.75, y=max_mfe * 0.9,
            text="<b>Best Trades</b><br>Low MAE, High MFE",
            showarrow=False,
            bgcolor="rgba(0,255,0,0.2)",
            bordercolor="green",
            borderwidth=2,
            font=dict(size=11, color="darkgreen")
        )
        
        fig.add_annotation(
            x=max_mae * 0.75, y=max_mfe * 0.1,
            text="<b>Worst Trades</b><br>High MAE, Low MFE",
            showarrow=False,
            bgcolor="rgba(255,0,0,0.2)",
            bordercolor="red",
            borderwidth=2,
            font=dict(size=11, color="darkred")
        )
        
        fig.add_annotation(
            x=max_mae * 0.1, y=max_mfe * 0.1,
            text="<b>Quick Exits</b><br>Low MAE, Low MFE",
            showarrow=False,
            bgcolor="rgba(255,255,0,0.2)",
            bordercolor="orange",
            borderwidth=2,
            font=dict(size=11, color="darkorange")
        )
        
        fig.add_annotation(
            x=max_mae * 0.1, y=max_mfe * 0.9,
            text="<b>Recovery Trades</b><br>Low MAE, High MFE<br>(Good entries)",
            showarrow=False,
            bgcolor="rgba(0,0,255,0.2)",
            bordercolor="blue",
            borderwidth=2,
            font=dict(size=11, color="darkblue")
        )
        
        # Update layout
        fig.update_layout(
            xaxis_title='MAE % (Maximum Adverse Excursion - Against You)',
            yaxis_title='MFE % (Maximum Favorable Excursion - In Your Favor)',
            height=700,
            template='plotly_white',
            hovermode='closest',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(r=200),  # Extra margin for colorbar
            title=dict(
                text="<b>MAE vs MFE Analysis</b><br><sub>Marker size = P&L magnitude | Color = Efficiency (winners) / MAE severity (losers)</sub>",
                x=0.5,
                xanchor='center',
                font=dict(size=14)
            )
        )
        
        # Add axis range padding
        fig.update_xaxes(range=[-max_mae * 0.1, max_mae * 1.1])
        fig.update_yaxes(range=[-max_mfe * 0.1, max_mfe * 1.1])
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Add summary statistics below the chart
        st.markdown("#### 📈 Trade Quality Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            best_trades = len(winners[(winners['MAE %'] < mae_75th) & (winners['MFE %'] > mfe_median)])
            st.metric(
                "Trades in Best Zone",
                best_trades,
                help="Winners with low MAE and high MFE"
            )
        
        with col2:
            wide_stops_needed = len(mae_mfe_df[mae_mfe_df['MAE %'] > mae_75th])
            st.metric(
                "Trades Needing Wider Stops",
                wide_stops_needed,
                help="Trades where MAE exceeded optimal stop distance"
            )
        
        with col3:
            early_exits = len(winners[(winners['MFE %'] > mfe_median) & (winners['Exit Efficiency %'] < 50)])
            st.metric(
                "Early Exit Trades",
                early_exits,
                help="Winners with high MFE but low efficiency"
            )
        
        with col4:
            recovery_trades = len(winners[(winners['MAE %'] > mae_75th) & (winners['Exit P&L %'] > 0)])
            st.metric(
                "Recovery Trades",
                recovery_trades,
                help="Trades that went against you but recovered"
            )
        
        # Additional Analysis Charts
        st.markdown("---")
        st.markdown("### 📈 Additional Analysis")
        
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["Distribution Analysis", "Efficiency Analysis", "Trade Patterns"])
        
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                # MAE Distribution
                fig_mae = go.Figure()
                fig_mae.add_trace(go.Histogram(
                    x=mae_mfe_df['MAE %'],
                    nbinsx=30,
                    name='MAE Distribution',
                    marker_color='red',
                    opacity=0.7
                ))
                fig_mae.add_vline(
                    x=mae_75th,
                    line_dash="dash",
                    line_color="orange",
                    annotation_text=f"75th: {mae_75th:.2f}%"
                )
                fig_mae.update_layout(
                    title="MAE Distribution (Stop Loss Analysis)",
                    xaxis_title="MAE %",
                    yaxis_title="Number of Trades",
                    height=400
                )
                st.plotly_chart(fig_mae, use_container_width=True)
            
            with col2:
                # MFE Distribution
                fig_mfe = go.Figure()
                fig_mfe.add_trace(go.Histogram(
                    x=mae_mfe_df['MFE %'],
                    nbinsx=30,
                    name='MFE Distribution',
                    marker_color='green',
                    opacity=0.7
                ))
                fig_mfe.add_vline(
                    x=mfe_median,
                    line_dash="dash",
                    line_color="blue",
                    annotation_text=f"Median: {mfe_median:.2f}%"
                )
                fig_mfe.update_layout(
                    title="MFE Distribution (Profit Target Analysis)",
                    xaxis_title="MFE %",
                    yaxis_title="Number of Trades",
                    height=400
                )
                st.plotly_chart(fig_mfe, use_container_width=True)
        
        with tab2:
            # Exit Efficiency vs P&L
            fig_eff = go.Figure()
            
            winners_eff = winners.copy()
            losers_eff = losers.copy()
            
            if len(winners_eff) > 0:
                fig_eff.add_trace(go.Scatter(
                    x=winners_eff['Exit Efficiency %'],
                    y=winners_eff['Exit P&L %'],
                    mode='markers',
                    name='Winners',
                    marker=dict(color='green', size=10, opacity=0.6),
                    text=winners_eff['Symbol'],
                    hovertemplate='<b>%{text}</b><br>Efficiency: %{x:.1f}%<br>P&L: %{y:.2f}%<extra></extra>'
                ))
            
            if len(losers_eff) > 0:
                fig_eff.add_trace(go.Scatter(
                    x=losers_eff['Exit Efficiency %'],
                    y=losers_eff['Exit P&L %'],
                    mode='markers',
                    name='Losers',
                    marker=dict(color='red', size=10, opacity=0.6),
                    text=losers_eff['Symbol'],
                    hovertemplate='<b>%{text}</b><br>Efficiency: %{x:.1f}%<br>P&L: %{y:.2f}%<extra></extra>'
                ))
            
            fig_eff.add_hline(y=0, line_dash="dash", line_color="gray")
            fig_eff.update_layout(
                title="Exit Efficiency vs Actual P&L",
                xaxis_title="Exit Efficiency %",
                yaxis_title="Exit P&L %",
                height=500
            )
            st.plotly_chart(fig_eff, use_container_width=True)
        
        with tab3:
            # MAE vs Holding Days
            fig_holding = go.Figure()
            
            if len(winners) > 0:
                fig_holding.add_trace(go.Scatter(
                    x=winners['Holding Days'],
                    y=winners['MAE %'],
                    mode='markers',
                    name='Winners',
                    marker=dict(color='green', size=10, opacity=0.6),
                    text=winners['Symbol'],
                    hovertemplate='<b>%{text}</b><br>Holding: %{x} days<br>MAE: %{y:.2f}%<extra></extra>'
                ))
            
            if len(losers) > 0:
                fig_holding.add_trace(go.Scatter(
                    x=losers['Holding Days'],
                    y=losers['MAE %'],
                    mode='markers',
                    name='Losers',
                    marker=dict(color='red', size=10, opacity=0.6),
                    text=losers['Symbol'],
                    hovertemplate='<b>%{text}</b><br>Holding: %{x} days<br>MAE: %{y:.2f}%<extra></extra>'
                ))
            
            fig_holding.update_layout(
                title="MAE vs Holding Period",
                xaxis_title="Holding Days",
                yaxis_title="MAE %",
                height=500
            )
            st.plotly_chart(fig_holding, use_container_width=True)
        
        # Insights
        st.markdown("---")
        st.markdown("### 💡 Key Insights")
        
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
