import os
import gzip
import json
import pandas as pd
import yfinance as yf
import ccxt
import matplotlib.pyplot as plt
from datetime import datetime
import warnings
import urllib.request

warnings.filterwarnings("ignore")

DATA_DIR = "bitcoin_5year_data"
os.makedirs(DATA_DIR, exist_ok=True)

YEARS_OF_DATA = 5
DAYS = YEARS_OF_DATA * 365

TOP_EXCHANGES = [
    {"id": "binance", "name": "Binance", "symbol": "BTC/USDT"},
    {"id": "coinbase", "name": "Coinbase", "symbol": "BTC/USD"},
    {"id": "kucoin", "name": "KuCoin", "symbol": "BTC/USDT"},
    {"id": "bybit", "name": "Bybit", "symbol": "BTC/USDT"},
    {"id": "okx", "name": "OKX", "symbol": "BTC/USDT"},
    {"id": "cryptocom", "name": "Crypto.com", "symbol": "BTC/USDT"},
    {"id": "gate", "name": "Gate.io", "symbol": "BTC/USDT"},
    {"id": "bitstamp", "name": "Bitstamp", "symbol": "BTC/USD"},
    {"id": "binanceus", "name": "Binance US", "symbol": "BTC/USDT"},
]


def fetch_ccxt_data(exchange_id, symbol, days):
    try:
        exchange = getattr(ccxt, exchange_id)()
        exchange.enableRateLimit = True
        since = exchange.milliseconds() - (days * 24 * 60 * 60 * 1000)
        ohlcv = exchange.fetch_ohlcv(symbol, "1d", since, limit=days)
        df = pd.DataFrame(
            ohlcv, columns=["Timestamp", "Open", "High", "Low", "Close", "Volume"]
        )
        df["Date"] = pd.to_datetime(df["Timestamp"], unit="ms").dt.strftime("%Y-%m-%d")
        df["Exchange"] = exchange_id.title()
        df = df[["Date", "Open", "High", "Low", "Close", "Volume", "Exchange"]]
        return df
    except:
        return pd.DataFrame()


def fetch_yahoo_data(days):
    print("[1] Fetching Yahoo Finance aggregate data...")
    btc = yf.download("BTC-USD", period=f"{days}d", interval="1d", progress=False)
    if len(btc) == 0:
        return pd.DataFrame()

    if isinstance(btc.columns, pd.MultiIndex):
        btc.columns = btc.columns.get_level_values(0)

    df = btc[["Open", "High", "Low", "Close", "Volume"]].copy()
    df.reset_index(inplace=True)
    df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
    df["Exchange"] = "Yahoo Finance"
    return df[["Date", "Open", "High", "Low", "Close", "Volume", "Exchange"]]


def download_whale_archive():
    """Download whale archive if not present"""
    archive_path = "bitcoin_whale_data/whale-alerts-archive.json.gzip"
    if os.path.exists(archive_path):
        return archive_path

    url = "https://cdn.whale-alert.com/v1/archives/bitcoin.json.gzip"
    try:
        print("   Downloading whale archive (~200MB)...")
        os.makedirs("bitcoin_whale_data", exist_ok=True)
        urllib.request.urlretrieve(url, archive_path)
        return archive_path
    except:
        return None


def process_whale_data():
    print("[2] Processing whale transaction data...")
    archive_path = download_whale_archive()
    if not archive_path or not os.path.exists(archive_path):
        print("   Whale archive not found - skipping")
        return pd.DataFrame()

    whales_list = []
    try:
        with gzip.open(archive_path, "rt", encoding="utf-8") as f:
            data = json.load(f)
    except:
        return pd.DataFrame()

    for w in data:
        if w.get("blockchain") == "bitcoin":
            try:
                amounts = w.get("amounts", [])
                usd_val = 0
                btc_amount = 0
                if isinstance(amounts, list):
                    for a in amounts:
                        if a.get("symbol") == "BTC":
                            btc_amount = float(a.get("amount", 0))
                            usd_val = float(a.get("value_usd", 0))
                            break

                if usd_val >= 1_000_000:
                    whales_list.append(
                        {
                            "Date": pd.to_datetime(
                                w.get("timestamp"), unit="s"
                            ).strftime("%Y-%m-%d"),
                            "Transaction_Hash": w.get("transaction", {}).get(
                                "hash", "N/A"
                            )
                            if isinstance(w.get("transaction"), dict)
                            else "N/A",
                            "From_Wallet": w.get("from", "Unknown"),
                            "To_Wallet": w.get("to", "Unknown"),
                            "BTC_Amount": btc_amount,
                            "USD_Value": usd_val,
                        }
                    )
            except:
                continue

    df = pd.DataFrame(whales_list)
    if len(df) > 0:
        df = df.sort_values("USD_Value", ascending=False)
    return df


