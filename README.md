# ZeroJournal - Trading Dashboard for Swing Traders

A comprehensive trading analytics dashboard built with Streamlit for analyzing swing trading performance. Upload your Zerodha tradebook and P&L Excel files to get detailed insights into your trading strategies.

## Features

### 📊 Performance Metrics
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Gross profit / Gross loss ratio
- **Average Holding Period**: Mean days between buy and sell
- **Sharpe Ratio**: Risk-adjusted return metric
- **Max Drawdown**: Maximum peak-to-trough decline

### 📈 P&L Analysis
- **Interactive Equity Curve**: Portfolio value over time with zoom/pan/hover
- **Daily/Weekly/Monthly P&L Trends**: Time-series analysis with interactive charts
- **Cumulative P&L Chart**: Portfolio growth visualization
- **Top Winners/Losers**: Best and worst performing stocks with detailed breakdown

### 📋 Trade Analysis
- **Win Rate by Symbol**: Performance breakdown by stock
- **Average Holding Period by Stock**: Duration analysis per symbol
- **Trade Duration Distribution**: Histogram of holding periods

### 🔍 Interactive Features
- **Date Range Filtering**: Analyze specific time periods
- **Symbol Filtering**: Focus on specific stocks
- **Export Functionality**: Download filtered data as CSV
- **Interactive Charts**: All charts support zoom, pan, and hover tooltips (powered by Plotly)

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. **Clone or download this repository**
   ```bash
   cd ZeroJournal
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the Dashboard

1. **Start the Streamlit app**
   ```bash
   streamlit run app.py
   ```

2. **Upload Excel Files**
   - The app will open in your browser (usually at `http://localhost:8501`)
   - In the sidebar, upload your **Tradebook** Excel file
   - Upload your **P&L Statement** Excel file
   - Both files should be in Zerodha export format

3. **Analyze Your Data**
   - The dashboard will automatically load and analyze your trading data
   - Use the sidebar filters to:
     - Select date ranges
     - Filter by specific symbols
   - Explore the interactive charts and metrics
   - Export filtered data using the export buttons

### File Format Requirements

The dashboard expects Zerodha Excel export files with the following structure:

**Tradebook File:**
- Headers at row 14 (0-indexed)
- Required columns: Symbol, ISIN, Trade Date, Exchange, Segment, Series, Trade Type, Auction, Quantity, Price, Trade ID, Order ID, Order Execution Time

**P&L Statement File:**
- Headers at row 37 (0-indexed)
- Required columns: Symbol, ISIN, Quantity, Buy Value, Sell Value, Realized P&L, Realized P&L Pct.

## Project Structure

```
ZeroJournal/
├── services/
│   ├── __init__.py
│   ├── excel_reader.py          # Excel file parsing
│   └── metrics_calculator.py    # Trading metrics calculations
├── app.py                        # Main Streamlit application
├── config.py                     # Configuration constants
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## Deployment

### Streamlit Cloud (Free Hosting)

1. **Push your code to GitHub**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with your GitHub account
   - Click "New app"
   - Select your repository and branch
   - Set main file path: `app.py`
   - Click "Deploy"

3. **Access your dashboard**
   - Your dashboard will be available at a public URL
   - Share with others or keep it private (free tier supports both)

### Multi-User Support

The dashboard is designed for multi-user deployment:
- Each user session is independent
- Files are stored in session state (not persisted to disk)
- No shared storage needed
- Works seamlessly on Streamlit Cloud

## Features in Detail

### Interactive Charts
All charts are built with Plotly and support:
- **Zoom**: Click and drag to zoom into specific regions
- **Pan**: Click and drag to pan across the chart
- **Hover**: Hover over data points to see detailed tooltips
- **Reset**: Double-click to reset the view

### Export Options
- Export filtered tradebook data as CSV
- Export filtered P&L data as CSV
- Files are automatically named with the selected date range

### Filtering
- **Date Range**: Select any date range within your data
- **Symbol Filter**: Select specific stocks to analyze
- Filters apply to all charts and metrics automatically

## Troubleshooting

### Common Issues

1. **File Upload Errors**
   - Ensure files are in correct Zerodha format
   - Check that both files are uploaded
   - Verify file extensions are `.xlsx` or `.xls`

2. **No Data Showing**
   - Check date range filter - it might be excluding all data
   - Verify symbol filter - ensure symbols are selected
   - Check file format matches expected structure

3. **Installation Issues**
   - Ensure Python 3.8+ is installed
   - Use virtual environment: `python -m venv venv`
   - Activate venv: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)

## Future Enhancements

Potential features for future versions:
- Additional metrics (Sortino ratio, Calmar ratio, etc.)
- Comparison between different time periods
- Risk analysis and position sizing insights
- Trade journal entries and notes
- Email/notification alerts

## License

This project is open source and available for personal and commercial use.

## Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests

## Support

For issues or questions, please create an issue on the GitHub repository.

---

**Happy Trading! 📈**
