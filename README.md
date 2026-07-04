# AI-Quant 2

A-share quantitative research workspace. Currently focused on Tushare Pro data acquisition, price adjustment, and technical indicator analysis.

## Project Structure

```
AI-Quant-2/
├── specs/                          # Standardized specifications (YAML, machine-parseable)
│   ├── data_acquisition/
│   │   └── boc_stock_data.spec.yml # Data acquisition spec: 9 domains, 4 tiers, 44 APIs
│   └── analysis/
│       └── technical_indicators.spec.yml  # Technical indicator spec: RSI/MACD/BOLL/ATR/KDJ
├── scripts/                        # Python scripts
│   ├── fetch_boc_to_csv.py         # Tushare JSON -> CSV parser
│   ├── adjust_boc_daily.py         # Forward/backward price adjustment
│   └── gen_ta_notebook.py          # Technical indicator notebook generator
├── notebooks/                      # Jupyter notebooks
│   └── boc_technical_indicators.ipynb  # 5 indicators + visualization + CSV export
├── data/
│   ├── raw/                        # Raw data from Tushare (append-only)
│   └── processed/                  # Processed data (adjusted prices, indicators)
├── outputs/                        # Charts, skill packages
│   ├── boc_*.png                   # Technical indicator charts
│   └── tushare-stock-fetcher.zip   # Packaged reusable skill
└── .workbuddy/                     # (gitignored) WorkBuddy internal data
```

## Data Coverage

- **Securities**: Bank of China (601988.SH), Kweichow Moutai (600519.SH)
- **Time Range**: 2021-07-05 ~ 2026-07-03 (1,211 trading days)
- **Data Domains**: Daily OHLCV, daily fundamentals (PE/PB/PS/MV), adjustment factors, trade calendar

## Technical Indicators

| Indicator | Parameters | Signals |
|-----------|-----------|---------|
| RSI | 6/14/24 periods | Overbought >70, Oversold <30 |
| MACD | 12/26/9 | Golden/death cross, zero-axis |
| BOLL | 20-day, 2 std | Upper/lower band breakout, bandwidth |
| ATR | 14-day | Volatility expansion/contraction |
| KDJ | 9/3/3 | Golden/death cross, J extreme |

## Data Source

[Tushare Pro](https://tushare.pro) via MCP connector.

## Disclaimer

Technical indicators are based on historical price statistics only and do not constitute investment advice. Historical performance does not guarantee future returns.
