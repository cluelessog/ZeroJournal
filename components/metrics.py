"""
Metrics display components for ZeroJournal dashboard
Extracted from app.py for better modularity
"""

import streamlit as st
import pandas as pd
from streamlit_elements import elements, mui
from services import metrics_calculator as mc
from utils.formatters import format_currency


def render_performance_metrics(
    win_rate: float,
    profit_factor: float,
    avg_holding_period: float,
    sharpe_ratio: float,
    max_drawdown: float
) -> None:
    """
    Render performance metrics section using Material-UI Grid.
    
    Args:
        win_rate: Win rate percentage
        profit_factor: Profit factor value
        avg_holding_period: Average holding period in days
        sharpe_ratio: Sharpe ratio value
        max_drawdown: Maximum drawdown value
    """
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


def render_advanced_metrics(filtered_tradebook: pd.DataFrame) -> None:
    """
    Render advanced metrics section (Expectancy, Risk-Reward, Streaks).
    
    Args:
        filtered_tradebook: Filtered tradebook DataFrame
    """
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


def render_key_insights(filtered_tradebook: pd.DataFrame) -> None:
    """
    Render key insights panel.
    
    Args:
        filtered_tradebook: Filtered tradebook DataFrame
    """
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


def render_trading_style_metrics(sentiment_data: dict) -> None:
    """
    Render trading style performance metrics.
    
    Args:
        sentiment_data: Dictionary with trading style analysis data
    """
    total_analyzed = (sentiment_data['intraday']['count'] + 
                     sentiment_data['btst']['count'] + 
                     sentiment_data['velocity']['count'] + 
                     sentiment_data['swing']['count'])
    
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
