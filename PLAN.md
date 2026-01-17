# ZeroJournal - Trading Dashboard Implementation Plan

## Overview
Build a Streamlit-based trading dashboard with interactive charts and analytics for swing traders, analyzing Excel tradebook and P&L data.

## Tech Stack
- **Framework**: Streamlit
- **Charts**: Plotly (for interactive visualizations)
- **Data Processing**: Pandas, NumPy
- **Excel Reading**: openpyxl, pandas

## Project Structure
```
ZeroJournal/
├── services/
│   ├── __init__.py
│   ├── excel_reader.py          # Parse tradebook and P&L Excel files
│   └── metrics_calculator.py    # Calculate swing trading metrics
├── app.py                        # Main Streamlit application
├── config.py                     # Configuration (file paths, etc.)
├── requirements.txt              # Python dependencies
└── README.md                     # Setup and usage instructions
```

## Implementation Details

### 1. Configuration (`config.py`)
- Constants for Excel file structure:
  - Tradebook header row: 14 (0-indexed)
  - PnL header row: 37 (0-indexed)
  - Date format handling
  - Supported file formats (validation)
- No hardcoded file paths - files will be uploaded via UI

### 2. Excel Reader Service (`services/excel_reader.py`)
**Functions:**
- `read_tradebook(file)`: Parse tradebook Excel (from uploaded file or BytesIO), return DataFrame
  - Accept file object (BytesIO from Streamlit upload)
  - Drop empty first column
  - Parse Trade Date to datetime
  - Handle missing values
  - Return tuple: (DataFrame, error_message)
- `read_pnl(file)`: Parse P&L Excel (from uploaded file or BytesIO), return DataFrame
  - Accept file object (BytesIO from Streamlit upload)
  - Drop empty first column
  - Calculate trade quantities and values
  - Return tuple: (DataFrame, error_message)

**Data Validation:**
- Verify file is valid Excel format
- Verify required columns exist (check for expected Zerodha format columns)
- Handle date parsing errors gracefully
- Validate numeric fields
- Return descriptive error messages for invalid files
- Support both `.xlsx` and `.xls` formats

### 3. Metrics Calculator Service (`services/metrics_calculator.py`)
**Performance Metrics:**
- `calculate_win_rate(trades)`: % of profitable trades
- `calculate_profit_factor(pnl_data)`: Gross profit / Gross loss
- `calculate_avg_holding_period(trades)`: Average days between buy and sell
- `calculate_sharpe_ratio(daily_returns, risk_free_rate=0)`: Risk-adjusted return
- `calculate_max_drawdown(cumulative_pnl)`: Maximum peak-to-trough decline

**P&L Analysis:**
- `get_daily_pnl(trades)`: Group trades by date, calculate daily P&L
- `get_weekly_pnl(trades)`: Weekly aggregation
- `get_monthly_pnl(trades)`: Monthly aggregation
- `get_cumulative_pnl(daily_pnl)`: Cumulative P&L over time
- `get_equity_curve(trades)`: Portfolio value over time

**Trade Analysis:**
- `get_win_rate_by_symbol(pnl_data)`: Win rate grouped by stock symbol
- `get_avg_holding_period_by_stock(trades)`: Average days held per stock
- `get_trade_duration_distribution(trades)`: Distribution of holding periods

**Helper Functions:**
- `match_buy_sell_trades(trades)`: Pair buy and sell trades to calculate holding periods
- `filter_by_date_range(data, start_date, end_date)`: Date range filtering
- `filter_by_symbols(data, symbols)`: Symbol filtering

### 4. Main Streamlit App (`app.py`)
**Layout Structure:**
```
- Sidebar (File Upload & Filters)
  - File Upload Section
    - Upload tradebook Excel file
    - Upload P&L Excel file
    - File format validation and error messages
  - Date range picker (enabled only if files uploaded)
  - Multi-select symbol filter (enabled only if files uploaded)
  - Export buttons (CSV/Excel) (enabled only if files uploaded)
  
- Main Content
  - Performance Metrics Section (5 metric cards)
  - P&L Analysis Section
    - Interactive Equity Curve (Plotly line chart)
    - Daily/Weekly/Monthly P&L Tabs (Plotly bar/line charts)
    - Cumulative P&L Chart (Plotly line chart)
  - Top Winners/Losers Section
    - Data table with sorting
  - Trade Analysis Section
    - Win Rate by Symbol (Plotly bar chart)
    - Average Holding Period by Stock (Plotly bar chart)
    - Trade Duration Distribution (Plotly histogram)
```

**Key Components:**