def analyze_data(df):
    if len(df) == 0:
        return df

    try:
        close = df["Close"].astype(float)
        vol = df["Volume"].astype(float)

        df = df.copy()
        df["Pct_Change"] = close.pct_change() * 100
        df["Price_Direction"] = df["Pct_Change"].apply(
            lambda x: "UP" if x > 0 else "DOWN" if x < 0 else "FLAT"
        )
        df["Volatility"] = (df["High"].astype(float) - close) / close * 100
        df["MA_7"] = close.rolling(7).mean()
        df["MA_21"] = close.rolling(21).mean()
        df["MA_50"] = close.rolling(50).mean()
        df["MA_200"] = close.rolling(200).mean()

        vol_ma = vol.rolling(7).mean()
        df["Volume_Ratio"] = vol / vol_ma
    except:
        pass

    return df


def save_clean_csvs(yahoo_df, exchange_dfs, whale_df):
    print("[3] Saving clean CSV files...")

    yahoo_csv = os.path.join(DATA_DIR, "yahoo_finance_aggregate.csv")
    yahoo_df.to_csv(yahoo_csv, index=False)
    print(f"   -> yahoo_finance_aggregate.csv")

    if exchange_dfs:
        all_ex = pd.concat(exchange_dfs, ignore_index=True)
        all_ex.to_csv(os.path.join(DATA_DIR, "exchange_specific_data.csv"), index=False)
        print(f"   -> exchange_specific_data.csv")

        summary = []
        for ex in exchange_dfs:
            if len(ex) > 0:
                summary.append(
                    {
                        "Exchange": ex["Exchange"].iloc[0],
                        "Data_Points": len(ex),
                        "Start_Date": ex["Date"].min(),
                        "End_Date": ex["Date"].max(),
                        "Latest_Price": ex["Close"].iloc[-1],
                    }
                )
        if summary:
            pd.DataFrame(summary).to_csv(
                os.path.join(DATA_DIR, "exchange_summary.csv"), index=False
            )
            print(f"   -> exchange_summary.csv")

    if len(whale_df) > 0:
        whale_df.to_csv(os.path.join(DATA_DIR, "bitcoin_whales.csv"), index=False)
        print(f"   -> bitcoin_whales.csv")

        daily = (
            whale_df.groupby("Date")
            .agg({"USD_Value": ["count", "sum"], "BTC_Amount": "sum"})
            .reset_index()
        )
        daily.columns = ["Date", "Whale_Count", "Total_USD", "Total_BTC"]
        daily.to_csv(os.path.join(DATA_DIR, "daily_whale_summary.csv"), index=False)
        print(f"   -> daily_whale_summary.csv")

    if "Pct_Change" in yahoo_df.columns:
        events = yahoo_df[yahoo_df["Pct_Change"].abs() >= 5]
        if len(events) > 0:
            events.to_csv(
                os.path.join(DATA_DIR, "significant_price_events.csv"), index=False
            )
            print(f"   -> significant_price_events.csv")


