# Satoshi Pulse - Bitcoin Market Analyzer

Advanced Bitcoin market analysis tool using real exchange data via CCXT and aggregated Yahoo Finance data.

## What It Does

- Fetches 5 years of Bitcoin price data from Yahoo Finance (aggregate baseline)
- Fetches real exchange-specific data from 9+ exchanges via CCXT (free public APIs)
- Downloads whale transaction data automatically (if not present)
- Generates clean, AI-readable CSV files and charts

## Data Sources (All Free - No API Keys Needed)

| Source | Type | Coverage |
|--------|------|---------|
| Yahoo Finance | Aggregate | 1825 days |
| Binance | Real exchange | 1000 days |
| KuCoin | Real exchange | 1500 days |
| Bybit | Real exchange | 1000 days |
| Bitstamp | Real exchange | 1000 days |
| Gate.io | Real exchange | 999 days |
| Coinbase | Real exchange | 300 days |
| OKX | Real exchange | 300 days |
| Crypto.com | Real exchange | 300 days |

## Quick Start (Fresh Windows Machine)

### 1. Install Python

Download from: https://www.python.org/downloads/

**Or via PowerShell (admin):**
```powershell
winget install Python.Python.3.12
```

### 2. Install Dependencies

Open terminal/command prompt in this folder:
```powershell
pip install pandas yfinance matplotlib ccxt requests
```

### 3. Run the Analyzer

```powershell
python bitcoin_exchange_analyzer.py
```

## Output Files

Generated in `bitcoin_5year_data/`:

```
bitcoin_5year_data/
├── yahoo_finance_aggregate.csv    # Aggregate baseline
├── exchange_specific_data.csv # CCXT real data
├── exchange_summary.csv      # Exchange stats
├── bitcoin_whales.csv     # Whale transactions
├── daily_whale_summary.csv
├── significant_price_events.csv
├── analysis_report.txt
└── bitcoin_5year_chart.png
```

## Project Structure

```
Satoshi-Pulse/
├── bitcoin_exchange_analyzer.py  # Main script
├── README.md                  # This file
├── AGENTS.md                 # Developer guide
├── .gitignore
└── bitcoin_5year_data/      # Generated on run
```

## Requirements

- Python 3.8+
- pandas
- yfinance
- matplotlib
- ccxt
- requests

Install all: `pip install pandas yfinance matplotlib ccxt requests`

## Troubleshooting

### "gh is not recognized"
GitHub CLI not installed. Download from: https://cli.github.com/

### Rate Limited
CCXT has built-in rate limiting. Wait a few minutes and retry.

### Whale Archive Download Fails
The whale archive (~200MB) downloads automatically. If it fails, manually download from:
https://cdn.whale-alert.com/v1/archives/bitcoin.json.gzip
Save to: `bitcoin_whale_data/whale-alerts-archive.json.gzip`

## For Collaborators

1. Clone the repo:
```bash
git clone https://github.com/Aeell/Satoshi-Pulse.git
cd Satoshi-Pulse
```

2. Install requirements:
```bash
pip install pandas yfinance matplotlib ccxt requests
```

3. Run:
```bash
python bitcoin_exchange_analyzer.py
```

4. Check `bitcoin_5year_data/` for output files

## License

MIT - Free to use and modify.