1. **File Upload Section:**
   - `st.file_uploader()` for tradebook Excel file
     - Accepts `.xlsx`, `.xls` files
     - Store in `st.session_state.tradebook_file`
     - Show file name and size after upload
     - Clear button to remove uploaded file
   - `st.file_uploader()` for P&L Excel file
     - Accepts `.xlsx`, `.xls` files
     - Store in `st.session_state.pnl_file`
     - Show file name and size after upload
     - Clear button to remove uploaded file
   - Validation: Check if both files are uploaded before enabling other features
   - Error handling: Display clear error messages for invalid file formats
   - Instructions: Show file format requirements (Zerodha tradebook/P&L format)

2. **Sidebar Filters (conditional on file upload):**
   - `st.date_input()` for start/end dates (disabled if no files)
   - `st.multiselect()` for symbol filtering (disabled if no files)
   - Export buttons using `st.download_button()` (disabled if no files)

2. **Performance Metrics Cards:**
   - Use `st.metric()` for win rate, profit factor, avg holding period
   - Display Sharpe ratio and max drawdown
   - Color-coded (green for positive, red for negative)

3. **Interactive Charts (Plotly):**
   - Equity Curve: Line chart with hover tooltips, zoom/pan
   - Daily/Weekly/Monthly P&L: Bar/line charts with date on x-axis
   - Cumulative P&L: Line chart showing portfolio growth
   - Win Rate by Symbol: Horizontal bar chart, sorted
   - Holding Period by Stock: Bar chart, sorted by duration
   - Duration Distribution: Histogram with bins for days

4. **Data Tables:**
   - Top winners/losers using `st.dataframe()` with sorting
   - Show: Symbol, Quantity, Buy Value, Sell Value, Realized P&L, P&L %

5. **Export Functionality:**
   - Generate filtered DataFrame
   - Export to CSV using `st.download_button()` with `to_csv()`
   - Export to Excel using `st.download_button()` with `to_excel()` (requires openpyxl)

**Data Flow:**
1. User uploads tradebook and P&L Excel files via sidebar
2. Files stored in `st.session_state` (persists during session)
3. Validate file format and parse with Excel reader service (cache parsed data with `@st.cache_data`)
4. Apply filters from sidebar
5. Calculate metrics for filtered data
6. Generate interactive charts
7. Update all UI components
8. Show placeholder/instructions if files not uploaded

### 5. Requirements (`requirements.txt`)
```
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
plotly>=5.17.0
openpyxl>=3.1.0
```

### 6. README (`README.md`)
- Project description
- Installation instructions
- How to run: `streamlit run app.py`
- File upload instructions (supported formats, expected file structure)
- Expected Excel file format (Zerodha tradebook/P&L format)
- Feature list
- Deployment instructions for Streamlit Cloud
- Multi-user usage notes

## Features Implementation Checklist

### Performance Metrics ✓
- [x] Win rate calculation
- [x] Profit factor calculation
- [x] Average holding period
- [x] Sharpe ratio
- [x] Max drawdown

### P&L Analysis ✓
- [x] Daily/weekly/monthly P&L trends (interactive Plotly charts)
- [x] Cumulative P&L chart (interactive)
- [x] Top winners/losers table
- [x] Interactive equity curve

### Trade Analysis ✓
- [x] Win rate by symbol (interactive bar chart)
- [x] Average holding period per stock (interactive bar chart)
- [x] Trade duration distribution (interactive histogram)

### Interactive Features ✓
- [x] Date range filtering
- [x] Symbol filtering
- [x] Export to CSV/Excel
- [x] All charts interactive (Plotly with zoom, pan, hover)

## Implementation Order
1. Set up project structure and dependencies
2. Create Excel reader service
3. Create metrics calculator service
4. Build main Streamlit app with filters
5. Add performance metrics cards
6. Implement P&L charts (daily/weekly/monthly, cumulative, equity curve)
7. Add top winners/losers table
8. Create trade analysis visualizations
9. Add export functionality
10. Testing and refinement

## Notes
- All charts use Plotly for interactivity (zoom, pan, hover, tooltips)
- Use `@st.cache_data` with `hash_funcs` to cache parsed Excel data (key on file content, not just filename)
- Use `st.session_state` to persist uploaded files across reruns
- Handle edge cases (no trades in date range, single symbol, no files uploaded, etc.)
- Format currency values with ₹ symbol and commas
- Format percentages with 2 decimal places
- Use responsive layout with columns for metric cards
- **Scalability considerations:**
  - File uploads stored in session state (not persisted to disk)
  - Each user session is independent
  - No shared file storage needed (ready for Streamlit Cloud multi-user deployment)
  - Clear session state when files are removed
  - Show loading indicators during file parsing
