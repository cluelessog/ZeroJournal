"""
Dashboard page for ZeroJournal
Extracted from app.py for better modularity
"""

import streamlit as st
import pandas as pd
from services import metrics_calculator as mc
from utils.formatters import format_currency, format_percentage

from components.charts import (
    render_equity_curve,
    render_pnl_tabs,
    render_rolling_expectancy_chart,
    render_monthly_expectancy_chart,
    render_cumulative_metrics_charts,
    render_win_rate_chart,
    render_holding_period_chart,
    render_trade_duration_distribution
)
from components.metrics import (
    render_performance_metrics,
    render_advanced_metrics,
    render_key_insights,
    render_trading_style_metrics
)
from components.navigation import render_navigation_bar


def show(
    filtered_tradebook: pd.DataFrame,
    filtered_pnl: pd.DataFrame,
    win_rate: float,
    profit_factor: float,
    avg_holding_period: float,
    sharpe_ratio: float,
    max_drawdown: float,
    daily_pnl: pd.DataFrame,
    cumulative_pnl: pd.DataFrame,
    initial_capital: float
) -> None:
    """
    Render the main dashboard page.
    
    Args:
        filtered_tradebook: Filtered tradebook DataFrame
        filtered_pnl: Filtered P&L DataFrame
        win_rate: Win rate percentage
        profit_factor: Profit factor value
        avg_holding_period: Average holding period in days
        sharpe_ratio: Sharpe ratio value
        max_drawdown: Maximum drawdown value
        daily_pnl: DataFrame with daily P&L data
        cumulative_pnl: DataFrame with cumulative P&L data
        initial_capital: Initial capital amount
    """
    # Check if we have any data to display
    has_data = len(filtered_tradebook) > 0 or len(filtered_pnl) > 0
    
    if not has_data:
        st.warning("⚠️ No data available for the selected filters. Please adjust your date range or symbol filters.")
        st.stop()
    
    # Key Insights Section (moved to top)
    render_key_insights(filtered_tradebook)
    
    # Quick Navigation Bar
    render_navigation_bar()
    
    # Section 1: Performance Metrics
    render_performance_metrics(win_rate, profit_factor, avg_holding_period, sharpe_ratio, max_drawdown)
    
    # Advanced Metrics Section
    render_advanced_metrics(filtered_tradebook)
    
    # Performance Trends Section - Time Series Analysis
    st.markdown("---")
    st.header("📊 Performance Trends Over Time")
    st.markdown('<div id="performance-trends"></div>', unsafe_allow_html=True)
    st.caption("Analyze how your trading metrics have evolved over time to identify improvement or degradation")
    
    if len(filtered_tradebook) > 0:
        render_rolling_expectancy_chart(filtered_tradebook)
        render_monthly_expectancy_chart(filtered_tradebook)
        render_cumulative_metrics_charts(filtered_tradebook)
    
    # Section 2: P&L Analysis
    st.markdown("---")
    st.header("📈 P&L Analysis")
    st.markdown('<div id="p-l-analysis"></div>', unsafe_allow_html=True)
    
    # Equity Curve and P&L Tabs
    if len(daily_pnl) > 0:
        render_equity_curve(daily_pnl, initial_capital)
        render_pnl_tabs(daily_pnl, cumulative_pnl)
    
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
        render_win_rate_chart(filtered_pnl, filtered_tradebook)
    
    with col2:
        render_holding_period_chart(filtered_tradebook)
    
    # Section 5: Trading Style Performance
    st.markdown("---")
    st.header("⏱️ Trading Style Performance")
    st.markdown('<div id="trading-style-performance"></div>', unsafe_allow_html=True)
    sentiment_data = mc.calculate_holding_sentiment(filtered_tradebook)
    
    render_trading_style_metrics(sentiment_data)
    
    # Trade Duration Distribution
    if len(filtered_tradebook) > 0:
        render_trade_duration_distribution(filtered_tradebook)
