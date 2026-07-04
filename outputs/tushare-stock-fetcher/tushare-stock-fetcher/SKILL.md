---
name: tushare-stock-fetcher
description: "Standardized workflow for fetching A-share stock daily data from Tushare Pro MCP, writing it to CSV, and computing forward/backward adjusted prices. Use when the user asks to download or acquire Chinese A-share stock daily data (OHLCV, fundamentals, adjustment factors, trade calendar) from Tushare, or needs price adjustment on raw daily data. Triggers: Tushare, 获取股票数据, 下载日线, A股行情, 复权, 前复权, 后复权, 日线数据."
agent_created: true
---

# Tushare Stock Fetcher

## Overview

Standardized pipeline for fetching A-share Tier-1 core data from Tushare Pro via the MCP connector,
converting JSON results to CSV, and computing forward/backward adjusted OHLCV prices. Covering daily
OHLCV, daily fundamentals (PE/PB/PS/market cap), adjustment factors, and SSE trade calendar.

## Prerequisites

Before fetching, verify the Tushare MCP connector (`tushareMcp`) is connected and has a valid token.
The token is configured in `~/.workbuddy/mcp.json` under `mcpServers.tushareMcp.url`.

Test connectivity by calling `mcp__tushareMcp__stock_basic` with `ts_code` set to the target stock
(e.g., `"601988.SH"`). If a `40101` token error is returned, ask the user for a new Tushare Pro token
from https://tushare.pro/user/token and update `~/.workbuddy/mcp.json`.

## Workflow

### Step 1 — Verify Target Stock

Call `mcp__tushareMcp__stock_basic` with the target `ts_code` to confirm the stock exists and
retrieve its basic info (name, industry, list_date, market).

### Step 2 — Fetch Trade Calendar (optional but recommended)

Call `mcp__tushareMcp__trade_cal` with `exchange="SSE"`, `start_date`, `end_date`, and
`is_open="1"` to get the list of trading days. This provides a reference for date alignment
and counts.

### Step 3 — Fetch Core Data in Parallel

Call the following three Tushare APIs **in parallel** (single batch of DeferExecuteTool calls):

| API | Tool Name | Key Params |
|-----|-----------|------------|
| Daily OHLCV | `mcp__tushareMcp__daily` | `ts_code`, `start_date`, `end_date` |
| Daily Fundamentals | `mcp__tushareMcp__daily_basic` | `ts_code` (required), `start_date`, `end_date` |
| Adjustment Factors | `mcp__tushareMcp__adj_factor` | `ts_code`, `start_date`, `end_date` |

Date range: default to 5 years back from current date, format `YYYYMMDD`.
Example: `start_date="20210704"`, `end_date="20260704"`.

Results exceeding token limits will be saved to temporary files on disk.
Note the directory path of these result files — it will be needed in the next step.

### Step 4 — Parse JSON Results to CSV

Run `scripts/fetch_stock_to_csv.py` to convert the MCP JSON result files into CSVs:

```bash
python scripts/fetch_stock_to_csv.py <result-dir> <out-dir> <prefix>
```

- `result-dir`: Path to the directory containing MCP result `.txt` files
- `out-dir`: Target directory for CSV output (e.g., `data/raw`)
- `prefix`: File prefix for naming (e.g., `boc` produces `boc_daily.csv`, `boc_daily_basic.csv`, etc.)

The script auto-matches files by keyword in filenames (`daily-`, `daily_basic`, `adj_factor`, `trade_cal`).

A Python 3.12+ environment with `json` and `csv` (stdlib) is sufficient — no extra packages needed.
However, prefer using the project's isolated venv for consistency.

### Step 5 — Compute Adjusted Prices

Run `scripts/adjust_daily.py` to compute forward-adjusted (前复权) and backward-adjusted (后复权) prices:

```bash
python scripts/adjust_daily.py <raw-dir> <out-dir> <prefix>
```

- `raw-dir`: Directory containing `{prefix}_daily.csv` and `{prefix}_adj_factor.csv`
- `out-dir`: Output directory for adjusted CSV (e.g., `data/processed`)
- `prefix`: Same prefix used in Step 4

**Adjustment formulas:**

| Type | Formula | Use Case |
|------|---------|----------|
| 前复权 (fwd) | `raw × (adj_factor / latest_adj_factor)` | Charting, technical analysis, backtesting — latest date is the anchor |
| 后复权 (bwd) | `raw × adj_factor` | True cumulative return calculation — base date is the anchor |

The script validates both computations:
- Forward-adjusted latest close must equal raw latest close (by definition)
- Backward-adjusted earliest close must equal raw earliest close × its adj_factor

Output CSV fields: `ts_code, trade_date, fwd_open, fwd_high, fwd_low, fwd_close, fwd_pre_close,
bwd_open, bwd_high, bwd_low, bwd_close, bwd_pre_close, vol, amount, pct_chg, change`.

### Step 6 — Present Results

After CSV generation succeeds, present the files to the user using `present_files`. List all
generated CSVs and provide a summary table with row counts, date ranges, and file sizes.

## Data Files Produced

| File | Content | Fields |
|------|---------|--------|
| `{prefix}_daily.csv` | Raw daily OHLCV | open, high, low, close, pre_close, change, pct_chg, vol, amount |
| `{prefix}_daily_basic.csv` | Daily fundamentals | PE, PE_TTM, PB, PS, turnover_rate, total_mv, circ_mv, dv_ratio |
| `{prefix}_adj_factor.csv` | Cumulative adjustment factors | adj_factor (one per trading day) |
| `{prefix}_trade_cal.csv` | SSE trade calendar | cal_date, is_open, pretrade_date |
| `{prefix}_daily_adj.csv` | Adjusted daily OHLCV | fwd_* + bwd_* for all price fields, plus vol/amount |

## Scripts

- `scripts/fetch_stock_to_csv.py` — Parse MCP JSON results into CSV files. Accepts `<result-dir> <out-dir> <prefix>`.
- `scripts/adjust_daily.py` — Compute forward and backward adjusted prices from raw daily + adj_factor. Accepts `<raw-dir> <out-dir> <prefix>`.

## References

- `references/data_spec.yml` — Full data acquisition specification (9 data domains, 4 tiers, 44 Tushare APIs, quality rules, storage conventions). Reference when the user asks for data beyond Tier 1 (money flow, financial reports, shareholders, H-shares, macro indices).

## Common Issues

- **Token 40101 error**: Token invalid or expired. Ask user to provide a new one from https://tushare.pro/user/token.
- **Results exceed token limit**: Normal for 5-year data. Results are saved to temp files; use the scripts to parse them.
- **Missing adj_factor for some dates**: Skip those rows (logged as "skipped"). This is rare and usually affects < 1% of rows.
- **Bank financial statements**: Use `comp_type=2` parameter when calling `mcp__tushareMcp__income` / `balancesheet` / `cashflow` for bank stocks as specified in `references/data_spec.yml`.
