#!/usr/bin/env python3
"""
中国银行 A 股复权计算
- 前复权 (forward-adjusted): 以最新日期为基准，历史价格向下调整
  adjusted = raw * (adj_factor / latest_adj_factor)
- 后复权 (backward-adjusted): 以上市首日为基准，后续价格向上调整
  adjusted = raw * adj_factor

输入: data/raw/boc_daily.csv + data/raw/boc_adj_factor.csv
输出: data/processed/boc_daily_adj.csv (前复权 + 后复权双列)
"""
import csv
import os
from pathlib import Path

RAW_DIR  = os.path.join(Path(__file__).parent.parent, "data", "raw")
OUT_DIR  = os.path.join(Path(__file__).parent.parent, "data", "processed")
os.makedirs(OUT_DIR, exist_ok=True)

# 1. 加载 adj_factor → dict {trade_date: adj_factor}
adj_map = {}
with open(os.path.join(RAW_DIR, "boc_adj_factor.csv"), "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        adj_map[row["trade_date"]] = float(row["adj_factor"])

latest_factor = max(adj_map.values())

print(f"复权因子范围: {min(adj_map.values()):.4f} ~ {max(adj_map.values()):.4f}")
print(f"最新复权因子 (基准): {latest_factor:.4f}")
print(f"复权因子变化: {latest_factor - min(adj_map.values()):.4f}  (说明存在分红/送股)")

# 2. 读取日线，逐行计算复权价格
price_fields = ["open", "high", "low", "close", "pre_close"]
output_rows = []
skip_count = 0

with open(os.path.join(RAW_DIR, "boc_daily.csv"), "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        td = row["trade_date"]
        factor = adj_map.get(td)
        if factor is None:
            skip_count += 1
            continue

        new_row = {"ts_code": row["ts_code"], "trade_date": td}

        # 前复权系数: raw → fwd_adjusted
        coef_fwd = factor / latest_factor
        # 后复权系数: raw → bwd_adjusted
        coef_bwd = factor

        for pf in price_fields:
            raw_val = float(row[pf])
            # 前复权
            new_row[f"fwd_{pf}"] = round(raw_val * coef_fwd, 4)
            # 后复权
            new_row[f"bwd_{pf}"] = round(raw_val * coef_bwd, 4)

        # 成交量、成交额不变（复权不影响）
        new_row["vol"]     = row["vol"]
        new_row["amount"]  = row["amount"]
        new_row["pct_chg"] = row["pct_chg"]
        new_row["change"]  = row["change"]

        output_rows.append(new_row)

# 3. 按 trade_date 降序输出（最新在前）
output_rows.sort(key=lambda x: x["trade_date"], reverse=True)

# 4. 字段顺序
fieldnames = [
    "ts_code", "trade_date",
    "fwd_open", "fwd_high", "fwd_low", "fwd_close", "fwd_pre_close",
    "bwd_open", "bwd_high", "bwd_low", "bwd_close", "bwd_pre_close",
    "vol", "amount", "pct_chg", "change",
]

out_path = os.path.join(OUT_DIR, "boc_daily_adj.csv")
with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(output_rows)

# 5. 校验
n = len(output_rows)
print(f"\n=== 复权完成 ===")
print(f"共 {n} 条记录 (跳过 {skip_count} 条无复权因子)")
print(f"输出: {out_path}")
print()
print("=== 前复权 (fwd) 验证 ===")
first = output_rows[0]   # 最新日
last  = output_rows[-1]  # 最远日
print(f"最新日 {first['trade_date']}: close={first['fwd_close']:.4f} (应与原始一致)")
print(f"最远日 {last['trade_date']}:  raw_close={float(last.get('change','')) or 'N/A'}")
# 重新读一次原始值
with open(os.path.join(RAW_DIR, "boc_daily.csv"), "r", encoding="utf-8-sig") as f:
    raw_rows = list(csv.DictReader(f))
raw_last = raw_rows[-1]
print(f"最远日原始 close={raw_last['close']} → 前复权 close={float(raw_last['close']) * (adj_map.get(raw_last['trade_date'], 1) / latest_factor):.4f}")
print()
print("=== 后复权 (bwd) 验证 ===")
print(f"最新日 {first['trade_date']}: close={first['bwd_close']:.4f}")
print(f"最远日 {last['trade_date']}: close={last['bwd_close']:.4f}")
print(f"  原始: {raw_last['close']} × {adj_map.get(raw_last['trade_date'])} = {float(raw_last['close']) * adj_map.get(raw_last['trade_date']):.4f}")

# 前复权最新日应等于原始最新日
raw_first_close = float(list(csv.DictReader(open(os.path.join(RAW_DIR, "boc_daily.csv"), "r", encoding="utf-8-sig")))[0]["close"])
print(f"\n=== 交叉验证 ===")
print(f"原始最新 close:    {raw_first_close}")
print(f"前复权最新 close:  {first['fwd_close']}")
print(f"差值:             {abs(raw_first_close - first['fwd_close']):.6f} (应≈0)")
print(f"后复权最远 close:  {last['bwd_close']} (应≈原始最远 close × adj)")
print(f"原始最远 close:    {raw_last['close']}")