def create_report(yahoo_df, exchange_dfs, whale_df):
    print("[4] Creating analysis report...")

    report = []
    report.append("=" * 80)
    report.append("BITCOIN 5-YEAR COMPREHENSIVE MARKET ANALYSIS")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Data Range: {YEARS_OF_DATA} years")
    report.append("=" * 80)
    report.append("\n--- DATA SOURCES ---")
    report.append("1. Yahoo Finance (Aggregate baseline - free)")
    report.append("2. Exchange-specific data via CCXT (free public APIs)")
    report.append("3. Whale Alert archive (downloaded if needed)")

    if len(yahoo_df) > 0:
        close_vals = yahoo_df["Close"].astype(float)
        high_vals = yahoo_df["High"].astype(float)

        report.append(f"\n--- YAHOO FINANCE AGGREGATE ---")
        report.append(
            f"   Date Range: {yahoo_df['Date'].min()} to {yahoo_df['Date'].max()}"
        )
        report.append(f"   Total Days: {len(yahoo_df)}")
        report.append(f"   Starting Price: ${close_vals.iloc[0]:,.2f}")
        report.append(f"   Current Price: ${close_vals.iloc[-1]:,.2f}")
        report.append(f"   All-Time High: ${high_vals.max():,.2f}")

    if exchange_dfs:
        report.append(f"\n--- EXCHANGE-SPECIFIC DATA (CCXT) ---")
        for ex in exchange_dfs:
            if len(ex) > 0:
                report.append(
                    f"   {ex['Exchange'].iloc[0]}: {len(ex)} days | Last: ${ex['Close'].iloc[-1]:,.0f}"
                )

    if len(whale_df) > 0:
        report.append(f"\n--- WHALE ACTIVITY ---")
        report.append(f"   Total Transactions: {len(whale_df):,}")
        report.append(f"   Total Value: ${whale_df['USD_Value'].sum():,.0f}")
        report.append(f"   Largest: ${whale_df['USD_Value'].max():,.0f}")

    report.append("\n" + "=" * 80)

    report_text = "\n".join(report)
    with open(os.path.join(DATA_DIR, "analysis_report.txt"), "w") as f:
        f.write(report_text)
    print("   -> analysis_report.txt")
    return report_text


def create_charts(yahoo_df):
    print("[5] Creating charts...")

    fig, axes = plt.subplots(2, 1, figsize=(14, 10))

    dates = pd.to_datetime(yahoo_df["Date"])
    closes = yahoo_df["Close"].astype(float)

    ax1 = axes[0]
    ax1.plot(dates, closes, label="BTC Price", color="#F7931A", linewidth=2)
    if "MA_50" in yahoo_df.columns:
        ax1.plot(
            dates,
            yahoo_df["MA_50"],
            label="MA 50",
            color="orange",
            alpha=0.7,
            linewidth=1,
        )
    if "MA_200" in yahoo_df.columns:
        ax1.plot(
            dates,
            yahoo_df["MA_200"],
            label="MA 200",
            color="red",
            alpha=0.7,
            linewidth=1,
        )
    ax1.set_ylabel("Price (USD)")
    ax1.set_title("Bitcoin 5-Year Price with Moving Averages")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2 = axes[1]
    volumes = yahoo_df["Volume"].astype(float) / 1e9
    ax2.fill_between(dates, volumes, alpha=0.3, color="blue")
    ax2.set_ylabel("Volume (Billions)")
    ax2.set_title("Trading Volume")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(DATA_DIR, "bitcoin_5year_chart.png"), dpi=200)
    plt.close()
    print("   -> bitcoin_5year_chart.png")


def main():
    print("=" * 60)
    print("Satoshi Pulse - Bitcoin Market Analyzer")
    print("=" * 60)
    print(f"Fetching {YEARS_OF_DATA} years of data...\n")

    yahoo_df = fetch_yahoo_data(DAYS)
    print(f"   Yahoo Finance: {len(yahoo_df)} days loaded")

    exchange_dfs = []
    print("\n[1b] Fetching exchange-specific data via CCXT...")
    for i, ex_info in enumerate(TOP_EXCHANGES):
        print(f"   [{i + 1}/{len(TOP_EXCHANGES)}] {ex_info['name']}...", end=" ")
        ex_df = fetch_ccxt_data(ex_info["id"], ex_info["symbol"], DAYS)
        if len(ex_df) > 0:
            exchange_dfs.append(ex_df)
            print(f"OK ({len(ex_df)} days)")
        else:
            print("failed")

    whale_df = process_whale_data()
    print(f"   Whales: {len(whale_df):,} transactions")

    yahoo_df = analyze_data(yahoo_df)
    save_clean_csvs(yahoo_df, exchange_dfs, whale_df)
    report = create_report(yahoo_df, exchange_dfs, whale_df)
    create_charts(yahoo_df)

    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE!")
    print("=" * 60)
    print(f"\nData saved to: {os.path.abspath(DATA_DIR)}")
    print("\nFiles created:")
    print("   - yahoo_finance_aggregate.csv (aggregate baseline)")
    print("   - exchange_specific_data.csv (CCXT real data)")
    print("   - exchange_summary.csv")
    print("   - bitcoin_whales.csv")
    print("   - daily_whale_summary.csv")
    print("   - significant_price_events.csv")
    print("   - analysis_report.txt")
    print("   - bitcoin_5year_chart.png")
    print("\n" + report)


if __name__ == "__main__":
    main()
