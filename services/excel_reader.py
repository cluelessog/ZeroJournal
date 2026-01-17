"""
Excel Reader Service - Parses tradebook and P&L Excel files
"""

import pandas as pd
from io import BytesIO
import config


def read_tradebook(file):
    """
    Parse tradebook Excel file from uploaded file object.
    
    Args:
        file: File object (BytesIO) from Streamlit file uploader
        
    Returns:
        tuple: (DataFrame, error_message)
        - DataFrame with tradebook data if successful, None otherwise
        - error_message string if error occurred, None otherwise
    """
    try:
        # Read Excel file
        df = pd.read_excel(file, header=config.TRADEBOOK_HEADER_ROW)
        
        # Drop empty first column if it exists
        if 'Unnamed: 0' in df.columns:
            df = df.drop('Unnamed: 0', axis=1)
        
        # Validate required columns
        missing_cols = set(config.TRADEBOOK_REQUIRED_COLUMNS) - set(df.columns)
        if missing_cols:
            return None, f"Missing required columns in tradebook: {', '.join(missing_cols)}"
        
        # Parse Trade Date to datetime
        df['Trade Date'] = pd.to_datetime(df['Trade Date'], errors='coerce')
        
        # Check for invalid dates
        if df['Trade Date'].isna().any():
            return None, "Invalid date format found in Trade Date column"
        
        # Ensure Quantity and Price are numeric
        df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
        
        if df['Quantity'].isna().any() or df['Price'].isna().any():
            return None, "Invalid numeric values found in Quantity or Price columns"
        
        # Remove rows with any remaining NaN values in critical columns
        df = df.dropna(subset=['Symbol', 'Trade Date', 'Trade Type'])
        
        # Reset index
        df = df.reset_index(drop=True)
        
        return df, None
        
    except Exception as e:
        return None, f"Error reading tradebook file: {str(e)}"


def read_pnl(file):
    """
    Parse P&L Excel file from uploaded file object.
    
    Args:
        file: File object (BytesIO) from Streamlit file uploader
        
    Returns:
        tuple: (DataFrame, error_message)
        - DataFrame with P&L data if successful, None otherwise
        - error_message string if error occurred, None otherwise
    """
    try:
        # Read Excel file
        df = pd.read_excel(file, header=config.PNL_HEADER_ROW)
        
        # Drop empty first column if it exists
        if 'Unnamed: 0' in df.columns:
            df = df.drop('Unnamed: 0', axis=1)
        
        # Validate required columns
        missing_cols = set(config.PNL_REQUIRED_COLUMNS) - set(df.columns)
        if missing_cols:
            return None, f"Missing required columns in P&L file: {', '.join(missing_cols)}"
        
        # Ensure numeric columns are numeric
        numeric_cols = ['Quantity', 'Buy Value', 'Sell Value', 'Realized P&L', 'Realized P&L Pct.']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Remove rows with NaN in critical columns
        df = df.dropna(subset=['Symbol', 'Realized P&L'])
        
        # Reset index
        df = df.reset_index(drop=True)
        
        return df, None
        
    except Exception as e:
        return None, f"Error reading P&L file: {str(e)}"
