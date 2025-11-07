"""Streamlit web UI for Wheel Strategy Simulator"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import sys; import os; sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..")); from wheel_simulator.core.simulator import WheelSimulator
from wheel_simulator.models.position import PositionStatus
from wheel_simulator import config

# Page configuration
st.set_page_config(
    page_title="Wheel Strategy Simulator",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .big-font {
        font-size: 24px !important;
        font-weight: bold;
    }
    .metric-positive {
        color: #00CC00;
    }
    .metric-negative {
        color: #CC0000;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'simulator' not in st.session_state:
    st.session_state.simulator = None
    st.session_state.initialized = False
    st.session_state.recent_transactions = []

def initialize_simulator():
    """Initialize the simulator"""
    with st.spinner("Loading historical data... This may take a minute..."):
        sim = WheelSimulator()
        sim.initialize()
        st.session_state.simulator = sim
        st.session_state.initialized = True
        st.success("✓ Simulator initialized!")

def format_currency(value):
    """Format value as currency"""
    if pd.isna(value) or not isinstance(value, (int, float)):
        return "$0.00"
    return f"${value:,.2f}"

def format_percent(value):
    """Format value as percentage"""
    if pd.isna(value) or not isinstance(value, (int, float)):
        return "0.00%"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.2f}%"

def display_portfolio_metrics():
    """Display portfolio metrics in the sidebar"""
    sim = st.session_state.simulator
    current_prices = sim.get_current_prices()
    total_value = sim.portfolio.get_total_value(current_prices)
    total_return = (total_value - sim.portfolio.initial_capital) / sim.portfolio.initial_capital * 100
    total_premium = sim.portfolio.get_total_premium_collected()
    
    st.sidebar.markdown("### 💰 Portfolio")
    
    col1, col2 = st.sidebar.columns(2)
    col1.metric("Cash", format_currency(sim.portfolio.cash))
    col2.metric("Total Value", format_currency(total_value))
    
    col3, col4 = st.sidebar.columns(2)
    col3.metric("Return", format_percent(total_return))
    col4.metric("Premium", format_currency(total_premium))
    
    # Stock positions summary in sidebar
    if sim.portfolio.stock_positions:
        st.sidebar.markdown("### 📈 Stock Holdings")
        for symbol, pos in sim.portfolio.stock_positions.items():
            current_price = current_prices.get(symbol, 0)
            pnl = pos.unrealized_pnl(current_price)
            pnl_pct = (pnl / pos.total_cost()) * 100 if pos.total_cost() > 0 else 0
            
            with st.sidebar.expander(f"**{symbol}** - {pos.shares} shares"):
                st.write(f"**Cost Basis:** ${pos.cost_basis:.2f}")
                st.write(f"**Current Price:** ${current_price:.2f}")
                st.write(f"**Total Value:** ${pos.current_value(current_price):,.2f}")
                
                if pnl >= 0:
                    st.success(f"**P&L:** +${pnl:,.2f} ({pnl_pct:+.1f}%)")
                else:
                    st.error(f"**P&L:** -${abs(pnl):,.2f} ({pnl_pct:.1f}%)")
                
                st.caption(f"Acquired: {pos.acquisition_date.strftime('%Y-%m-%d')}")
                if pos.assigned_from_put:
                    st.caption("📌 From put assignment")
    
    # Options positions summary in sidebar
    if sim.portfolio.options_positions:
        st.sidebar.markdown("### 📋 Open Options")
        for pos in sim.portfolio.options_positions:
            dte = pos.days_to_expiration(sim.current_date)
            option_symbol = f"{pos.symbol} ${pos.strike:.0f} {pos.option_type.upper()}"
            
            with st.sidebar.expander(f"**{option_symbol}**"):
                st.write(f"**Contracts:** {pos.contracts}")
                st.write(f"**Premium:** ${pos.premium_received:.2f}/share")
                st.write(f"**Total Premium:** ${pos.total_premium():.2f}")
                st.write(f"**Expiration:** {pos.expiration.strftime('%Y-%m-%d')}")
                
                if dte <= 7:
                    st.warning(f"**⏰ {dte} days left**")
                else:
                    st.info(f"**DTE:** {dte} days")
                
                st.caption(f"Entry: {pos.entry_date.strftime('%Y-%m-%d')} @ ${pos.stock_price_at_entry:.2f}")
    
    # Date info
    st.sidebar.markdown("### 📅 Date")
    st.sidebar.write(f"**Current:** {sim.current_date.strftime('%Y-%m-%d')}")
    st.sidebar.write(f"**Day:** {sim.current_date_index + 1} / {len(sim.trading_dates)}")

def display_recent_transactions():
    """Display recent transaction history"""
    if not st.session_state.recent_transactions:
        return
    
    st.markdown("### 📝 Recent Activity")
    
    # Show last 5 transactions
    for txn in reversed(st.session_state.recent_transactions[-5:]):
        if txn['type'] == 'put_sold':
            st.success(f"""
            **✅ SOLD PUT** - {txn['date']}
            - **{txn['contracts']} {txn['symbol']} ${txn['strike']:.2f}** put contract(s)
            - **Premium collected:** ${txn['premium']:.2f} per share = **${txn['total_premium']:.2f} total**
            - **Stock price:** ${txn['stock_price']:.2f}
            - **Expiration:** {txn['expiration']} ({txn['dte']} days)
            - **Cash secured:** ${txn['cash_secured']:,.2f}
            """)
        elif txn['type'] == 'call_sold':
            st.success(f"""
            **✅ SOLD CALL** - {txn['date']}
            - **{txn['contracts']} {txn['symbol']} ${txn['strike']:.2f}** call contract(s)
            - **Premium collected:** ${txn['premium']:.2f} per share = **${txn['total_premium']:.2f} total**
            - **Stock price:** ${txn['stock_price']:.2f}
            - **Expiration:** {txn['expiration']} ({txn['dte']} days)
            """)
        elif txn['type'] == 'put_assigned':
            st.warning(f"""
            **⚠️ PUT ASSIGNED** - {txn['date']}
            - **Bought {txn['shares']} shares of {txn['symbol']}**
            - **Cost basis:** ${txn['strike']:.2f} per share
            - **Total cost:** ${txn['total_cost']:,.2f}
            - **Stock price at assignment:** ${txn['stock_price']:.2f}
            """)
        elif txn['type'] == 'call_assigned':
            st.info(f"""
            **📤 CALL ASSIGNED** - {txn['date']}
            - **Sold {txn['shares']} shares of {txn['symbol']}**
            - **Sale price:** ${txn['strike']:.2f} per share
            - **Total proceeds:** ${txn['total_proceeds']:,.2f}
            - **Stock price at assignment:** ${txn['stock_price']:.2f}
            """)
        elif txn['type'] == 'expired_worthless':
            st.success(f"""
            **🎉 EXPIRED WORTHLESS** - {txn['date']}
            - **{txn['symbol']} ${txn['strike']:.2f} {txn['option_type']} expired worthless**
            - **You kept the premium:** ${txn['premium_kept']:.2f}
            - **Stock price at expiration:** ${txn['stock_price']:.2f}
            """)
    
    if st.button("Clear History"):
        st.session_state.recent_transactions = []
        st.rerun()

def plot_portfolio_performance():
    """Plot portfolio performance over time"""
    sim = st.session_state.simulator
    
    # Build a timeline of portfolio values
    dates = []
    values = []
    
    # Add starting point
    dates.append(sim.trading_dates[0])
    values.append(sim.portfolio.initial_capital)
    
    # Sample portfolio value at regular intervals (every 5 trading days)
    for i in range(5, sim.current_date_index + 1, 5):
        date = sim.trading_dates[i]
        dates.append(date)
        
        # Calculate value at that point - need to get prices for that date
        total = sim.portfolio.cash
        for symbol, pos in sim.portfolio.stock_positions.items():
            price = sim.data_fetcher.get_price_at_date(symbol, date)
            total += pos.shares * price
        values.append(total)
    
    # Always add current value
    if sim.current_date not in dates:
        dates.append(sim.current_date)
        current_prices = sim.get_current_prices()
        values.append(sim.portfolio.get_total_value(current_prices))
    
    # Create figure
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=values,
        mode='lines+markers',
        name='Portfolio Value',
        line=dict(color='#1f77b4', width=2),
        fill='tozeroy',
        fillcolor='rgba(31, 119, 180, 0.1)'
    ))
    
    # Add initial capital line
    fig.add_hline(
        y=sim.portfolio.initial_capital,
        line_dash="dash",
        line_color="gray",
        annotation_text="Initial Capital"
    )
    
    # Calculate and show current return
    current_value = values[-1]
    total_return = ((current_value - sim.portfolio.initial_capital) / sim.portfolio.initial_capital * 100)
    
    fig.update_layout(
        title=f"Portfolio Performance (Return: {total_return:+.2f}%)",
        xaxis_title="Date",
        yaxis_title="Value ($)",
        hovermode='x unified',
        height=400
    )
    
    return fig

def plot_stock_price_history(symbol: str, sim: WheelSimulator, show_full_history: bool = False):
    """Plot stock price history with trade markers"""
    
    # Get stock data
    df = sim.data_fetcher.get_data(symbol)
    if df.empty:
        return None
    
    # Filter to show only up to current date
    df_filtered = df[df.index <= sim.current_date]
    
    # If not showing full history, show last 90 days
    if not show_full_history and len(df_filtered) > 90:
        df_filtered = df_filtered.tail(90)
    
    # Create figure
    fig = go.Figure()
    
    # Add stock price line
    fig.add_trace(go.Scatter(
        x=df_filtered.index,
        y=df_filtered['Close'],
        mode='lines',
        name=f'{symbol} Price',
        line=dict(color='#2E86AB', width=2),
        hovertemplate='%{x|%Y-%m-%d}<br>Price: $%{y:.2f}<extra></extra>'
    ))
    
    # Add markers for put sales
    put_entries = []
    put_dates = []
    put_strikes = []
    for pos in sim.portfolio.options_positions + sim.portfolio.closed_positions:
        if pos.symbol == symbol and pos.option_type == 'put':
            put_entries.append(pos.stock_price_at_entry)
            put_dates.append(pos.entry_date)
            put_strikes.append(pos.strike)
    
    if put_entries:
        fig.add_trace(go.Scatter(
            x=put_dates,
            y=put_entries,
            mode='markers',
            name='Put Sold',
            marker=dict(color='#A23B72', size=12, symbol='triangle-down'),
            hovertemplate='Put Sold<br>%{x|%Y-%m-%d}<br>Stock: $%{y:.2f}<extra></extra>'
        ))
        
        # Add strike lines for puts
        for date, strike in zip(put_dates, put_strikes):
            fig.add_hline(
                y=strike,
                line_dash="dot",
                line_color="#A23B72",
                opacity=0.3,
                annotation_text=f"Put Strike ${strike:.0f}",
                annotation_position="right"
            )
    
    # Add markers for call sales
    call_entries = []
    call_dates = []
    call_strikes = []
    for pos in sim.portfolio.options_positions + sim.portfolio.closed_positions:
        if pos.symbol == symbol and pos.option_type == 'call':
            call_entries.append(pos.stock_price_at_entry)
            call_dates.append(pos.entry_date)
            call_strikes.append(pos.strike)
    
    if call_entries:
        fig.add_trace(go.Scatter(
            x=call_dates,
            y=call_entries,
            mode='markers',
            name='Call Sold',
            marker=dict(color='#F18F01', size=12, symbol='triangle-up'),
            hovertemplate='Call Sold<br>%{x|%Y-%m-%d}<br>Stock: $%{y:.2f}<extra></extra>'
        ))
        
        # Add strike lines for calls
        for date, strike in zip(call_dates, call_strikes):
            fig.add_hline(
                y=strike,
                line_dash="dot",
                line_color="#F18F01",
                opacity=0.3,
                annotation_text=f"Call Strike ${strike:.0f}",
                annotation_position="right"
            )
    
    # Add markers for stock acquisitions
    stock_pos = sim.portfolio.stock_positions.get(symbol)
    if stock_pos:
        fig.add_trace(go.Scatter(
            x=[stock_pos.acquisition_date],
            y=[stock_pos.cost_basis],
            mode='markers',
            name='Stock Acquired',
            marker=dict(color='#06A77D', size=15, symbol='star'),
            hovertemplate='Stock Acquired<br>%{x|%Y-%m-%d}<br>Cost: $%{y:.2f}<extra></extra>'
        ))
    
    # Add current date marker
    current_price = sim.data_fetcher.get_price_at_date(symbol, sim.current_date)
    fig.add_trace(go.Scatter(
        x=[sim.current_date],
        y=[current_price],
        mode='markers',
        name='Current',
        marker=dict(color='red', size=10, symbol='diamond'),
        hovertemplate='Current<br>%{x|%Y-%m-%d}<br>Price: $%{y:.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"{symbol} Price History with Trade Markers",
        xaxis_title="Date",
        yaxis_title="Price ($)",
        hovermode='x unified',
        height=450,
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )
    
    return fig

def display_market_overview():
    """Display market overview table"""
    sim = st.session_state.simulator
    
    st.header("📊 Market Overview")
    
    market_data = []
    for symbol in config.STOCKS:
        price = sim.data_fetcher.get_price_at_date(symbol, sim.current_date)
        vol = sim.data_fetcher.calculate_historical_volatility(symbol, sim.current_date)
        
        # Check positions
        has_stock = symbol in sim.portfolio.stock_positions
        has_option = any(pos.symbol == symbol for pos in sim.portfolio.options_positions)
        
        status = []
        if has_stock:
            status.append("Stock")
        if has_option:
            opt_types = [pos.option_type.upper() for pos in sim.portfolio.options_positions if pos.symbol == symbol]
            status.extend(opt_types)
        
        market_data.append({
            'Symbol': symbol,
            'Price': price,
            'IV (30d)': f"{vol:.1%}",
            'Position': ", ".join(status) if status else "-"
        })
    
    df = pd.DataFrame(market_data)
    df['Price'] = df['Price'].apply(lambda x: f"${x:.2f}")
    
    st.dataframe(df, use_container_width=True, hide_index=True)

def display_stock_positions():
    """Display stock positions"""
    sim = st.session_state.simulator
    
    if not sim.portfolio.stock_positions:
        st.info("No stock positions")
        return
    
    current_prices = sim.get_current_prices()
    
    stock_data = []
    for symbol, pos in sim.portfolio.stock_positions.items():
        current_price = current_prices.get(symbol, 0)
        pnl = pos.unrealized_pnl(current_price)
        pnl_pct = (pnl / pos.total_cost()) * 100 if pos.total_cost() > 0 else 0
        
        stock_data.append({
            'Symbol': symbol,
            'Shares': pos.shares,
            'Cost Basis': f"${pos.cost_basis:.2f}",
            'Current Price': f"${current_price:.2f}",
            'Total Value': f"${pos.current_value(current_price):,.2f}",
            'P&L': f"${pnl:+,.2f}",
            'P&L %': f"{pnl_pct:+.1f}%"
        })
    
    df = pd.DataFrame(stock_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

def display_options_positions():
    """Display options positions"""
    sim = st.session_state.simulator
    
    if not sim.portfolio.options_positions:
        st.info("No open options positions")
        return
    
    options_data = []
    for pos in sim.portfolio.options_positions:
        dte = pos.days_to_expiration(sim.current_date)
        
        options_data.append({
            'Symbol': pos.symbol,
            'Type': pos.option_type.upper(),
            'Strike': f"${pos.strike:.2f}",
            'Contracts': pos.contracts,
            'Premium/Contract': f"${pos.premium_received:.2f}",
            'Total Premium': f"${pos.total_premium():.2f}",
            'Expiration': pos.expiration.strftime('%Y-%m-%d'),
            'DTE': f"{dte} days"
        })
    
    df = pd.DataFrame(options_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

def display_closed_positions():
    """Display recently closed positions"""
    sim = st.session_state.simulator
    
    if not sim.portfolio.closed_positions:
        st.info("No closed positions yet")
        return
    
    # Show last 10 closed positions
    recent = sim.portfolio.closed_positions[-10:]
    
    closed_data = []
    for pos in reversed(recent):
        closed_data.append({
            'Symbol': pos.symbol,
            'Type': pos.option_type.upper(),
            'Strike': f"${pos.strike:.2f}",
            'Contracts': pos.contracts,
            'Premium': f"${pos.total_premium():.2f}",
            'Status': pos.status.value.replace('_', ' ').title(),
            'Entry': pos.entry_date.strftime('%Y-%m-%d'),
            'Exit': pos.exit_date.strftime('%Y-%m-%d') if pos.exit_date else '-'
        })
    
    df = pd.DataFrame(closed_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

def sell_put_interface():
    """Interface for selling puts"""
    st.subheader("Sell Cash-Secured Put")
    sim = st.session_state.simulator
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        symbol = st.selectbox("Stock", config.STOCKS, key="put_symbol")
    
    with col2:
        dte = st.selectbox("Days to Expiration", config.DAYS_TO_EXPIRATION, key="put_dte")
    
    with col3:
        contracts = st.number_input("Contracts", min_value=1, max_value=10, value=1, key="put_contracts")
    
    if symbol:
        current_price = sim.data_fetcher.get_price_at_date(symbol, sim.current_date)
        vol = sim.data_fetcher.calculate_historical_volatility(symbol, sim.current_date)
        
        st.write(f"**Current Price:** ${current_price:.2f} | **IV:** {vol:.1%}")
        
        # Show option chain
        chain = sim.get_option_chain(symbol, dte, num_strikes=7)
        
        # Only show puts
        put_chain = chain[['Strike', 'Put Premium', 'Put Premium (%)']].copy()
        put_chain.columns = ['Strike', 'Premium', 'Premium (%)']
        
        st.dataframe(put_chain, use_container_width=True, hide_index=True)
        
        # Strike selection
        col1, col2 = st.columns(2)
        with col1:
            default_strike = round(current_price * 0.95 * 2) / 2  # Round to nearest 0.50
            strike = st.number_input("Strike Price", min_value=0.0, value=float(default_strike), step=0.50, key=f"put_strike_{symbol}")
        
        with col2:
            required_cash = strike * contracts * 100
            st.metric("Required Cash", format_currency(required_cash))
        
        if st.button("Sell Put", type="primary", key="sell_put_btn"):
            if sim.sell_put_option(symbol, strike, dte, contracts):
                # Record transaction
                from datetime import timedelta
                premium_per_share = chain[chain['Strike'] == strike]['Put Premium'].values[0] if len(chain[chain['Strike'] == strike]) > 0 else 0
                expiration_date = sim.current_date + timedelta(days=dte)
                
                st.session_state.recent_transactions.append({
                    'type': 'put_sold',
                    'date': sim.current_date.strftime('%Y-%m-%d'),
                    'symbol': symbol,
                    'strike': strike,
                    'contracts': contracts,
                    'premium': premium_per_share,
                    'total_premium': premium_per_share * contracts * 100,
                    'stock_price': current_price,
                    'dte': dte,
                    'expiration': expiration_date.strftime('%Y-%m-%d'),
                    'cash_secured': strike * contracts * 100
                })
                st.rerun()
            else:
                st.error("Failed to sell put - check available cash")

def sell_call_interface():
    """Interface for selling calls"""
    st.subheader("Sell Covered Call")
    sim = st.session_state.simulator
    
    if not sim.portfolio.stock_positions:
        st.warning("⚠️ No stock positions available for covered calls!")
        return
    
    available_stocks = list(sim.portfolio.stock_positions.keys())
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        symbol = st.selectbox("Stock", available_stocks, key="call_symbol")
    
    with col2:
        dte = st.selectbox("Days to Expiration", config.DAYS_TO_EXPIRATION, key="call_dte")
    
    stock_pos = sim.portfolio.stock_positions[symbol]
    max_contracts = stock_pos.shares // 100
    
    with col3:
        contracts = st.number_input("Contracts", min_value=1, max_value=max_contracts, value=1, key="call_contracts")
    
    if symbol:
        current_price = sim.data_fetcher.get_price_at_date(symbol, sim.current_date)
        vol = sim.data_fetcher.calculate_historical_volatility(symbol, sim.current_date)
        
        st.write(f"**Current Price:** ${current_price:.2f} | **Cost Basis:** ${stock_pos.cost_basis:.2f} | **IV:** {vol:.1%}")
        st.write(f"**Available:** {stock_pos.shares} shares ({max_contracts} contracts)")
        
        # Show option chain
        chain = sim.get_option_chain(symbol, dte, num_strikes=7)
        
        # Only show calls
        call_chain = chain[['Strike', 'Call Premium', 'Call Premium (%)']].copy()
        call_chain.columns = ['Strike', 'Premium', 'Premium (%)']
        
        st.dataframe(call_chain, use_container_width=True, hide_index=True)
        
        # Strike selection
        default_strike = round(current_price * 1.05 * 2) / 2  # Round to nearest 0.50
        strike = st.number_input("Strike Price", min_value=0.0, value=float(default_strike), step=0.50, key=f"call_strike_{symbol}")
        
        if st.button("Sell Call", type="primary", key="sell_call_btn"):
            if sim.sell_call_option(symbol, strike, dte, contracts):
                # Record transaction
                from datetime import timedelta
                premium_per_share = chain[chain['Strike'] == strike]['Call Premium'].values[0] if len(chain[chain['Strike'] == strike]) > 0 else 0
                expiration_date = sim.current_date + timedelta(days=dte)
                
                st.session_state.recent_transactions.append({
                    'type': 'call_sold',
                    'date': sim.current_date.strftime('%Y-%m-%d'),
                    'symbol': symbol,
                    'strike': strike,
                    'contracts': contracts,
                    'premium': premium_per_share,
                    'total_premium': premium_per_share * contracts * 100,
                    'stock_price': current_price,
                    'dte': dte,
                    'expiration': expiration_date.strftime('%Y-%m-%d')
                })
                st.rerun()
            else:
                st.error("Failed to sell call - check available shares")

def main():
    """Main application"""
    # Title and info box
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.title("🎯 Wheel Strategy Training Simulator")
    
    with col2:
        st.info("""
        **IV (30d) = Implied Volatility**
        
        Measures expected price movement over 30 days.
        
        • **Higher IV** = More premium, more risk
        • **Lower IV** = Less premium, more stable
        
        *Example: 25% IV means ±25% annual price swing*
        """)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Control Panel")
        
        if not st.session_state.initialized:
            if st.button("🚀 Initialize Simulator", type="primary"):
                initialize_simulator()
                st.rerun()
        else:
            display_portfolio_metrics()
            
            st.markdown("---")
            st.markdown("### ⏰ Time Control")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("▶️ +1 Day"):
                    success, events = st.session_state.simulator.advance_day(1)
                    for event in events:
                        event['date'] = st.session_state.simulator.current_date.strftime('%Y-%m-%d')
                        st.session_state.recent_transactions.append(event)
                    st.rerun()
            with col2:
                if st.button("⏩ +7 Days"):
                    success, all_events = True, []
                    for _ in range(7):
                        success, events = st.session_state.simulator.advance_day(1)
                        all_events.extend(events)
                        if not success:
                            break
                    for event in all_events:
                        event['date'] = st.session_state.simulator.current_date.strftime('%Y-%m-%d')
                        st.session_state.recent_transactions.append(event)
                    st.rerun()
            
            if st.button("⏭️ +30 Days"):
                success, all_events = True, []
                for _ in range(30):
                    success, events = st.session_state.simulator.advance_day(1)
                    all_events.extend(events)
                    if not success:
                        break
                for event in all_events:
                    event['date'] = st.session_state.simulator.current_date.strftime('%Y-%m-%d')
                    st.session_state.recent_transactions.append(event)
                st.rerun()
            
            st.markdown("**Custom:**")
            custom_days = st.number_input("Days", min_value=1, max_value=365, value=45, key="custom_days")
            if st.button(f"⏩ +{custom_days} Days", type="secondary"):
                success, all_events = True, []
                for _ in range(custom_days):
                    success, events = st.session_state.simulator.advance_day(1)
                    all_events.extend(events)
                    if not success:
                        break
                for event in all_events:
                    event['date'] = st.session_state.simulator.current_date.strftime('%Y-%m-%d')
                    st.session_state.recent_transactions.append(event)
                st.rerun()
            
            st.markdown("---")
            if st.button("🔄 Reset Simulator"):
                st.session_state.simulator = None
                st.session_state.initialized = False
                st.rerun()
    
    # Main content
    if not st.session_state.initialized:
        st.info("👈 Click 'Initialize Simulator' in the sidebar to start")
        
        st.markdown("### 📚 About the Wheel Strategy")
        st.markdown("""
        The wheel strategy is a systematic options trading approach:
        
        1. **Sell Cash-Secured Puts** - Collect premium on stocks you want to own
        2. **Get Assigned** - Buy the stock if the put expires in-the-money
        3. **Sell Covered Calls** - Generate income from your stock position
        4. **Repeat** - Continue the cycle to build income over time
        
        **Stocks Available:** AAPL, MSFT, JNJ, KO, XOM, V, GOOG, AXP, WMT, PG
        
        **Historical Data:** 18 months of real market data
        
        **Options Pricing:** Black-Scholes model with historical volatility
        """)
        
    else:
        sim = st.session_state.simulator
        
        # Recent transactions at the top
        display_recent_transactions()
        
        # Performance chart
        st.plotly_chart(plot_portfolio_performance(), use_container_width=True)
        
        # Tabs for different views
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Market", "📈 Stocks", "📋 Options", "✅ Closed", "💼 Trade"
        ])
        
        with tab1:
            display_market_overview()
        
        with tab2:
            st.header("📈 Stock Positions")
            display_stock_positions()
        
        with tab3:
            st.header("📋 Open Options Positions")
            display_options_positions()
        
        with tab4:
            st.header("✅ Recently Closed Positions")
            display_closed_positions()
        
        with tab5:
            st.header("💼 Trade Options")
            
            trade_type = st.radio("Select Trade Type", ["Sell Put", "Sell Call"], horizontal=True)
            
            st.markdown("---")
            
            if trade_type == "Sell Put":
                sell_put_interface()
            else:
                sell_call_interface()
        
        # Stock price charts section
        st.markdown("---")
        st.header("📈 Stock Price Charts")
        
        # Create tabs for stocks with activity
        active_symbols = set()
        
        # Add stocks we own
        for symbol in sim.portfolio.stock_positions.keys():
            active_symbols.add(symbol)
        
        # Add stocks with open options
        for pos in sim.portfolio.options_positions:
            active_symbols.add(pos.symbol)
        
        # Add stocks with closed positions
        for pos in sim.portfolio.closed_positions[-10:]:  # Last 10 closed
            active_symbols.add(pos.symbol)
        
        if active_symbols:
            chart_symbol = st.selectbox("Select stock to view", sorted(active_symbols))
            
            col1, col2 = st.columns([3, 1])
            with col2:
                show_full = st.checkbox("Show full history", value=False)
            
            if chart_symbol:
                fig = plot_stock_price_history(chart_symbol, sim, show_full)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No active positions yet. Make a trade to see stock price charts!")

if __name__ == "__main__":
    main()
