# Bitcoin Market Analyzer - Developer Guide

## Project Overview

This project analyzes Bitcoin market data using free public APIs. No subscription or API keys required.

## Setup

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/bitcoin_market_analyzer.git
cd bitcoin_market_analyzer

# Install dependencies
pip install pandas yfinance matplotlib ccxt requests
```

## Running the Analyzer

```bash
python bitcoin_exchange_analyzer.py
```

This will:
1. Fetch 5 years of Yahoo Finance data
2. Fetch exchange-specific data via CCXT (free public APIs)
3. Process whale transaction data
4. Generate clean CSV files and charts

## Data Output

All output goes to `bitcoin_5year_data/` directory.

## Adding New Exchanges

To add more exchanges, edit `TOP_EXCHANGES` list in `bitcoin_exchange_analyzer.py`:

```python
TOP_EXCHANGES = [
    {"id": "exchange_name", "name": "Display Name", "symbol": "BTC/USDT"},
]
```

CCXT exchange IDs: https://docs.ccxt.com/#/ccxt-master?id=exchange-ids

## Updating Data Range

Change `YEARS_OF_DATA` in the script:

```python
YEARS_OF_DATA = 5  # 5 years
```

## Troubleshooting

### Rate Limited
- CCXT has built-in rate limiting
- Wait and retry

### Missing Data
- Some exchanges have shorter history
- Check exchange documentation

## Architecture

- `bitcoin_exchange_analyzer.py` - Main script
- Uses yfinance for Yahoo data
- Uses ccxt for exchange data
- Processes whale archive locally

## For Collaborators

1. Clone the repo
2. Install requirements
3. Run the script
4. Check `bitcoin_5year_data/` for output

## Notes

- Whale archive (`whale-alerts-archive.json.gzip`) is ~200MB - first run takes time
- Reuses downloaded data on subsequent runs
- All data sources are free and public