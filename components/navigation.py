"""
Navigation components for ZeroJournal dashboard
Extracted from app.py for better modularity
"""

import streamlit as st


def render_navigation_bar() -> None:
    """
    Render quick navigation bar with Material Design buttons.
    """
    st.markdown("---")
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
