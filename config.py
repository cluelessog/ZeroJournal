"""
Configuration constants for ZeroJournal trading dashboard
"""

# Excel file structure constants
TRADEBOOK_HEADER_ROW = 14  # 0-indexed row where column headers start
PNL_HEADER_ROW = 37  # 0-indexed row where P&L data headers start

# Expected columns for validation
TRADEBOOK_REQUIRED_COLUMNS = [
    'Symbol', 'ISIN', 'Trade Date', 'Exchange', 'Segment', 
    'Series', 'Trade Type', 'Auction', 'Quantity', 'Price', 
    'Trade ID', 'Order ID', 'Order Execution Time'
]

PNL_REQUIRED_COLUMNS = [
    'Symbol', 'ISIN', 'Quantity', 'Buy Value', 'Sell Value', 
    'Realized P&L', 'Realized P&L Pct.'
]

# Supported file formats
SUPPORTED_EXCEL_FORMATS = ['.xlsx', '.xls']

# Risk-free rate for Sharpe ratio calculation (assuming 0% for now)
RISK_FREE_RATE = 0.0
