"""
Sector Mapper Service - Fetches sector information for stock symbols
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from utils.logger import logger


# Cache for sector information to avoid repeated API calls
_sector_cache = {}


def get_stock_sector(symbol: str) -> str:
    """
    Fetch sector information for a stock symbol.
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')
        
    Returns:
        str: Sector name or 'Unknown'
    """
    # Check cache first
    if symbol in _sector_cache:
        return _sector_cache[symbol]
    
    try:
        # Try with .NS suffix for NSE stocks
        ticker_symbol = f"{symbol}.NS"
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        # Get sector information
        sector = info.get('sector', 'Unknown')
        
        # If sector not found, try industry
        if sector == 'Unknown' or not sector:
            sector = info.get('industry', 'Unknown')
        
        # Cache the result
        _sector_cache[symbol] = sector
        return sector
        
    except Exception as e:
        logger.error(f"Error fetching sector for {symbol}: {str(e)}")
        _sector_cache[symbol] = 'Unknown'
        return 'Unknown'


def get_sectors_for_symbols(
    symbols: List[str], 
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> Dict[str, str]:
    """
    Fetch sector information for multiple symbols using parallel processing.
    Falls back to sequential processing if parallel processing fails.
    
    Args:
        symbols: List of stock symbols
        progress_callback: Optional callback function for progress updates
        
    Returns:
        dict: Dictionary mapping symbol to sector
    """
    try:
        # Try parallel processing first
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import threading
        
        sector_map = {}
        total = len(symbols)
        completed = 0
        lock = threading.Lock()
        
        def fetch_with_progress(symbol):
            """Fetch sector and update progress"""
            sector = get_stock_sector(symbol)
            return (symbol, sector)
        
        # Use parallel processing with max workers from config
        from config import THREAD_POOL_MAX_WORKERS
        max_workers = min(THREAD_POOL_MAX_WORKERS, len(symbols))
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_symbol = {executor.submit(fetch_with_progress, symbol): symbol for symbol in symbols}
            
            # Process completed tasks
            for future in as_completed(future_to_symbol):
                try:
                    symbol, sector = future.result()
                    sector_map[symbol] = sector
                except Exception as e:
                    # If individual fetch fails, mark as Unknown
                    symbol = future_to_symbol.get(future, 'UNKNOWN')
                    sector_map[symbol] = 'Unknown'
                    logger.error(f"Error fetching sector for {symbol}: {str(e)}")
                
                # Update progress with thread safety
                with lock:
                    completed += 1
                    if progress_callback:
                        progress_callback(completed, total)
        
        return sector_map
        
    except Exception as e:
        # Fallback to sequential processing if parallel fails
        logger.warning(f"Parallel processing failed, falling back to sequential: {str(e)}")
        sector_map = {}
        total = len(symbols)
        
        for i, symbol in enumerate(symbols):
            sector = get_stock_sector(symbol)
            sector_map[symbol] = sector
            
            if progress_callback:
                progress_callback(i + 1, total)
        
        return sector_map


def add_sector_to_dataframe(df, symbol_column='Symbol'):
    """
    Add sector column to a dataframe based on stock symbols.
    
    Args:
        df: DataFrame with stock symbols
        symbol_column: Name of the column containing symbols
        
    Returns:
        DataFrame: DataFrame with added 'Sector' column
    """
    if df is None or len(df) == 0:
        return df
    
    df = df.copy()
    unique_symbols = df[symbol_column].unique()
    
    # Get sectors for all unique symbols
    sector_map = get_sectors_for_symbols(unique_symbols)
    
    # Add sector column
    df['Sector'] = df[symbol_column].map(sector_map)
    
    return df


def get_sector_summary(df, symbol_column='Symbol'):
    """
    Get summary of sectors present in the dataframe.
    
    Args:
        df: DataFrame with stock symbols
        symbol_column: Name of the column containing symbols
        
    Returns:
        DataFrame: Summary with sector and count
    """
    if df is None or len(df) == 0:
        return pd.DataFrame(columns=['Sector', 'Count'])
    
    unique_symbols = df[symbol_column].unique()
    sector_map = get_sectors_for_symbols(unique_symbols)
    
    # Count symbols per sector
    sector_counts = pd.Series(sector_map).value_counts().reset_index()
    sector_counts.columns = ['Sector', 'Count']
    
    return sector_counts
