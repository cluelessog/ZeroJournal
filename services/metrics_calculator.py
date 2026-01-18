"""
Metrics Calculator Service - Calculates swing trading metrics
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import config
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


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
    Calculate daily P&L by matching individual buy and sell trades per day.
    Uses FIFO matching to calculate actual realized P&L per day.
    
    Args:
        pnl_data: DataFrame with P&L data (used for validation but not primary calculation)
        trades: DataFrame with tradebook data
        
    Returns:
        DataFrame: Daily P&L with columns ['Date', 'PnL']
    """
    if trades is None or len(trades) == 0:
        return pd.DataFrame(columns=['Date', 'PnL'])
    
    daily_pnl_dict = {}
    
    # Group trades by symbol for FIFO matching
    for symbol in trades['Symbol'].unique():
        symbol_trades = trades[trades['Symbol'] == symbol].copy()
        
        # Sort by Trade Date and Order Execution Time for proper FIFO matching
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
        
        # FIFO matching: track buy positions
        buy_queue = []  # List of {date, quantity, price}
        
        for _, trade in symbol_trades.iterrows():
            trade_date = pd.to_datetime(trade['Trade Date']).date()
            quantity = trade['Quantity']
            price = trade['Price']
            
            if pd.isna(trade_date) or pd.isna(quantity) or pd.isna(price):
                continue
            
            if trade['Trade Type'] == 'buy':
                # Add to buy queue
                buy_queue.append({
                    'date': trade_date,
                    'quantity': quantity,
                    'price': price
                })
            
            elif trade['Trade Type'] == 'sell' and len(buy_queue) > 0:
                # Match sell with buys using FIFO
                remaining_sell = quantity
                
                while remaining_sell > 0 and len(buy_queue) > 0:
                    buy = buy_queue[0]
                    
                    # Calculate P&L for this match
                    matched_qty = min(buy['quantity'], remaining_sell)
                    pnl = (price - buy['price']) * matched_qty
                    
                    # Attribute P&L to sell date (when P&L is realized)
                    if trade_date in daily_pnl_dict:
                        daily_pnl_dict[trade_date] += pnl
                    else:
                        daily_pnl_dict[trade_date] = pnl
                    
                    # Update quantities
                    if buy['quantity'] <= remaining_sell:
                        # Entire buy position consumed
                        remaining_sell -= buy['quantity']
                        buy_queue.pop(0)
                    else:
                        # Partial buy position consumed
                        buy['quantity'] -= remaining_sell
                        remaining_sell = 0
    
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


def calculate_daily_turnover(trades):
    """
    Calculate daily turnover (buy value + sell value per day).
    
    Args:
        trades: DataFrame with tradebook data
        
    Returns:
        DataFrame: Daily turnover with columns ['Date', 'Turnover']
    """
    if trades is None or len(trades) == 0:
        return pd.DataFrame(columns=['Date', 'Turnover'])
    
    daily_turnover_dict = {}
    
    for _, trade in trades.iterrows():
        trade_date = pd.to_datetime(trade['Trade Date']).date()
        quantity = trade['Quantity']
        price = trade['Price']
        
        if pd.isna(trade_date) or pd.isna(quantity) or pd.isna(price):
            continue
        
        turnover = quantity * price
        
        if trade_date in daily_turnover_dict:
            daily_turnover_dict[trade_date] += turnover
        else:
            daily_turnover_dict[trade_date] = turnover
    
    # Convert to DataFrame
    daily_turnover_list = [{'Date': pd.to_datetime(date), 'Turnover': turnover} 
                          for date, turnover in daily_turnover_dict.items()]
    
    return pd.DataFrame(daily_turnover_list).sort_values('Date')


def distribute_charges_pro_rata(daily_pnl, trades, total_charges, dp_charges_dict=None):
    """
    Distribute charges pro-rata by daily turnover.
    - Brokerage + taxes: allocated proportionally to daily turnover
    - DP charges: allocated to actual posting dates if provided
    
    Args:
        daily_pnl: DataFrame with daily P&L
        trades: DataFrame with tradebook data (for turnover calculation)
        total_charges: Total charges amount (brokerage + taxes)
        dp_charges_dict: Dict {date: amount} for DP charges on actual dates
        
    Returns:
        DataFrame: Daily P&L with charges subtracted
    """
    if daily_pnl is None or len(daily_pnl) == 0:
        return daily_pnl
    
    daily_pnl = daily_pnl.copy()
    
    # Calculate daily turnover
    daily_turnover = calculate_daily_turnover(trades)
    
    # Merge turnover with daily P&L
    daily_pnl = daily_pnl.merge(daily_turnover, on='Date', how='left')
    daily_pnl['Turnover'] = daily_pnl['Turnover'].fillna(0)
    
    # Allocate brokerage + taxes pro-rata by turnover
    if total_charges > 0:
        total_turnover = daily_pnl['Turnover'].sum()
        
        if total_turnover > 0:
            # Calculate charge per rupee of turnover
            charge_rate = total_charges / total_turnover
            daily_pnl['Charges'] = daily_pnl['Turnover'] * charge_rate
        else:
            # If no turnover, distribute evenly (fallback)
            daily_pnl['Charges'] = total_charges / len(daily_pnl)
    else:
        daily_pnl['Charges'] = 0.0
    
    # Add DP charges on actual dates if provided
    if dp_charges_dict:
        for date, dp_charge in dp_charges_dict.items():
            date_obj = pd.to_datetime(date).date() if isinstance(date, str) else date
            mask = daily_pnl['Date'].dt.date == date_obj
            if mask.any():
                daily_pnl.loc[mask, 'Charges'] += dp_charge
    
    # Subtract total charges from P&L
    daily_pnl['PnL'] = daily_pnl['PnL'] - daily_pnl['Charges']
    
    # Drop turnover and charges columns (keep only Date and PnL)
    return daily_pnl[['Date', 'PnL']]


