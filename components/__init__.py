"""
Components package for ZeroJournal dashboard
"""

from components.sidebar import (
    render_file_upload,
    render_navigation_buttons,
    render_portfolio_settings,
    render_filters,
    render_export_section
)
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

__all__ = [
    # Sidebar
    'render_file_upload',
    'render_navigation_buttons',
    'render_portfolio_settings',
    'render_filters',
    'render_export_section',
    # Charts
    'render_equity_curve',
    'render_pnl_tabs',
    'render_rolling_expectancy_chart',
    'render_monthly_expectancy_chart',
    'render_cumulative_metrics_charts',
    'render_win_rate_chart',
    'render_holding_period_chart',
    'render_trade_duration_distribution',
    # Metrics
    'render_performance_metrics',
    'render_advanced_metrics',
    'render_key_insights',
    'render_trading_style_metrics',
    # Navigation
    'render_navigation_bar',
]
