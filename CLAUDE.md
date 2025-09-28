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