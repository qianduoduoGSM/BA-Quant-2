#!/usr/bin/env python3
"""
日线行情复权计算。
用法: python adjust_daily.py <raw-dir> <out-dir> <prefix>

raw-dir:  含 {prefix}_daily.csv 和 {prefix}_adj_factor.csv 的目录
out-dir:  输出目录
prefix:   文件前缀 (如 "boc")

计算:
  - 前复权 (fwd): raw × (adj_factor / latest_adj_factor)  — 以最新日为锚，消除除权跳空
  - 后复权 (bwd): raw × adj_factor                       — 以上市/基期为锚，反映累积真实价值

输出: {out_dir}/{prefix}_daily_adj.csv
"""
import csv
import os
import sys

def main():
    if len(sys.argv) < 4:
        print("用法: python adjust_daily.py <raw-dir> <out-dir> <prefix>")
        sys.exit(1)

    raw_dir = sys.argv[1]
    out_dir = sys.argv[2]
    prefix  = sys.argv[3]

    daily_file      = os.path.join(raw_dir, f"{prefix}_daily.csv")
    adj_factor_file = os.path.join(raw_dir, f"{prefix}_adj_factor.csv")
    out_file        = os.path.join(out_dir, f"{prefix}_daily_adj.csv")

    for f in [daily_file, adj_factor_file]:
        if not os.path.exists(f):
            print(f"[ERROR] 文件不存在: {f}")
            sys.exit(1)

    os.makedirs(out_dir, exist_ok=True)

    # 1. 加载复权因子
    adj_map = {}
    with open(adj_factor_file, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            adj_map[row["trade_date"]] = float(row["adj_factor"])

    latest_factor = max(adj_map.values())
    print(f"复权因子: {min(adj_map.values()):.4f} ~ {max(adj_map.values()):.4f}")
    print(f"基准因子: {latest_factor:.4f}  (变化: {latest_factor - min(adj_map.values()):.4f})")

    # 2. 逐行复权
    price_fields = ["open", "high", "low", "close", "pre_close"]
    output_rows = []
    skip = 0

    with open(daily_file, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            td = row["trade_date"]
            factor = adj_map.get(td)
            if factor is None:
                skip += 1
                continue

            new_row = {"ts_code": row["ts_code"], "trade_date": td}
            coef_fwd = factor / latest_factor
            coef_bwd = factor

            for pf in price_fields:
                val = float(row[pf])
                new_row[f"fwd_{pf}"] = round(val * coef_fwd, 4)
                new_row[f"bwd_{pf}"] = round(val * coef_bwd, 4)

            for k in ["vol", "amount", "pct_chg", "change"]:
                new_row[k] = row[k]

            output_rows.append(new_row)

    output_rows.sort(key=lambda x: x["trade_date"], reverse=True)

    fieldnames = [
        "ts_code", "trade_date",
        "fwd_open", "fwd_high", "fwd_low", "fwd_close", "fwd_pre_close",
        "bwd_open", "bwd_high", "bwd_low", "bwd_close", "bwd_pre_close",
        "vol", "amount", "pct_chg", "change",
    ]

    with open(out_file, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(output_rows)

    # 3. 校验
    first = output_rows[0]
    last  = output_rows[-1]

    with open(daily_file, "r", encoding="utf-8-sig") as f:
        raw_rows = list(csv.DictReader(f))
    raw_first = float(raw_rows[0]["close"])
    raw_last  = float(raw_rows[-1]["close"])

    ok_fwd = abs(raw_first - first["fwd_close"]) < 0.001
    ok_bwd = abs(raw_last * adj_map[raw_rows[-1]["trade_date"]] - last["bwd_close"]) < 0.001

    print(f"\n{len(output_rows)} 条 (跳过 {skip} 条)")
    print(f"前复权验证 (最新日 close): {first['fwd_close']} vs 原始 {raw_first} → {'✓' if ok_fwd else '✗'}")
    print(f"后复权验证 (最远日 close): {last['bwd_close']} vs 原始×adj={raw_last * adj_map[raw_rows[-1]['trade_date']]:.4f} → {'✓' if ok_bwd else '✗'}")
    print(f"输出: {out_file}")

if __name__ == "__main__":
    main()
