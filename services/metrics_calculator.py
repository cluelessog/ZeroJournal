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