def distribute_charges_evenly(daily_pnl, total_charges):
    """
    Distribute total charges evenly across all trading days (legacy method).
    Use distribute_charges_pro_rata for more accurate allocation.
    
    Args:
        daily_pnl: DataFrame with daily P&L
        total_charges: Total charges amount to distribute
        
    Returns:
        DataFrame: Daily P&L with charges subtracted
    """
    if daily_pnl is None or len(daily_pnl) == 0:
        return daily_pnl
    
    if total_charges <= 0:
        return daily_pnl
    
    daily_pnl = daily_pnl.copy()
    num_trading_days = len(daily_pnl)
    
    if num_trading_days > 0:
        daily_charge = total_charges / num_trading_days
        daily_pnl['PnL'] = daily_pnl['PnL'] - daily_charge
    
    return daily_pnl


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


def get_win_rate_by_symbol(pnl_data, trades=None):
    """
    Calculate win rate for each symbol based on individual trades.
    
    Args:
        pnl_data: DataFrame with P&L data
        trades: DataFrame with tradebook data (optional, for accurate trade-level win rate)
        
    Returns:
        DataFrame: Win rate by symbol
    """
    if pnl_data is None or len(pnl_data) == 0:
        return pd.DataFrame(columns=['Symbol', 'Win Rate %'])
    
    # If trades data is provided, calculate win rate from individual trade matches
    if trades is not None and len(trades) > 0:
        win_rate_list = []
        
        for symbol in trades['Symbol'].unique():
            symbol_trades = trades[trades['Symbol'] == symbol].copy()
            
            # Get trade matches with P&L for this symbol
            # Sort by Trade Date and Order Execution Time for proper FIFO matching
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
            
            buy_queue = []
            winning_trades = 0
            total_trades = 0
            
            for _, trade in symbol_trades.iterrows():
                trade_date = trade['Trade Date']
                quantity = trade['Quantity']
                price = trade['Price']
                
                if pd.isna(trade_date) or pd.isna(quantity) or pd.isna(price):
                    continue
                
                if trade['Trade Type'] == 'buy':
                    buy_queue.append({'quantity': quantity, 'price': price})
                elif trade['Trade Type'] == 'sell' and len(buy_queue) > 0:
                    remaining_sell = quantity
                    sell_price = price
                    
                    # Accumulate total P&L for this sell transaction
                    total_sell_pnl = 0.0
                    
                    while remaining_sell > 0 and len(buy_queue) > 0:
                        buy = buy_queue[0]
                        matched_qty = min(buy['quantity'], remaining_sell)
                        pnl = (sell_price - buy['price']) * matched_qty
                        
                        # Accumulate P&L for this sell transaction
                        total_sell_pnl += pnl
                        
                        if buy['quantity'] <= remaining_sell:
                            remaining_sell -= buy['quantity']
                            buy_queue.pop(0)
                        else:
                            buy['quantity'] -= matched_qty
                            remaining_sell = 0
                    
                    # Count this entire sell transaction as ONE trade
                    total_trades += 1
                    if total_sell_pnl > 0:
                        winning_trades += 1
            
            if total_trades > 0:
                win_rate_pct = (winning_trades / total_trades) * 100
                win_rate_list.append({
                    'Symbol': symbol,
                    'Win Rate %': win_rate_pct
                })
        
        if len(win_rate_list) > 0:
            return pd.DataFrame(win_rate_list).sort_values('Win Rate %', ascending=False)
    
    # Fallback: Use P&L data (less accurate - just shows if overall symbol P&L is positive)
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
    Returns list of days (one entry per trade match, not per quantity unit).
    
    Args:
        trades: DataFrame with tradebook data
        
    Returns:
        list: List of holding periods (days) for histogram - one entry per trade match
    """
    if trades is None or len(trades) == 0:
        return []
    
    periods = match_buy_sell_trades(trades)
    # Return one entry per trade match (not weighted by quantity)
    # This gives the distribution of trade durations, not quantity-weighted
    distribution = [days for days, _ in periods]
    
    return distribution


def match_trades_with_pnl(trades):
    """
    Match buy and sell trades to calculate holding periods with P&L.
    Uses FIFO (First In First Out) matching.
    Returns list of (holding_days, pnl, quantity) tuples for analysis.
    
    Args:
        trades: DataFrame with tradebook data
        
    Returns:
        list: List of tuples (holding_days, pnl, quantity) for each matched trade
    """
    trade_matches = []  # List of (days, pnl, quantity) tuples
    
    # Group trades by symbol
    for symbol in trades['Symbol'].unique():
        symbol_trades = trades[trades['Symbol'] == symbol].copy()
        
        # Sort by Trade Date and Order Execution Time for proper FIFO matching
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
        
        buy_queue = []  # List of {date, quantity, price}
        
        for _, trade in symbol_trades.iterrows():
            trade_date = trade['Trade Date']
            quantity = trade['Quantity']
            price = trade['Price']
            
            if pd.isna(trade_date) or pd.isna(quantity) or pd.isna(price):
                continue
                
            if trade['Trade Type'] == 'buy':
                # Add buy trade to queue (FIFO)
                buy_queue.append({
                    'date': trade_date,
                    'quantity': quantity,
                    'price': price
                })
            elif trade['Trade Type'] == 'sell' and len(buy_queue) > 0:
                # Match sell with earliest buy (FIFO)
                remaining_sell = quantity
                sell_price = price
                
                while remaining_sell > 0 and len(buy_queue) > 0:
                    buy = buy_queue[0]
                    buy_date = buy['date']
                    buy_price = buy['price']
                    
                    # Calculate holding period in days
                    holding_days = (trade_date - buy_date).days
                    
                    # Ensure holding period is non-negative
                    if holding_days < 0:
                        buy_queue.pop(0)
                        continue
                    
                    if buy['quantity'] <= remaining_sell:
                        # Use entire buy trade
                        matched_qty = buy['quantity']
                        pnl = (sell_price - buy_price) * matched_qty
                        trade_matches.append((holding_days, pnl, matched_qty))
                        remaining_sell -= matched_qty
                        buy_queue.pop(0)
                    else:
                        # Use partial buy trade
                        matched_qty = remaining_sell
                        pnl = (sell_price - buy_price) * matched_qty
                        trade_matches.append((holding_days, pnl, matched_qty))
                        buy['quantity'] -= matched_qty
                        remaining_sell = 0
    
    return trade_matches


def calculate_holding_sentiment(trades):
    """
    Analyze holding period vs profitability by trading style to generate insights.
    Categories: Intraday (0 days), BTST (1 day), Velocity (2-4 days), Swing (>4 days)
    
    Args:
        trades: DataFrame with tradebook data
        
    Returns:
        dict: Sentiment analysis with recommendations by trading style
    """
    if trades is None or len(trades) == 0:
        return {
            'sentiment': 'neutral',
            'intraday': {'count': 0, 'win_rate': 0.0, 'avg_pnl': 0.0},
            'btst': {'count': 0, 'win_rate': 0.0, 'avg_pnl': 0.0},
            'velocity': {'count': 0, 'win_rate': 0.0, 'avg_pnl': 0.0},
            'swing': {'count': 0, 'win_rate': 0.0, 'avg_pnl': 0.0},
            'pure_swing': {'count': 0, 'win_rate': 0.0, 'avg_pnl': 0.0},
            'recommendation': 'Insufficient data for analysis',
            'best_style': None,
            'worst_style': None
        }
    
    # Get matched trades with P&L
    trade_matches = match_trades_with_pnl(trades)
    
    if len(trade_matches) == 0:
        return {
            'sentiment': 'neutral',
            'intraday': {'count': 0, 'win_rate': 0.0, 'avg_pnl': 0.0},
            'btst': {'count': 0, 'win_rate': 0.0, 'avg_pnl': 0.0},
            'velocity': {'count': 0, 'win_rate': 0.0, 'avg_pnl': 0.0},
            'swing': {'count': 0, 'win_rate': 0.0, 'avg_pnl': 0.0},
            'pure_swing': {'count': 0, 'win_rate': 0.0, 'avg_pnl': 0.0},
            'recommendation': 'No completed trades to analyze',
            'best_style': None,
            'worst_style': None
        }
    
    # Categorize trades by trading style
    intraday_trades = [(days, pnl, qty) for days, pnl, qty in trade_matches if days == 0]
    btst_trades = [(days, pnl, qty) for days, pnl, qty in trade_matches if days == 1]
    velocity_trades = [(days, pnl, qty) for days, pnl, qty in trade_matches if 2 <= days <= 4]
    swing_trades = [(days, pnl, qty) for days, pnl, qty in trade_matches if days > 4]
    pure_swing_trades = [(days, pnl, qty) for days, pnl, qty in trade_matches if days > 0]  # All trades > 0 day
    
    # Helper function to calculate metrics
    def calc_metrics(trade_list):
        if len(trade_list) == 0:
            return {'count': 0, 'win_rate': 0.0, 'avg_pnl': 0.0}
        
        wins = sum(1 for _, pnl, _ in trade_list if pnl > 0)
        win_rate = (wins / len(trade_list)) * 100
        avg_pnl = sum(pnl for _, pnl, _ in trade_list) / len(trade_list)
        
        return {
            'count': len(trade_list),
            'win_rate': win_rate,
            'avg_pnl': avg_pnl
        }
    
    # Calculate metrics for each style
    intraday_metrics = calc_metrics(intraday_trades)
    btst_metrics = calc_metrics(btst_trades)
    velocity_metrics = calc_metrics(velocity_trades)
    swing_metrics = calc_metrics(swing_trades)
    
    # Pure Swing is the aggregate of BTST + Velocity + Swing (all >0 day trades)
    # Calculate by combining the three categories
    all_non_intraday = btst_trades + velocity_trades + swing_trades
    pure_swing_metrics = calc_metrics(all_non_intraday)
    
    # Determine best and worst performing styles (only if enough trades)
    styles = []
    if intraday_metrics['count'] >= 3:
        styles.append(('Intraday', intraday_metrics))
    if btst_metrics['count'] >= 3:
        styles.append(('BTST', btst_metrics))
    if velocity_metrics['count'] >= 3:
        styles.append(('Velocity', velocity_metrics))
    if swing_metrics['count'] >= 3:
        styles.append(('Swing', swing_metrics))
    if pure_swing_metrics['count'] >= 3:
        styles.append(('Pure Swing', pure_swing_metrics))
    
    best_style = None
    worst_style = None
    recommendations = []
    
    if len(styles) >= 2:
        # Sort by average P&L
        styles_sorted = sorted(styles, key=lambda x: x[1]['avg_pnl'], reverse=True)
        best_style = styles_sorted[0][0]
        worst_style = styles_sorted[-1][0]
        
        best_metrics = styles_sorted[0][1]
        worst_metrics = styles_sorted[-1][1]
        
        # Generate recommendations
        recommendations.append("📊 **Trading Style Performance Analysis:**\n")
        
        # Best performing style
        if best_metrics['avg_pnl'] > 0:
            recommendations.append(f"✅ **{best_style}** is your most profitable style:")
            recommendations.append(f"   • Trades: {best_metrics['count']}")
            recommendations.append(f"   • Win Rate: {best_metrics['win_rate']:.1f}%")
            recommendations.append(f"   • Avg P&L: ₹{best_metrics['avg_pnl']:.2f}")
            recommendations.append(f"   💡 **Focus more on {best_style} trades**\n")
        
        # Worst performing style
        if worst_metrics['avg_pnl'] < 0:
            recommendations.append(f"⚠️ **{worst_style}** is losing money:")
            recommendations.append(f"   • Trades: {worst_metrics['count']}")
            recommendations.append(f"   • Win Rate: {worst_metrics['win_rate']:.1f}%")
            recommendations.append(f"   • Avg P&L: ₹{worst_metrics['avg_pnl']:.2f}")
            recommendations.append(f"   💡 **Reduce or avoid {worst_style} trades**\n")
        
        # Compare all styles
        recommendations.append("📈 **Profitability Ranking:**")
        for i, (style, metrics) in enumerate(styles_sorted, 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📍"
            recommendations.append(
                f"{emoji} {style}: ₹{metrics['avg_pnl']:.2f} avg | "
                f"{metrics['win_rate']:.1f}% win rate | {metrics['count']} trades"
            )
    else:
        recommendations.append("Need more trades across different holding periods for comprehensive analysis")
    
    recommendation_text = '\n'.join(recommendations) if recommendations else 'Insufficient data for style-based analysis'
    
    return {
        'sentiment': 'analyzed',
        'intraday': intraday_metrics,
        'btst': btst_metrics,
        'velocity': velocity_metrics,
        'swing': swing_metrics,
        'pure_swing': pure_swing_metrics,
        'recommendation': recommendation_text,
        'best_style': best_style,
        'worst_style': worst_style
    }


def calculate_expectancy(trades):
    """
    Calculate expectancy (expected value per trade) for Intraday and Swing separately.
    Expectancy = (Win Rate × Avg Win) - (Loss Rate × Avg Loss)
    
    Args:
        trades: DataFrame with tradebook data
        
    Returns:
        dict: {
            'intraday': {'expectancy': float, 'avg_win': float, 'avg_loss': float},
            'swing': {'expectancy': float, 'avg_win': float, 'avg_loss': float},
            'overall': {'expectancy': float, 'avg_win': float, 'avg_loss': float}
        }
    """
    if trades is None or len(trades) == 0:
        return {
            'intraday': {'expectancy': 0.0, 'avg_win': 0.0, 'avg_loss': 0.0},
            'swing': {'expectancy': 0.0, 'avg_win': 0.0, 'avg_loss': 0.0},
            'overall': {'expectancy': 0.0, 'avg_win': 0.0, 'avg_loss': 0.0}
        }
    
    # Get matched trades with P&L
    trade_matches = match_trades_with_pnl(trades)
    
    if len(trade_matches) == 0:
        return {
            'intraday': {'expectancy': 0.0, 'avg_win': 0.0, 'avg_loss': 0.0},
            'swing': {'expectancy': 0.0, 'avg_win': 0.0, 'avg_loss': 0.0},
            'overall': {'expectancy': 0.0, 'avg_win': 0.0, 'avg_loss': 0.0}
        }
    
    # Separate intraday and swing trades
    intraday_trades = [(days, pnl, qty) for days, pnl, qty in trade_matches if days == 0]
    swing_trades = [(days, pnl, qty) for days, pnl, qty in trade_matches if days > 0]
    
    def calc_expectancy_for_trades(trade_list):
        if len(trade_list) == 0:
            return {'expectancy': 0.0, 'avg_win': 0.0, 'avg_loss': 0.0, 'win_rate': 0.0, 'loss_rate': 0.0}
        
        wins = [pnl for _, pnl, _ in trade_list if pnl > 0]
        losses = [pnl for _, pnl, _ in trade_list if pnl < 0]
        
        total_trades = len(trade_list)
        win_count = len(wins)
        loss_count = len(losses)
        
        win_rate = win_count / total_trades if total_trades > 0 else 0.0
        loss_rate = loss_count / total_trades if total_trades > 0 else 0.0
        
        avg_win = sum(wins) / win_count if win_count > 0 else 0.0
        avg_loss = abs(sum(losses) / loss_count) if loss_count > 0 else 0.0
        
        # Expectancy = (Win Rate × Avg Win) - (Loss Rate × Avg Loss)
        expectancy = (win_rate * avg_win) - (loss_rate * avg_loss)
        
        return {
            'expectancy': expectancy,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'win_rate': win_rate * 100,
            'loss_rate': loss_rate * 100
        }
    
    return {
        'intraday': calc_expectancy_for_trades(intraday_trades),
        'swing': calc_expectancy_for_trades(swing_trades),
        'overall': calc_expectancy_for_trades(trade_matches)
    }


def calculate_risk_reward_ratio(trades):
    """
    Calculate Risk-Reward Ratio (Average Win / Average Loss) for Intraday and Swing separately.
    
    Args:
        trades: DataFrame with tradebook data
        
    Returns:
        dict: {
            'intraday': {'ratio': float, 'avg_win': float, 'avg_loss': float},
            'swing': {'ratio': float, 'avg_win': float, 'avg_loss': float},
            'overall': {'ratio': float, 'avg_win': float, 'avg_loss': float}
        }
    """
    if trades is None or len(trades) == 0:
        return {
            'intraday': {'ratio': 0.0, 'avg_win': 0.0, 'avg_loss': 0.0},
            'swing': {'ratio': 0.0, 'avg_win': 0.0, 'avg_loss': 0.0},
            'overall': {'ratio': 0.0, 'avg_win': 0.0, 'avg_loss': 0.0}
        }
    
    # Get matched trades with P&L
    trade_matches = match_trades_with_pnl(trades)
    
    if len(trade_matches) == 0:
        return {
            'intraday': {'ratio': 0.0, 'avg_win': 0.0, 'avg_loss': 0.0},
            'swing': {'ratio': 0.0, 'avg_win': 0.0, 'avg_loss': 0.0},
            'overall': {'ratio': 0.0, 'avg_win': 0.0, 'avg_loss': 0.0}
        }
    
    # Separate intraday and swing trades
    intraday_trades = [(days, pnl, qty) for days, pnl, qty in trade_matches if days == 0]
    swing_trades = [(days, pnl, qty) for days, pnl, qty in trade_matches if days > 0]
    
    def calc_rr_for_trades(trade_list):
        if len(trade_list) == 0:
            return {'ratio': 0.0, 'avg_win': 0.0, 'avg_loss': 0.0}
        
        wins = [pnl for _, pnl, _ in trade_list if pnl > 0]
        losses = [pnl for _, pnl, _ in trade_list if pnl < 0]
        
        avg_win = sum(wins) / len(wins) if len(wins) > 0 else 0.0
        avg_loss = abs(sum(losses) / len(losses)) if len(losses) > 0 else 0.0
        
        # Risk-Reward Ratio = Avg Win / Avg Loss
        ratio = avg_win / avg_loss if avg_loss > 0 else float('inf') if avg_win > 0 else 0.0
        
        return {
            'ratio': ratio,
            'avg_win': avg_win,
            'avg_loss': avg_loss
        }
    
    return {
        'intraday': calc_rr_for_trades(intraday_trades),
        'swing': calc_rr_for_trades(swing_trades),
        'overall': calc_rr_for_trades(trade_matches)
    }


def calculate_consecutive_streaks(trades):
    """
    Calculate longest consecutive winning and losing streaks for Intraday and Swing separately.
    
    Args:
        trades: DataFrame with tradebook data
        
    Returns:
        dict: {
            'intraday': {'max_win_streak': int, 'max_loss_streak': int, 'current_streak': int, 'current_type': str},
            'swing': {'max_win_streak': int, 'max_loss_streak': int, 'current_streak': int, 'current_type': str},
            'overall': {'max_win_streak': int, 'max_loss_streak': int, 'current_streak': int, 'current_type': str}
        }
    """
    if trades is None or len(trades) == 0:
        return {
            'intraday': {'max_win_streak': 0, 'max_loss_streak': 0, 'current_streak': 0, 'current_type': 'None'},
            'swing': {'max_win_streak': 0, 'max_loss_streak': 0, 'current_streak': 0, 'current_type': 'None'},
            'overall': {'max_win_streak': 0, 'max_loss_streak': 0, 'current_streak': 0, 'current_type': 'None'}
        }
    
    # Get matched trades with P&L
    trade_matches = match_trades_with_pnl(trades)
    
    if len(trade_matches) == 0:
        return {
            'intraday': {'max_win_streak': 0, 'max_loss_streak': 0, 'current_streak': 0, 'current_type': 'None'},
            'swing': {'max_win_streak': 0, 'max_loss_streak': 0, 'current_streak': 0, 'current_type': 'None'},
            'overall': {'max_win_streak': 0, 'max_loss_streak': 0, 'current_streak': 0, 'current_type': 'None'}
        }
    
    # Separate intraday and swing trades
    intraday_trades = [(days, pnl, qty) for days, pnl, qty in trade_matches if days == 0]
    swing_trades = [(days, pnl, qty) for days, pnl, qty in trade_matches if days > 0]
    
    def calc_streaks_for_trades(trade_list):
        if len(trade_list) == 0:
            return {'max_win_streak': 0, 'max_loss_streak': 0, 'current_streak': 0, 'current_type': 'None'}
        
        max_win_streak = 0
        max_loss_streak = 0
        current_streak = 0
        current_type = None
        
        for _, pnl, _ in trade_list:
            if pnl > 0:  # Win
                if current_type == 'win':
                    current_streak += 1
                else:
                    current_streak = 1
                    current_type = 'win'
                max_win_streak = max(max_win_streak, current_streak)
            elif pnl < 0:  # Loss
                if current_type == 'loss':
                    current_streak += 1
                else:
                    current_streak = 1
                    current_type = 'loss'
                max_loss_streak = max(max_loss_streak, current_streak)
            # Ignore breakeven trades (pnl == 0)
        
        # Current streak info
        current_streak_type = current_type.capitalize() if current_type else 'None'
        
        return {
            'max_win_streak': max_win_streak,
            'max_loss_streak': max_loss_streak,
            'current_streak': current_streak,
            'current_type': current_streak_type
        }
    
    return {
        'intraday': calc_streaks_for_trades(intraday_trades),
        'swing': calc_streaks_for_trades(swing_trades),
        'overall': calc_streaks_for_trades(trade_matches)
    }


def calculate_rolling_expectancy(trades, window=20):
    """
    Calculate rolling expectancy over time with a sliding window.
    
    Args:
        trades: DataFrame with tradebook data
        window: Number of trades in rolling window (default 20)
        
    Returns:
        DataFrame with columns: ['trade_number', 'date', 'expectancy_overall', 
                                 'expectancy_intraday', 'expectancy_swing']
    """
    if trades is None or len(trades) == 0:
        return pd.DataFrame(columns=['trade_number', 'date', 'expectancy_overall', 
                                     'expectancy_intraday', 'expectancy_swing'])
    
    # Get matched trades with P&L and dates
    trade_matches = []
    
    # Group trades by symbol to track dates
    for symbol in trades['Symbol'].unique():
        symbol_trades = trades[trades['Symbol'] == symbol].copy()
        
        # Sort by Trade Date and Order Execution Time for proper FIFO matching
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
        
        buy_queue = []
        
        for _, trade in symbol_trades.iterrows():
            trade_date = trade['Trade Date']
            quantity = trade['Quantity']
            price = trade['Price']
            
            if pd.isna(trade_date) or pd.isna(quantity) or pd.isna(price):
                continue
                
            if trade['Trade Type'] == 'buy':
                buy_queue.append({
                    'date': trade_date,
                    'quantity': quantity,
                    'price': price
                })
            elif trade['Trade Type'] == 'sell' and len(buy_queue) > 0:
                remaining_sell = quantity
                sell_price = price
                
                while remaining_sell > 0 and len(buy_queue) > 0:
                    buy = buy_queue[0]
                    buy_date = buy['date']
                    buy_price = buy['price']
                    
                    holding_days = (trade_date - buy_date).days
                    
                    if holding_days < 0:
                        buy_queue.pop(0)
                        continue
                    
                    if buy['quantity'] <= remaining_sell:
                        matched_qty = buy['quantity']
                        pnl = (sell_price - buy_price) * matched_qty
                        trade_matches.append({
                            'date': trade_date,
                            'holding_days': holding_days,
                            'pnl': pnl,
                            'qty': matched_qty
                        })
                        remaining_sell -= matched_qty
                        buy_queue.pop(0)
                    else:
                        matched_qty = remaining_sell
                        pnl = (sell_price - buy_price) * matched_qty
                        trade_matches.append({
                            'date': trade_date,
                            'holding_days': holding_days,
                            'pnl': pnl,
                            'qty': matched_qty
                        })
                        buy['quantity'] -= matched_qty
                        remaining_sell = 0
    
    if len(trade_matches) < window:
        return pd.DataFrame(columns=['trade_number', 'date', 'expectancy_overall', 
                                     'expectancy_intraday', 'expectancy_swing'])
    
    # Sort by date
    trade_matches_df = pd.DataFrame(trade_matches).sort_values('date')
    
    # Calculate rolling expectancy
    rolling_data = []
    
    for i in range(window, len(trade_matches) + 1):
        window_trades = trade_matches[i-window:i]
        
        # Overall expectancy for window
        wins = [t['pnl'] for t in window_trades if t['pnl'] > 0]
        losses = [t['pnl'] for t in window_trades if t['pnl'] < 0]
        
        win_rate = len(wins) / len(window_trades) if len(window_trades) > 0 else 0
        loss_rate = len(losses) / len(window_trades) if len(window_trades) > 0 else 0
        avg_win = sum(wins) / len(wins) if len(wins) > 0 else 0
        avg_loss = abs(sum(losses) / len(losses)) if len(losses) > 0 else 0
        expectancy_overall = (win_rate * avg_win) - (loss_rate * avg_loss)
        
        # Intraday expectancy for window
        intraday_window = [t for t in window_trades if t['holding_days'] == 0]
        if len(intraday_window) > 0:
            wins_id = [t['pnl'] for t in intraday_window if t['pnl'] > 0]
            losses_id = [t['pnl'] for t in intraday_window if t['pnl'] < 0]
            win_rate_id = len(wins_id) / len(intraday_window)
            loss_rate_id = len(losses_id) / len(intraday_window)
            avg_win_id = sum(wins_id) / len(wins_id) if len(wins_id) > 0 else 0
            avg_loss_id = abs(sum(losses_id) / len(losses_id)) if len(losses_id) > 0 else 0
            expectancy_intraday = (win_rate_id * avg_win_id) - (loss_rate_id * avg_loss_id)
        else:
            expectancy_intraday = None
        
        # Swing expectancy for window
        swing_window = [t for t in window_trades if t['holding_days'] > 0]
        if len(swing_window) > 0:
            wins_sw = [t['pnl'] for t in swing_window if t['pnl'] > 0]
            losses_sw = [t['pnl'] for t in swing_window if t['pnl'] < 0]
            win_rate_sw = len(wins_sw) / len(swing_window)
            loss_rate_sw = len(losses_sw) / len(swing_window)
            avg_win_sw = sum(wins_sw) / len(wins_sw) if len(wins_sw) > 0 else 0
            avg_loss_sw = abs(sum(losses_sw) / len(losses_sw)) if len(losses_sw) > 0 else 0
            expectancy_swing = (win_rate_sw * avg_win_sw) - (loss_rate_sw * avg_loss_sw)
        else:
            expectancy_swing = None
        
        rolling_data.append({
            'trade_number': i,
            'date': window_trades[-1]['date'],
            'expectancy_overall': expectancy_overall,
            'expectancy_intraday': expectancy_intraday,
            'expectancy_swing': expectancy_swing
        })
    
    return pd.DataFrame(rolling_data)


def calculate_monthly_expectancy(trades):
    """
    Calculate expectancy grouped by month for Intraday and Swing separately.
    
    Args:
        trades: DataFrame with tradebook data
        
    Returns:
        DataFrame with columns: ['month', 'expectancy_overall', 'expectancy_intraday', 
                                 'expectancy_swing', 'trade_count_overall', 
                                 'trade_count_intraday', 'trade_count_swing']
    """
    if trades is None or len(trades) == 0:
        return pd.DataFrame(columns=['month', 'expectancy_overall', 'expectancy_intraday', 
                                     'expectancy_swing', 'trade_count_overall',
                                     'trade_count_intraday', 'trade_count_swing'])
    
    # Get matched trades with P&L and dates
    trade_matches = []
    
    for symbol in trades['Symbol'].unique():
        symbol_trades = trades[trades['Symbol'] == symbol].copy()
        
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
        
        buy_queue = []
        
        for _, trade in symbol_trades.iterrows():
            trade_date = trade['Trade Date']
            quantity = trade['Quantity']
            price = trade['Price']
            
            if pd.isna(trade_date) or pd.isna(quantity) or pd.isna(price):
                continue
                
            if trade['Trade Type'] == 'buy':
                buy_queue.append({
                    'date': trade_date,
                    'quantity': quantity,
                    'price': price
                })
            elif trade['Trade Type'] == 'sell' and len(buy_queue) > 0:
                remaining_sell = quantity
                sell_price = price
                
                while remaining_sell > 0 and len(buy_queue) > 0:
                    buy = buy_queue[0]
                    buy_date = buy['date']
                    buy_price = buy['price']
                    
                    holding_days = (trade_date - buy_date).days
                    
                    if holding_days < 0:
                        buy_queue.pop(0)
                        continue
                    
                    if buy['quantity'] <= remaining_sell:
                        matched_qty = buy['quantity']
                        pnl = (sell_price - buy_price) * matched_qty
                        trade_matches.append({
                            'date': trade_date,
                            'month': trade_date.to_period('M'),
                            'holding_days': holding_days,
                            'pnl': pnl
                        })
                        remaining_sell -= matched_qty
                        buy_queue.pop(0)
                    else:
                        matched_qty = remaining_sell
                        pnl = (sell_price - buy_price) * matched_qty
                        trade_matches.append({
                            'date': trade_date,
                            'month': trade_date.to_period('M'),
                            'holding_days': holding_days,
                            'pnl': pnl
                        })
                        buy['quantity'] -= matched_qty
                        remaining_sell = 0
    
    if len(trade_matches) == 0:
        return pd.DataFrame(columns=['month', 'expectancy_overall', 'expectancy_intraday', 
                                     'expectancy_swing', 'trade_count_overall',
                                     'trade_count_intraday', 'trade_count_swing'])
    
    # Group by month
    df = pd.DataFrame(trade_matches)
    monthly_data = []
    
    for month in df['month'].unique():
        month_trades = df[df['month'] == month]
        
        # Overall
        wins = month_trades[month_trades['pnl'] > 0]['pnl']
        losses = month_trades[month_trades['pnl'] < 0]['pnl']
        win_rate = len(wins) / len(month_trades)
        loss_rate = len(losses) / len(month_trades)
        avg_win = wins.mean() if len(wins) > 0 else 0
        avg_loss = abs(losses.mean()) if len(losses) > 0 else 0
        expectancy_overall = (win_rate * avg_win) - (loss_rate * avg_loss)
        
        # Intraday
        intraday = month_trades[month_trades['holding_days'] == 0]
        if len(intraday) > 0:
            wins_id = intraday[intraday['pnl'] > 0]['pnl']
            losses_id = intraday[intraday['pnl'] < 0]['pnl']
            win_rate_id = len(wins_id) / len(intraday)
            loss_rate_id = len(losses_id) / len(intraday)
            avg_win_id = wins_id.mean() if len(wins_id) > 0 else 0
            avg_loss_id = abs(losses_id.mean()) if len(losses_id) > 0 else 0
            expectancy_intraday = (win_rate_id * avg_win_id) - (loss_rate_id * avg_loss_id)
            count_intraday = len(intraday)
        else:
            expectancy_intraday = None
            count_intraday = 0
        
        # Swing
        swing = month_trades[month_trades['holding_days'] > 0]
        if len(swing) > 0:
            wins_sw = swing[swing['pnl'] > 0]['pnl']
            losses_sw = swing[swing['pnl'] < 0]['pnl']
            win_rate_sw = len(wins_sw) / len(swing)
            loss_rate_sw = len(losses_sw) / len(swing)
            avg_win_sw = wins_sw.mean() if len(wins_sw) > 0 else 0
            avg_loss_sw = abs(losses_sw.mean()) if len(losses_sw) > 0 else 0
            expectancy_swing = (win_rate_sw * avg_win_sw) - (loss_rate_sw * avg_loss_sw)
            count_swing = len(swing)
        else:
            expectancy_swing = None
            count_swing = 0
        
        monthly_data.append({
            'month': month.to_timestamp(),
            'expectancy_overall': expectancy_overall,
            'expectancy_intraday': expectancy_intraday,
            'expectancy_swing': expectancy_swing,
            'trade_count_overall': len(month_trades),
            'trade_count_intraday': count_intraday,
            'trade_count_swing': count_swing
        })
    
    result = pd.DataFrame(monthly_data).sort_values('month')
    return result


def calculate_cumulative_metrics(trades):
    """
    Calculate cumulative metrics as trades accumulate over time.
    Shows evolution of win rate, profit factor, risk-reward, and expectancy.
    
    Args:
        trades: DataFrame with tradebook data
        
    Returns:
        DataFrame with columns: ['trade_number', 'date', 'win_rate', 'profit_factor', 
                                 'risk_reward', 'expectancy']
    """
    if trades is None or len(trades) == 0:
        return pd.DataFrame(columns=['trade_number', 'date', 'win_rate', 'profit_factor',
                                     'risk_reward', 'expectancy'])
    
    # Get matched trades with P&L
    trade_matches = match_trades_with_pnl(trades)
    
    if len(trade_matches) == 0:
        return pd.DataFrame(columns=['trade_number', 'date', 'win_rate', 'profit_factor',
                                     'risk_reward', 'expectancy'])
    
    cumulative_data = []
    
    for i in range(1, len(trade_matches) + 1):
        subset = trade_matches[:i]
        
        # Win Rate
        wins = [pnl for _, pnl, _ in subset if pnl > 0]
        losses = [pnl for _, pnl, _ in subset if pnl < 0]
        win_rate = (len(wins) / i) * 100
        
        # Profit Factor
        gross_profit = sum(wins) if len(wins) > 0 else 0
        gross_loss = abs(sum(losses)) if len(losses) > 0 else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else (float('inf') if gross_profit > 0 else 0)
        
        # Risk-Reward Ratio
        avg_win = sum(wins) / len(wins) if len(wins) > 0 else 0
        avg_loss = abs(sum(losses) / len(losses)) if len(losses) > 0 else 0
        risk_reward = avg_win / avg_loss if avg_loss > 0 else (float('inf') if avg_win > 0 else 0)
        
        # Expectancy
        win_rate_decimal = len(wins) / i
        loss_rate_decimal = len(losses) / i
        expectancy = (win_rate_decimal * avg_win) - (loss_rate_decimal * avg_loss)
        
        cumulative_data.append({
            'trade_number': i,
            'win_rate': win_rate,
            'profit_factor': profit_factor if profit_factor != float('inf') else None,
            'risk_reward': risk_reward if risk_reward != float('inf') else None,
            'expectancy': expectancy
        })
    
    return pd.DataFrame(cumulative_data)


def calculate_mae_mfe_for_trades(trades, progress_callback=None, fetch_function=None):
    """
    Calculate MAE (Maximum Adverse Excursion) and MFE (Maximum Favorable Excursion) 
    for all completed trades using NSE historical data.
    
    MAE: How far the price went AGAINST you during the trade
    MFE: How far the price went IN YOUR FAVOR during the trade
    
    Args:
        trades: DataFrame with tradebook data
        progress_callback: Optional function(progress, message) to report progress
        fetch_function: Optional cached fetch function (for optimization)
        
    Returns:
        DataFrame with columns: ['Symbol', 'Entry Date', 'Exit Date', 'Entry Price', 
                                 'Exit Price', 'Lowest Price', 'Highest Price', 
                                 'MAE %', 'MFE %', 'Exit P&L %', 'Exit Efficiency %', 
                                 'Holding Days', 'Data Source']
    """
    import time
    from datetime import timedelta
    if trades is None or len(trades) == 0:
        return pd.DataFrame()
    
    # Initialize openchart instance once (reuse for all symbols)
    openchart_nse = None
    try:
        from openchart import NSEData
        if progress_callback:
            progress_callback(5, "Initializing openchart...")
        openchart_nse = NSEData()
        print("openchart initialized successfully")
    except Exception as e:
        print(f"openchart not available: {e}")
        return pd.DataFrame()
    
    # Helper function to fetch historical data (with caching support)
    def fetch_hist_data(symbol, start_date, end_date, interval):
        """Fetch historical data, using cached function if provided"""
        if fetch_function:
            # Use cached function from Streamlit
            symbol_variants = [
                f"{symbol}-EQ",
                symbol,
                symbol.upper(),
                symbol.replace(' ', ''),
            ]
            for chart_symbol in symbol_variants:
                try:
                    hist_data = fetch_function(chart_symbol, start_date, end_date, interval)
                    if not hist_data.empty and 'Open' in hist_data.columns and 'High' in hist_data.columns:
                        return hist_data, chart_symbol
                except:
                    continue
            return pd.DataFrame(), None
        else:
            # Direct fetch without cache
            symbol_variants = [
                f"{symbol}-EQ",
                symbol,
                symbol.upper(),
                symbol.replace(' ', ''),
            ]
            for chart_symbol in symbol_variants:
                try:
                    hist_data = openchart_nse.historical(
                        symbol=chart_symbol,
                        segment='EQ',
                        start=start_date,
                        end=end_date + timedelta(days=1),
                        interval=interval
                    )
                    if not hist_data.empty:
                        hist_data.columns = [col.title() for col in hist_data.columns]
                        if 'Open' in hist_data.columns and 'High' in hist_data.columns:
                            return hist_data, chart_symbol
                except:
                    continue
            return pd.DataFrame(), None
    
    # Step 1: Collect all trade pairs using FIFO matching
    if progress_callback:
        progress_callback(10, "Matching buy-sell pairs...")
    
    trade_pairs = []  # List of (buy_trade, sell_trade, symbol) tuples
    unique_symbols = trades['Symbol'].unique()
    
    for symbol in unique_symbols:
        symbol_trades = trades[trades['Symbol'] == symbol].copy()
        
        # Sort by date and execution time
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
        
        buy_queue = []
        for idx, trade_row in symbol_trades.iterrows():
            trade = trade_row.to_dict()
            if trade.get('Trade Type') == 'buy':
                buy_queue.append(trade)
            elif trade.get('Trade Type') == 'sell' and len(buy_queue) > 0:
                buy_trade = buy_queue.pop(0)
                trade_pairs.append((buy_trade, trade, symbol))
    
    total_pairs = len(trade_pairs)
    if total_pairs == 0:
        return pd.DataFrame()
    
    if progress_callback:
        progress_callback(15, f"Found {total_pairs} trade pairs. Preparing parallel fetch...")
    
    # Step 2: Prepare fetch requests
    fetch_requests = []
    for buy_trade, sell_trade, symbol in trade_pairs:
        start_date = pd.to_datetime(buy_trade.get('Trade Date'))
        end_date = pd.to_datetime(sell_trade.get('Trade Date'))
        holding_days = (end_date - start_date).days
        interval = '5m' if holding_days == 0 else '1d'
        
        fetch_requests.append({
            'symbol': symbol,
            'start_date': start_date,
            'end_date': end_date,
            'interval': interval,
            'buy_trade': buy_trade,
            'sell_trade': sell_trade,
            'holding_days': holding_days
        })
    
    # Step 3: Parallel fetch using ThreadPoolExecutor (Optimization 3: Batch Requests)
    def fetch_single_request(request):
        """Fetch data for a single request"""
        try:
            hist_data, used_symbol = fetch_hist_data(
                request['symbol'],
                request['start_date'],
                request['end_date'],
                request['interval']
            )
            return {
                'request': request,
                'hist_data': hist_data,
                'used_symbol': used_symbol,
                'success': not hist_data.empty
            }
        except Exception as e:
            return {
                'request': request,
                'hist_data': pd.DataFrame(),
                'used_symbol': None,
                'success': False,
                'error': str(e)
            }
    
    mae_mfe_results = []
    completed_fetches = 0
    
    if progress_callback:
        progress_callback(20, f"Fetching data for {total_pairs} trades in parallel...")
    
    # Use ThreadPoolExecutor with max 10 workers (NSE can handle ~10 concurrent)
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all fetch requests
        future_to_request = {
            executor.submit(fetch_single_request, req): req 
            for req in fetch_requests
        }
        
        # Process completed fetches as they come in
        for future in as_completed(future_to_request):
            completed_fetches += 1
            result = future.result()
            request = result['request']
            
            # Update progress
            if progress_callback and total_pairs > 0:
                fetch_progress = 20 + int((completed_fetches / total_pairs) * 70)
                progress_callback(
                    fetch_progress, 
                    f"Fetched {completed_fetches}/{total_pairs} trades..."
                )
            
            if not result['success']:
                continue
            
            hist_data = result['hist_data']
            buy_trade = request['buy_trade']
            sell_trade = request['sell_trade']
            symbol = request['symbol']
            holding_days = request['holding_days']
            
            try:
                buy_price = buy_trade.get('Price', 0)
                sell_price = sell_trade.get('Price', 0)
                
                if buy_price == 0 or sell_price == 0:
                    continue
                
                # Ensure we have required columns
                required_cols = ['Low', 'High']
                if not all(col in hist_data.columns for col in required_cols):
                    continue
                
                lowest_price = hist_data['Low'].min()
                highest_price = hist_data['High'].max()
                
                if pd.isna(lowest_price) or pd.isna(highest_price):
                    continue
                
                # Calculate MAE and MFE
                mae = buy_price - lowest_price
                mfe = highest_price - buy_price
                
                mae_pct = (mae / buy_price) * 100
                mfe_pct = (mfe / buy_price) * 100
                
                exit_pnl = sell_price - buy_price
                exit_pnl_pct = (exit_pnl / buy_price) * 100
                
                exit_efficiency = (exit_pnl / mfe * 100) if (mfe > 0 and exit_pnl > 0) else 0
                
                start_date = request['start_date']
                end_date = request['end_date']
                
                mae_mfe_results.append({
                    'Symbol': symbol,
                    'Entry Date': start_date.date() if hasattr(start_date, 'date') else start_date,
                    'Exit Date': end_date.date() if hasattr(end_date, 'date') else end_date,
                    'Entry Price': buy_price,
                    'Exit Price': sell_price,
                    'Lowest Price': lowest_price,
                    'Highest Price': highest_price,
                    'MAE %': mae_pct,
                    'MFE %': mfe_pct,
                    'Exit P&L %': exit_pnl_pct,
                    'Exit Efficiency %': exit_efficiency,
                    'Holding Days': holding_days,
                    'Data Source': 'openchart'
                })
            except Exception as e:
                print(f"Error processing {symbol} trade: {e}")
                continue
    
    result_df = pd.DataFrame(mae_mfe_results)
    
    # Debug: Print summary
    if len(result_df) == 0:
        print(f"Warning: No MAE/MFE data calculated. Processed {len(trades)} trades.")
        print(f"Unique symbols: {list(trades['Symbol'].unique()[:10])}")  # Show first 10 symbols
        
        # Count buy/sell pairs
        buy_count = len(trades[trades['Trade Type'].str.lower() == 'buy'])
        sell_count = len(trades[trades['Trade Type'].str.lower() == 'sell'])
        print(f"Buy trades: {buy_count}, Sell trades: {sell_count}")
        
        # Check if we have matched pairs
        matched_pairs = 0
        for symbol in trades['Symbol'].unique():
            symbol_trades = trades[trades['Symbol'] == symbol]
            buys = symbol_trades[symbol_trades['Trade Type'].str.lower() == 'buy']
            sells = symbol_trades[symbol_trades['Trade Type'].str.lower() == 'sell']
            matched_pairs += min(len(buys), len(sells))
        print(f"Potential matched pairs: {matched_pairs}")
    
    return result_df
