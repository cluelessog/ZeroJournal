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
# Note: Only .xlsx is supported. .xls support would require xlrd<2.0 which has compatibility issues.
SUPPORTED_EXCEL_FORMATS = ['.xlsx']

# Risk-free rate for Sharpe ratio calculation (assuming 0% for now)
RISK_FREE_RATE = 0.0

# Performance analysis constants
ROLLING_WINDOW_SIZE = 20  # Number of trades in rolling window for expectancy calculation
QUANTILE_75TH = 0.75  # 75th percentile threshold for MAE/MFE analysis

# Chart and visualization constants
CHART_MARKER_SIZE_MIN = 8  # Minimum marker size in pixels
CHART_MARKER_SIZE_MAX = 30  # Maximum marker size in pixels
CHART_PROFIT_FACTOR_CAP = 5.0  # Maximum profit factor value to display (actual shown in hover)

# Thread pool and concurrency settings
THREAD_POOL_MAX_WORKERS = 10  # Maximum concurrent workers for parallel processing
API_TIMEOUT_SECONDS = 10  # Timeout for API requests in seconds

# Cache settings
CACHE_TTL_SECONDS = 1800  # Cache time-to-live in seconds (30 minutes)

# Progress callback percentages (for MAE/MFE calculation)
PROGRESS_INIT = 5  # Initial progress percentage
PROGRESS_MATCHING = 10  # Progress after matching trades
PROGRESS_PREPARE = 15  # Progress after preparing fetch requests
PROGRESS_FETCH_START = 20  # Progress when starting data fetch
PROGRESS_FETCH_RANGE = 70  # Progress range for fetch operations (20-90%)
