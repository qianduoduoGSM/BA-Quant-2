#!/usr/bin/env python3
"""
从 MCP 结果文件 (JSON) 解析并写入 CSV。
用法: python fetch_stock_to_csv.py <result-dir> <out-dir> <prefix>

result-dir: MCP 工具结果落盘的目录 (含 mcp-connector-proxy-tushareMcp_*.txt)
out-dir:     CSV 输出目录
prefix:      文件前缀 (如 "boc" → boc_daily.csv, boc_daily_basic.csv 等)

自动按文件名关键字匹配:
  daily-xxx.txt       → {prefix}_daily.csv
  daily_basic-xxx.txt → {prefix}_daily_basic.csv
  adj_factor-xxx.txt  → {prefix}_adj_factor.csv
  trade_cal-xxx.txt   → {prefix}_trade_cal.csv
"""
import json
import csv
import os
import sys
import glob

def main():
    if len(sys.argv) < 4:
        print("用法: python fetch_stock_to_csv.py <result-dir> <out-dir> <prefix>")
        sys.exit(1)

    result_dir = sys.argv[1]
    out_dir    = sys.argv[2]
    prefix     = sys.argv[3]

    # 文件名匹配规则: 关键字 -> 输出名
    KEYWORD_MAP = {
        "daily_basic": f"{prefix}_daily_basic",
        "daily-":      f"{prefix}_daily",
        "adj_factor":  f"{prefix}_adj_factor",
        "trade_cal":   f"{prefix}_trade_cal",
    }

    os.makedirs(out_dir, exist_ok=True)

    # 列出 result_dir 下所有 txt 文件
    all_files = glob.glob(os.path.join(result_dir, "mcp-connector-proxy-tushareMcp_*.txt"))
    if not all_files:
        # 也尝试直接匹配
        all_files = glob.glob(os.path.join(result_dir, "*.txt"))
    if not all_files:
        print(f"[ERROR] 在 {result_dir} 下未找到任何结果文件")
        sys.exit(1)

    matched = {}
    for fpath in all_files:
        fname = os.path.basename(fpath)
        for kw, out_name in KEYWORD_MAP.items():
            if kw in fname:
                matched[out_name] = fpath
                break

    if not matched:
        print(f"[ERROR] 未匹配到已知数据类型的文件，找到: {[os.path.basename(f) for f in all_files]}")
        sys.exit(1)

    print(f"匹配到 {len(matched)} 个数据文件:")
    for out_name, fpath in matched.items():
        print(f"  {out_name} <- {os.path.basename(fpath)}")

    stats = {}
    for out_name, fpath in matched.items():
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not data:
            print(f"[EMPTY] {out_name}")
            stats[out_name] = 0
            continue

        rows = data if isinstance(data, list) else data.get("items", [])
        out_path = os.path.join(out_dir, f"{out_name}.csv")

        with open(out_path, "w", newline="", encoding="utf-8-sig") as fout:
            writer = csv.DictWriter(fout, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

        n = len(rows)
        stats[out_name] = n
        date_min = rows[-1].get("trade_date") or rows[-1].get("cal_date") or "?"
        date_max = rows[0].get("trade_date") or rows[0].get("cal_date") or "?"
        print(f"[OK] {out_name}.csv  ({n} rows, {date_min} ~ {date_max})")

    total = sum(stats.values())
    print(f"\n合计: {total} 条, 输出: {out_dir}")
    return total

if __name__ == "__main__":
    main()
