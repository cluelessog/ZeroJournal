"""
Excel Reader Service - Parses tradebook and P&L Excel files
"""

import pandas as pd
from io import BytesIO
from typing import Tuple, Optional, Dict
import config


def read_tradebook(file: BytesIO) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
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


def read_pnl(file: BytesIO) -> Tuple[Optional[pd.DataFrame], Optional[str], float]:
    """
    Parse P&L Excel file from uploaded file object.
    
    Args:
        file: File object (BytesIO) from Streamlit file uploader
        
    Returns:
        tuple: (DataFrame, error_message, total_charges)
        - DataFrame with P&L data if successful, None otherwise
        - error_message string if error occurred, None otherwise
        - total_charges float (sum of all charges)
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
            return None, f"Missing required columns in P&L file: {', '.join(missing_cols)}", 0.0
        
        # Ensure numeric columns are numeric
        numeric_cols = ['Quantity', 'Buy Value', 'Sell Value', 'Realized P&L', 'Realized P&L Pct.']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Remove rows with NaN in critical columns
        df = df.dropna(subset=['Symbol', 'Realized P&L'])
        
        # Reset index
        df = df.reset_index(drop=True)
        
        # Extract charges from the P&L file (charges are in rows 14-32, ~0-indexed row 20)
        total_brokerage_taxes, dp_charges = extract_charges(file)
        total_charges = total_brokerage_taxes  # For backward compatibility
        
        return df, None, total_charges
        
    except Exception as e:
        return None, f"Error reading P&L file: {str(e)}", 0.0


def extract_charges(file: BytesIO) -> Tuple[float, Dict[str, float]]:
    """
    Extract charges from P&L Excel file.
    Separates brokerage/taxes (pro-rata allocation) from DP charges (date-specific).
    
    Args:
        file: File object (BytesIO) from Streamlit file uploader
        
    Returns:
        tuple: (total_brokerage_taxes, dp_charges_dict)
        - total_brokerage_taxes: Sum of brokerage and tax charges
        - dp_charges_dict: Dict {date_str: amount} for DP charges on actual dates
    """
    try:
        # Reset file pointer
        file.seek(0)
        
        # Read the charges section (around row 14-32)
        # We'll read rows 14-35 to capture the charges section
        charges_df = pd.read_excel(file, header=None, skiprows=13, nrows=25)
        
        total_brokerage_taxes = 0.0
        dp_charges_dict = {}
        
        # Charges that should be allocated pro-rata by turnover
        brokerage_tax_labels = [
            'Brokerage', 'Transaction Charges', 'Exchange Transaction Charges',
            'Clearing Charges', 'GST', 'State GST', 'Central GST', 'Integrated GST',
            'Securities Transaction Tax', 'STT', 'SEBI Turnover Fees',
            'Stamp Duty', 'IPFT'
        ]
        
        # DP-related charges (if dates are available, will be on actual dates)
        # For now, we'll treat all as brokerage/taxes and extract dates if found
        dp_labels = ['DP Charges', 'DP', 'Depository Charges']
        
        # Check if column 1 (index 1) contains charge labels and column 2 (index 2) contains amounts
        for idx, row in charges_df.iterrows():
            if len(row) >= 3:
                label = str(row.iloc[1]) if pd.notna(row.iloc[1]) else ""
                amount = row.iloc[2] if pd.notna(row.iloc[2]) else None
                
                # Skip summary rows
                if label.lower() in ['summary', 'charges', 'account head']:
                    continue
                
                # Check for DP charges (would need date extraction - simplified for now)
                is_dp_charge = any(label.lower().startswith(dp.lower()) for dp in dp_labels)
                
                # Check if this row contains a charge
                is_charge = any(label.lower().startswith(charge.lower()) 
                              for charge in brokerage_tax_labels + dp_labels)
                
                if is_charge and pd.notna(amount) and isinstance(amount, (int, float)):
                    charge_amount = abs(float(amount))
                    
                    if is_dp_charge:
                        # DP charges - for now add to total (can be enhanced with date extraction)
                        # In Zerodha files, DP charges usually don't have dates in this section
                        total_brokerage_taxes += charge_amount
                    else:
                        # Brokerage and taxes
                        total_brokerage_taxes += charge_amount
        
        return total_brokerage_taxes, dp_charges_dict
        
    except Exception as e:
        # If extraction fails, return 0 (charges will be optional)
        return 0.0, {}
