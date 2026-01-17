"""
Metrics Calculator Service - Calculates swing trading metrics
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import config


def calculate_win_rate(pnl_data):
    """
    Calculate win rate (% of profitable trades/stocks).
    
    Args:
        pnl_data: DataFrame with P&L data
        
    Returns:
        float: Win rate as percentage (0-100)
    """
    if pnl_data is None or len(pnl_data) == 0:
        return 0.0
    
    profitable = len(pnl_data[pnl_data['Realized P&L'] > 0])
    total = len(pnl_data[pnl_data['Realized P&L'] != 0])
    
    if total == 0:
        return 0.0
    
    return (profitable / total) * 100


def calculate_profit_factor(pnl_data):
    """
    Calculate profit factor (gross profit / gross loss).
    
    Args:
        pnl_data: DataFrame with P&L data
        
    Returns:
        float: Profit factor (positive number, >1 is good)
    """
    if pnl_data is None or len(pnl_data) == 0:
        return 0.0
    
    gross_profit = pnl_data[pnl_data['Realized P&L'] > 0]['Realized P&L'].sum()
    gross_loss = abs(pnl_data[pnl_data['Realized P&L'] < 0]['Realized P&L'].sum())
    
    if gross_loss == 0:
        return float('inf') if gross_profit > 0 else 0.0
    
    return gross_profit / gross_loss


def match_buy_sell_trades(trades):
    """
    Match buy and sell trades to calculate holding periods.
    Uses FIFO (First In First Out) matching and considers execution time.
    Returns list of (holding_days, quantity) tuples for weighted averaging.
    
    Args:
        trades: DataFrame with tradebook data
        
    Returns:
        list: List of tuples (holding_days, quantity) for each matched trade
    """
    holding_periods = []  # List of (days, quantity) tuples
    
    # Group trades by symbol
    for symbol in trades['Symbol'].unique():
        symbol_trades = trades[trades['Symbol'] == symbol].copy()
        
        # Sort by Trade Date and Order Execution Time for proper FIFO matching
        if 'Order Execution Time' in symbol_trades.columns:
            # Parse execution time if available
            symbol_trades['ExecTime'] = pd.to_datetime(
                symbol_trades['Order Execution Time'], 
                errors='coerce'
            )
            # Sort by date first, then by execution time if available, then by Trade ID
            symbol_trades = symbol_trades.sort_values(
                ['Trade Date', 'ExecTime', 'Trade ID'],
                na_position='last'
            )
        else:
            symbol_trades = symbol_trades.sort_values(['Trade Date', 'Trade ID'])
        
        buy_trades = []  # List of {date, quantity}
        
        for _, trade in symbol_trades.iterrows():
            trade_date = trade['Trade Date']
            
            if pd.isna(trade_date):
                continue
                
            if trade['Trade Type'] == 'buy':
                # Add buy trade to queue (FIFO)
                buy_trades.append({
                    'date': trade_date,
                    'quantity': trade['Quantity']
                })
            elif trade['Trade Type'] == 'sell' and len(buy_trades) > 0:
                # Match sell with earliest buy (FIFO)
                remaining_sell = trade['Quantity']
                
                while remaining_sell > 0 and len(buy_trades) > 0:
                    buy = buy_trades[0]
                    buy_date = buy['date']
                    
                    # Calculate holding period in days
                    holding_days = (trade_date - buy_date).days
                    
                    # Ensure holding period is non-negative (sell should be after buy)
                    if holding_days < 0:
                        # This shouldn't happen if data is sorted correctly
                        # Skip this buy and try next
                        buy_trades.pop(0)
                        continue
                    
                    if buy['quantity'] <= remaining_sell:
                        # Use entire buy trade
                        matched_qty = buy['quantity']
                        holding_periods.append((holding_days, matched_qty))
                        remaining_sell -= matched_qty
                        buy_trades.pop(0)
                    else:
                        # Use partial buy trade
                        matched_qty = remaining_sell
                        holding_periods.append((holding_days, matched_qty))
                        buy['quantity'] -= matched_qty
                        remaining_sell = 0
    
    return holding_periods


def calculate_avg_holding_period(trades):
    """
    Calculate average holding period in days (weighted by quantity).
    
    Args:
        trades: DataFrame with tradebook data
        
    Returns:
        float: Average holding period in days (weighted average)
    """
    if trades is None or len(trades) == 0:
        return 0.0
    
    holding_periods = match_buy_sell_trades(trades)
    
    if len(holding_periods) == 0:
        return 0.0
    
    # Calculate weighted average: sum(days * quantity) / sum(quantity)
    total_days = sum(days * qty for days, qty in holding_periods)
    total_quantity = sum(qty for _, qty in holding_periods)
    
    if total_quantity == 0:
        return 0.0
    
    return total_days / total_quantity


def get_daily_pnl(trades):
    """
    Calculate daily P&L by aggregating trades by date.
    
    Args:
        trades: DataFrame with tradebook data
        
    Returns:
        DataFrame: Daily P&L with columns ['Date', 'PnL']
    """
    if trades is None or len(trades) == 0:
        return pd.DataFrame(columns=['Date', 'PnL'])
    
    # Group by date and calculate net P&L
    daily_pnl = []
    
    for date in trades['Trade Date'].unique():
        date_trades = trades[trades['Trade Date'] == date]
        
        # Calculate net P&L for the day (simplified: sell value - buy value)
        buy_trades = date_trades[date_trades['Trade Type'] == 'buy']
        sell_trades = date_trades[date_trades['Trade Type'] == 'sell']
        
        # Handle cases where there are no buys or sells
        if len(buy_trades) > 0:
            buy_qty = buy_trades['Quantity'].sum()
            buy_price = buy_trades['Price'].mean()
            if pd.isna(buy_price):
                buy_price = 0
            buy_value = buy_qty * buy_price
        else:
            buy_value = 0
        
        if len(sell_trades) > 0:
            sell_qty = sell_trades['Quantity'].sum()
            sell_price = sell_trades['Price'].mean()
            if pd.isna(sell_price):
                sell_price = 0
            sell_value = sell_qty * sell_price
        else:
            sell_value = 0
        
        # This is approximate; actual P&L should come from P&L file
        daily_pnl.append({
            'Date': pd.to_datetime(date),
            'PnL': sell_value - buy_value
        })
    
    return pd.DataFrame(daily_pnl).sort_values('Date')


def get_daily_pnl_from_pnl_data(pnl_data, trades):
    """
    Calculate daily P&L by matching P&L data with trade dates.
    This is more accurate than get_daily_pnl.
    
    Args:
        pnl_data: DataFrame with P&L data
        trades: DataFrame with tradebook data
        
    Returns:
        DataFrame: Daily P&L with columns ['Date', 'PnL']
    """
    if pnl_data is None or len(pnl_data) == 0:
        return pd.DataFrame(columns=['Date', 'PnL'])
    
    # Get the last trade date for each symbol to calculate daily P&L
    symbol_dates = trades.groupby('Symbol')['Trade Date'].max().reset_index()
    
    daily_pnl_dict = {}
    
    for _, row in pnl_data.iterrows():
        symbol = row['Symbol']
        pnl = row['Realized P&L']
        
        # Get the last trade date for this symbol
        symbol_date = symbol_dates[symbol_dates['Symbol'] == symbol]['Trade Date'].values
        
        if len(symbol_date) > 0:
            date = pd.to_datetime(symbol_date[0]).date()
            
            if date in daily_pnl_dict:
                daily_pnl_dict[date] += pnl
            else:
                daily_pnl_dict[date] = pnl
    
    # Convert to DataFrame
    daily_pnl_list = [{'Date': pd.to_datetime(date), 'PnL': pnl} 
                      for date, pnl in daily_pnl_dict.items()]
    
    return pd.DataFrame(daily_pnl_list).sort_values('Date')


def get_weekly_pnl(daily_pnl):
    """
    Aggregate daily P&L to weekly.
    
    Args:
        daily_pnl: DataFrame with daily P&L
        
    Returns:
        DataFrame: Weekly P&L
    """
    if daily_pnl is None or len(daily_pnl) == 0:
        return pd.DataFrame(columns=['Week', 'PnL'])
    
    daily_pnl = daily_pnl.copy()
    daily_pnl['Week'] = daily_pnl['Date'].dt.to_period('W').dt.start_time
    
    weekly_pnl = daily_pnl.groupby('Week')['PnL'].sum().reset_index()
    weekly_pnl.columns = ['Week', 'PnL']
    
    return weekly_pnl


def get_monthly_pnl(daily_pnl):
    """
    Aggregate daily P&L to monthly.
    
    Args:
        daily_pnl: DataFrame with daily P&L
        
    Returns:
        DataFrame: Monthly P&L
    """
    if daily_pnl is None or len(daily_pnl) == 0:
        return pd.DataFrame(columns=['Month', 'PnL'])
    
    daily_pnl = daily_pnl.copy()
    daily_pnl['Month'] = daily_pnl['Date'].dt.to_period('M').dt.start_time
    
    monthly_pnl = daily_pnl.groupby('Month')['PnL'].sum().reset_index()
    monthly_pnl.columns = ['Month', 'PnL']
    
    return monthly_pnl


def get_cumulative_pnl(daily_pnl):
    """
    Calculate cumulative P&L over time.
    
    Args:
        daily_pnl: DataFrame with daily P&L
        
    Returns:
        DataFrame: Cumulative P&L with columns ['Date', 'Cumulative P&L']
    """
    if daily_pnl is None or len(daily_pnl) == 0:
        return pd.DataFrame(columns=['Date', 'Cumulative P&L'])
    
    cumulative = daily_pnl.copy()
    cumulative['Cumulative P&L'] = cumulative['PnL'].cumsum()
    
    return cumulative[['Date', 'Cumulative P&L']]


def get_equity_curve(daily_pnl, initial_value=0):
    """
    Calculate equity curve (portfolio value over time).
    
    Args:
        daily_pnl: DataFrame with daily P&L
        initial_value: Starting portfolio value (default: 0)
        
    Returns:
        DataFrame: Equity curve with columns ['Date', 'Equity']
    """
    if daily_pnl is None or len(daily_pnl) == 0:
        return pd.DataFrame(columns=['Date', 'Equity'])
    
    equity = daily_pnl.copy()
    equity['Equity'] = initial_value + equity['PnL'].cumsum()
    
    return equity[['Date', 'Equity']]


def calculate_sharpe_ratio(daily_pnl, risk_free_rate=None):
    """
    Calculate Sharpe ratio (risk-adjusted return).
    
    Args:
        daily_pnl: DataFrame with daily P&L
        risk_free_rate: Risk-free rate (default from config)
        
    Returns:
        float: Sharpe ratio
    """
    if daily_pnl is None or len(daily_pnl) == 0:
        return 0.0
    
    if risk_free_rate is None:
        risk_free_rate = config.RISK_FREE_RATE
    
    returns = daily_pnl['PnL'].values
    
    if len(returns) == 0:
        return 0.0
    
    mean_return = np.mean(returns)
    std_return = np.std(returns)
    
    if std_return == 0:
        return 0.0
    
    # Annualized Sharpe ratio (assuming 252 trading days)
    annualized_return = mean_return * 252
    annualized_std = std_return * np.sqrt(252)
    
    if annualized_std == 0:
        return 0.0
    
    sharpe = (annualized_return - risk_free_rate) / annualized_std
    
    return sharpe


def calculate_max_drawdown(cumulative_pnl):
    """
    Calculate maximum drawdown (peak-to-trough decline).
    
    Args:
        cumulative_pnl: DataFrame with cumulative P&L
        
    Returns:
        float: Maximum drawdown (positive number representing loss)
    """
    if cumulative_pnl is None or len(cumulative_pnl) == 0:
        return 0.0
    
    equity = cumulative_pnl['Cumulative P&L'].values
    
    if len(equity) == 0:
        return 0.0
    
    running_max = np.maximum.accumulate(equity)
    drawdown = running_max - equity
    max_drawdown = np.max(drawdown)
    
    return max_drawdown


def get_win_rate_by_symbol(pnl_data):
    """
    Calculate win rate for each symbol.
    
    Args:
        pnl_data: DataFrame with P&L data
        
    Returns:
        DataFrame: Win rate by symbol
    """
    if pnl_data is None or len(pnl_data) == 0:
        return pd.DataFrame(columns=['Symbol', 'Win Rate %'])
    
    # Each row in P&L represents a stock's overall P&L
    # Win rate by symbol is simply 100% if profitable, 0% if not
    win_rate = pnl_data.copy()
    win_rate['Win Rate %'] = win_rate['Realized P&L'].apply(lambda x: 100.0 if x > 0 else 0.0)
    
    return win_rate[['Symbol', 'Win Rate %']].sort_values('Win Rate %', ascending=False)


def get_avg_holding_period_by_stock(trades):
    """
    Calculate average holding period for each stock (weighted by quantity).
    
    Args:
        trades: DataFrame with tradebook data
        
    Returns:
        DataFrame: Average holding period by stock
    """
    if trades is None or len(trades) == 0:
        return pd.DataFrame(columns=['Symbol', 'Avg Holding Period (Days)'])
    
    holding_periods_by_stock = []
    
    for symbol in trades['Symbol'].unique():
        symbol_trades = trades[trades['Symbol'] == symbol].copy()
        
        # Sort properly for FIFO matching
        if 'Order Execution Time' in symbol_trades.columns:
            symbol_trades['ExecTime'] = pd.to_datetime(
                symbol_trades['Order Execution Time'], 
                errors='coerce'
            )
            symbol_trades = symbol_trades.sort_values(
                ['Trade Date', 'ExecTime', 'Trade ID'],
                na_position='last'
            )
        else:
            symbol_trades = symbol_trades.sort_values(['Trade Date', 'Trade ID'])
        
        periods = match_buy_sell_trades(symbol_trades)
        
        if len(periods) > 0:
            # Calculate weighted average
            total_days = sum(days * qty for days, qty in periods)
            total_quantity = sum(qty for _, qty in periods)
            
            if total_quantity > 0:
                avg_period = total_days / total_quantity
                holding_periods_by_stock.append({
                    'Symbol': symbol,
                    'Avg Holding Period (Days)': avg_period
                })
    
    return pd.DataFrame(holding_periods_by_stock).sort_values('Avg Holding Period (Days)', ascending=False)


def get_trade_duration_distribution(trades):
    """
    Get distribution of trade durations for histogram.
    Returns flat list of days (one entry per quantity unit for proper histogram).
    
    Args:
        trades: DataFrame with tradebook data
        
    Returns:
        list: List of holding periods (days) for histogram
    """
    if trades is None or len(trades) == 0:
        return []
    
    periods = match_buy_sell_trades(trades)
    # Flatten to one entry per quantity unit for histogram
    distribution = []
    for days, qty in periods:
        distribution.extend([days] * int(qty))
    
    return distribution
