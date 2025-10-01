# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Freqtrade cryptocurrency trading bot study project focused on price action strategies. The project includes:
- A main launcher script (`main.py`) that handles configuration and starts trading
- A price action trading strategy (`user_data/strategies/price-act_strategy.py`)
- Configuration files for trading
- Backtesting scripts

## Key Commands

### Running the Trading Bot
```bash
python main.py
```

### Running Backtests
```bash
./run_backtest.sh
```

### Manual Freqtrade Commands
```bash
# Download market data
freqtrade download-data --config user_data/config_price-act_strategy.json --pairs BTC/USDT --timeframe 5m

# Run backtesting
freqtrade backtesting --config user_data/config_price-act_strategy.json --strategy PriceActionStrategy

# Run hyperopt optimization
freqtrade hyperopt --config user_data/config_hyperopt.json --strategy PriceActionStrategy --hyperopt-loss SharpeHyperOptLoss --epochs 50 --timerange 20241001- --spaces buy sell

# Start live trading
freqtrade trade --config user_data/config_price-act_strategy.json --strategy PriceActionStrategy
```

## Project Structure

- `main.py`: Main entry point - handles configuration setup and starts trading
- `run_backtest.sh`: Shell script for automated backtesting with data download
- `user_data/strategies/price-act_strategy.py`: Price action trading strategy implementation
- `user_data/config_price-act_strategy.json`: Trading configuration
- `user_data/data/binance/`: Market data storage
- `pyproject.toml`: Python project configuration

## Architecture

The trading strategy follows a layered architecture:

1. **Layer 0 - K线预处理**: Basic candle properties (bullish/bearish, length, body length)
2. **Layer 1 - 基础判断方法**: Trend judgment and amplitude enhancement tools
3. **Layer 2 - 组合策略**: Breakout and rebound entry strategies
4. **Layer 3 - 出场机制**: Simple time-based exit conditions

The strategy rejects all technical indicators and volume analysis, focusing purely on price action.

## Environment Setup

Required environment variables:
- `BINANCE_API_KEY`: Binance exchange API key
- `BINANCE_API_SECRET`: Binance exchange API secret
- `FREQTRADE_USERNAME`: Optional API server username
- `FREQTRADE_PASSWORD`: Optional API server password
- `JWT_SECRET`: Optional JWT secret for API
- `WS_TOKEN`: Optional WebSocket token

If not provided, the system will auto-generate secure credentials.

## Development Notes

- Uses Python 3.12+ (configured for 3.13+)
- Dependency management via uv/poetry (pyproject.toml)
- Trading pairs: BTC/USDT, ETH/USDT, SOL/USDT, AVAX/USDT, DOGE/USDT, XRP/USDT
- Timeframe: 5 minutes
- Dry run mode enabled by default for testing

## Hyperopt Optimization Analysis (2025-09-30)

### Critical Configuration Issues Identified

**Original Hyperopt Results:**
- Total Return: -0.54% (Poor performance)
- Win Rate: 28.6% (Below target 40%+)
- Trade Count: Only 14 trades (Insufficient for statistical significance)
- Optimized Parameters: trend_analysis_period=24, exit_candle_count=9

**Root Cause Analysis:**
1. **Unrealistic ROI**: `"minimal_roi": {"0": 10}` = 1000% profit target (impossible)
2. **Aggressive Stop Loss**: `-0.15` = 15% stop loss (too high)
3. **Strategy Logic**: Too restrictive conditions generating minimal signals

**Configuration Fixes Applied:**
- Created `user_data/config_hyperopt_fixed.json` with realistic settings:
  - ROI: `{"0": 0.03, "15": 0.02, "30": 0.01, "60": 0}` (3%→2%→1%→0%)
  - Stop Loss: `-0.05` (5% instead of 15%)
  - More trading pairs: Added BNB/USDT, ADA/USDT, DOT/USDT

**Expected Improvements:**
- More trades: 50-200+ instead of 14
- Better win rate: 35-45% target
- Positive returns instead of -0.54%
- Realistic profit targets that trades can actually achieve

### Recommended Hyperopt Command:
```bash
freqtrade hyperopt --config user_data/config_hyperopt_fixed.json --strategy PriceActionStrategy --hyperopt-loss SharpeHyperOptLoss --epochs 50 --timerange 20241001- --spaces buy sell
```