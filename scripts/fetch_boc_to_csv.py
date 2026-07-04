#!/usr/bin/env python3
"""
中国银行 A 股数据 — 从 MCP 结果解析并写入 CSV
按照 spec: specs/data_acquisition/boc_stock_data.spec.yml Tier 1 核心数据域
"""
import json
import csv
import os
import sys
from pathlib import Path

RESULT_DIR = os.path.join(
    os.path.expanduser("~/.workbuddy/projects"),
    "c-Users-Admin-Desktop-AI-Quant 2",
    "c9bea588-79fc-43c1-87d9-fd11275f07a2",
    "tool-results"
)
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw")

FILES = {
    "boc_daily":         "mcp-connector-proxy-tushareMcp_daily-1783132494271-cbbf93.txt",
    "boc_daily_basic":   "mcp-connector-proxy-tushareMcp_daily_basic-1783132494377-05052f.txt",
    "boc_adj_factor":    "mcp-connector-proxy-tushareMcp_adj_factor-1783132494173-b51b34.txt",
    "sse_trade_cal":     "mcp-connector-proxy-tushareMcp_trade_cal-1783132494086-f4ed87.txt",
}

os.makedirs(OUT_DIR, exist_ok=True)

stats = {}

for name, fname in FILES.items():
    fpath = os.path.join(RESULT_DIR, fname)
    if not os.path.exists(fpath):
        print(f"[SKIP] {name}: file not found at {fpath}")
        continue

    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not data:
        print(f"[EMPTY] {name}")
        stats[name] = 0
        continue

    rows = data if isinstance(data, list) else data.get("items", [])
    out_path = os.path.join(OUT_DIR, f"{name}.csv")

    with open(out_path, "w", newline="", encoding="utf-8-sig") as fout:
        writer = csv.DictWriter(fout, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    n = len(rows)
    stats[name] = n
    date_min = rows[-1].get("trade_date") or rows[-1].get("cal_date")
    date_max = rows[0].get("trade_date") or rows[0].get("cal_date")
    print(f"[OK] {name} -> {out_path}  ({n} rows, {date_min} ~ {date_max})")

print("\n=== 汇总 ===")
total = sum(stats.values())
for k, v in stats.items():
    print(f"  {k}: {v} 条")
print(f"  合计: {total} 条")
print(f"  输出目录: {OUT_DIR}")
