"""
Utility functions for formatting currency and percentages
"""

import pandas as pd


def format_currency(value):
    """
    Format value as Indian Rupee currency.
    
    Args:
        value: Numeric value to format
        
    Returns:
        str: Formatted currency string (e.g., "₹1,234.56")
    """
    if pd.isna(value):
        return "₹0.00"
    return f"₹{value:,.2f}"


def format_percentage(value):
    """
    Format value as percentage.
    
    Args:
        value: Numeric value to format (e.g., 50.5 for 50.5%)
        
    Returns:
        str: Formatted percentage string (e.g., "50.50%")
    """
    if pd.isna(value):
        return "0.00%"
    return f"{value:.2f}%"
