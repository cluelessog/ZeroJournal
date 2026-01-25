"""
Chart rendering components for ZeroJournal dashboard
Extracted from app.py for better modularity
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional
from services import metrics_calculator as mc
import config


def render_equity_curve(daily_pnl: pd.DataFrame, initial_capital: float) -> None:
    """
    Render equity curve chart.
    
    Args:
        daily_pnl: DataFrame with daily P&L data
        initial_capital: Initial capital amount
    """
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


def render_pnl_tabs(daily_pnl: pd.DataFrame, cumulative_pnl: pd.DataFrame) -> None:
    """
    Render P&L analysis tabs (Daily, Weekly, Monthly, Cumulative).
    
    Args:
        daily_pnl: DataFrame with daily P&L data
        cumulative_pnl: DataFrame with cumulative P&L data
    """
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


def render_rolling_expectancy_chart(filtered_tradebook: pd.DataFrame) -> None:
    """
    Render rolling expectancy chart.
    
    Args:
        filtered_tradebook: Filtered tradebook DataFrame
    """
    st.subheader("📈 Rolling Expectancy (20-Trade Window)")
    st.markdown("""
    This chart shows your **expected profit per trade** calculated over rolling 20-trade windows.
    - **Above zero line** = profitable system
    - **Upward trend** = improving performance
    - **Downward trend** = degrading strategy or changing market conditions
    """)
    
    rolling_exp = mc.calculate_rolling_expectancy(filtered_tradebook)  # Uses default from config
    
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


def render_monthly_expectancy_chart(filtered_tradebook: pd.DataFrame) -> None:
    """
    Render monthly expectancy comparison chart.
    
    Args:
        filtered_tradebook: Filtered tradebook DataFrame
    """
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


def render_cumulative_metrics_charts(filtered_tradebook: pd.DataFrame) -> None:
    """
    Render cumulative metrics dashboard (4 charts in 2x2 grid).
    
    Args:
        filtered_tradebook: Filtered tradebook DataFrame
    """
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
            pf_data['profit_factor_display'] = pf_data['profit_factor'].clip(upper=config.CHART_PROFIT_FACTOR_CAP)
            
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
                title=f'Cumulative Profit Factor (capped at {config.CHART_PROFIT_FACTOR_CAP} for visibility)',
                xaxis_title='Trade Number',
                yaxis_title='Profit Factor',
                yaxis=dict(range=[0, config.CHART_PROFIT_FACTOR_CAP]),
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


def render_win_rate_chart(filtered_pnl: pd.DataFrame, filtered_tradebook: pd.DataFrame) -> None:
    """
    Render win rate by symbol chart.
    
    Args:
        filtered_pnl: Filtered P&L DataFrame
        filtered_tradebook: Filtered tradebook DataFrame
    """
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


def render_holding_period_chart(filtered_tradebook: pd.DataFrame) -> None:
    """
    Render average holding period by stock chart.
    
    Args:
        filtered_tradebook: Filtered tradebook DataFrame
    """
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


def render_trade_duration_distribution(filtered_tradebook: pd.DataFrame) -> None:
    """
    Render trade duration distribution histogram.
    
    Args:
        filtered_tradebook: Filtered tradebook DataFrame
    """
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
