import yfinance as yf
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.optimize import minimize

# App Title
st.title("Portfolio Risk Management System")

# Stocks Dictionary (Example with 4 sectors)
stocks_dict = {
    "Technology": ["AAPL", "MSFT", "GOOGL", "NVDA", "AMD"],
    "Healthcare": ["JNJ", "PFE", "MRK", "UNH", "ABT"],
    "Energy": ["XOM", "CVX", "BP", "SLB", "COP"],
    "Financials": ["JPM", "BAC", "WFC", "GS", "MS"]
}

# Multi-select sectors
selected_sectors = st.multiselect(
    "Select Sectors to Include in Your Portfolio",
    stocks_dict.keys(),
    default=list(stocks_dict.keys())
)

# Create a list of stocks based on selected sectors
final_stocks = []
for sector in selected_sectors:
    final_stocks.extend(stocks_dict[sector])

# Allow users to select specific stocks
selected_stocks = st.multiselect(
    "Select Stocks to Add to Your Portfolio",
    final_stocks,
    default=final_stocks
)

# Fetch historical data for selected stocks
if selected_stocks:
    st.write("### Fetching Historical Data...")
    data = yf.download(selected_stocks, start="2015-01-01", end="2024-12-27")["Adj Close"]
    
    # Display historical prices
    st.write("### Historical Prices of Selected Stocks")
    st.line_chart(data)

    # Calculate daily returns
    returns = data.pct_change().dropna()

    # Portfolio Weights input
    weights_input = st.text_input(
        "Enter weights for selected stocks (comma-separated, e.g., 0.4,0.3,0.3):"
    )

    if weights_input:
        try:
            weights = list(map(float, weights_input.split(',')))
            if len(weights) != len(selected_stocks):
                st.error("Number of weights must match the number of selected stocks.")
            elif sum(weights) != 1.0:
                st.error("Weights must sum to 1.")
            else:
                # Portfolio Metrics Calculation
                expected_returns = returns.mean() * 252
                cov_matrix = returns.cov() * 252
                portfolio_volatility = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
                portfolio_return = np.dot(weights, expected_returns)

                # Risk-Free Rate
                risk_free_rate = 0.03

                # Sharpe Ratio
                sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_volatility

                # Value-at-Risk (VaR)
                portfolio_returns = np.dot(returns, weights)
                VaR_95 = np.percentile(portfolio_returns, 5)

                # Sortino Ratio (downside risk)
                downside_returns = portfolio_returns[portfolio_returns < 0]
                downside_volatility = np.std(downside_returns) * np.sqrt(252)
                sortino_ratio = (portfolio_return - risk_free_rate) / downside_volatility

                # Benchmark Comparison
                benchmark_symbol = st.text_input("Enter Benchmark Symbol (e.g., ^GSPC for (S&P 500) or ^IXIC for (NASDAQ) or ^DJI for (Dow Jones).):", "^GSPC")

                if benchmark_symbol:
                    try:
                        st.write("Fetching benchmark data...")
                        benchmark_data = yf.download(benchmark_symbol, start="2015-01-01", end="2024-12-01")["Adj Close"]

                        if benchmark_data.empty:
                            st.warning("Benchmark data could not be fetched. Please check the symbol.")
                        else:
                            # Ensure alignment of dates
                            benchmark_returns = benchmark_data.pct_change().dropna()
                            aligned_returns = pd.concat([returns, benchmark_returns], axis=1, join='inner')
                            aligned_returns.columns = list(returns.columns) + ['Benchmark']

                            # Calculate metrics
                            portfolio_returns = np.dot(aligned_returns.iloc[:, :-1], weights)
                            benchmark_returns = aligned_returns['Benchmark']

                            # Calculate Beta
                            beta = np.cov(portfolio_returns, benchmark_returns)[0, 1] / np.var(benchmark_returns)

                            # Treynor Ratio
                            treynor_ratio = (portfolio_return - risk_free_rate) / beta

                            # Convert portfolio returns to a Pandas Series
                            portfolio_returns_series = pd.Series(portfolio_returns, index=aligned_returns.index, name='Portfolio')
                    
                            # Align portfolio and benchmark returns by their index (date)
                            aligned_data = pd.concat([portfolio_returns_series, benchmark_returns], axis=1)
                            aligned_data.columns = ['Portfolio', 'Benchmark']


                            # Calculate cumulative returns
                            aligned_data['Portfolio_Cum_Returns'] = (1 + aligned_data['Portfolio']).cumprod()
                            aligned_data['Benchmark_Cum_Returns'] = (1 + aligned_data['Benchmark']).cumprod()

                            # Plot cumulative returns
                            st.write("### Portfolio vs Benchmark Cumulative Returns ")
                            plt.figure(figsize=(12, 8))
                            plt.plot(aligned_data.index, aligned_data['Portfolio_Cum_Returns'], label="Portfolio", color='#1f77b4', linewidth=2.5)
                            plt.plot(aligned_data.index, aligned_data['Benchmark_Cum_Returns'], label=f"{benchmark_symbol}", color='#ff7f0e', linestyle='--', linewidth=2.5)
                            plt.title("Portfolio vs Benchmark Cumulative Returns", fontsize=16, fontweight='bold')
                            plt.xlabel("Date", fontsize=14, fontweight='bold')
                            plt.ylabel("Cumulative Return", fontsize=14, fontweight='bold')
                            plt.xticks(fontsize=12)
                            plt.yticks(fontsize=12)
                            plt.legend(fontsize=12, loc='upper left', frameon=True, shadow=True, fancybox=True, borderpad=1)
                            plt.grid(visible=True, linestyle='--', alpha=0.6)
                            plt.tight_layout()
                            st.pyplot(plt)

                            # Display risk metrics
                            st.write(f"### Portfolio Beta: {beta:.2f}")
                            st.write(f"### Treynor Ratio: {treynor_ratio:.2f}")

                    except Exception as e:
                        st.error(f"Error fetching benchmark data: {e}")

                # Display Portfolio Metrics
                st.write(f"### Portfolio Expected Annual Return: {portfolio_return:.2%}")
                st.write(f"### Portfolio Volatility (Risk): {portfolio_volatility:.2%}")
                st.write(f"### Sharpe Ratio: {sharpe_ratio:.2f}")
                st.write(f"### Sortino Ratio: {sortino_ratio:.2f}")
                st.write(f"### Value-at-Risk (VaR) at 95% Confidence: {VaR_95:.2%}")

                # Correlation Matrix
                st.write("### Correlation Matrix of Selected Stocks")
                corr_matrix = returns.corr()
                fig, ax = plt.subplots(figsize=(10, 8))
                sns.heatmap(corr_matrix, annot=True, cmap="coolwarm", ax=ax)
                st.pyplot(fig)

                # Sector-wise Allocation Pie Chart
            if weights_input:
                sector_allocation = {}
                for sector in selected_sectors:
                    sector_allocation[sector] = sum(
                        weights[i] for i, stock in enumerate(selected_stocks) if stock in stocks_dict[sector]
                    )
                fig, ax = plt.subplots()
                ax.pie(
                    sector_allocation.values(),
                    labels=sector_allocation.keys(),
                    autopct='%1.1f%%',
                    startangle=90,
                    colors=sns.color_palette("pastel"),
                )
                ax.set_title("Sector-wise Portfolio Allocation", fontweight='bold', fontsize=16)
                st.pyplot(fig)
                # Top/Bottom Performers in Portfolio
                st.write("### Top/Bottom Performers in Portfolio")
                
                # Calculate cumulative returns for each stock
                cumulative_returns = (1 + returns).cumprod().iloc[-1] - 1
                
                # Sort stocks by cumulative returns
                sorted_returns = cumulative_returns.sort_values(ascending=False)
                
                # Display top 3 performers
                st.write("#### Top 3 Performers")
                top_performers = sorted_returns.head(3)
                st.table(top_performers.apply(lambda x: f"{x:.2%}"))
                
                # Display bottom 3 performers
                st.write("#### Bottom 3 Performers")
                bottom_performers = sorted_returns.tail(3)
                st.table(bottom_performers.apply(lambda x: f"{x:.2%}"))
                
               
            
            # Volatility Trends Over Time
            st.write("### Rolling Volatility (30-Day)")
            rolling_volatility = returns.rolling(window=30).std() * np.sqrt(252)
            st.line_chart(rolling_volatility)
            
            


        except ValueError:
            st.error("Please enter valid numeric weights separated by commas.")
else:
    st.write("Select stocks to build your portfolio.")
