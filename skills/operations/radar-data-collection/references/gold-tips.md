# 金价 + TIPS 采集

## 铁律

**所有来源均失败 → 不写 gold_prices（跳过该步骤），不拿旧数据折中。**

入库时加 `ON CONFLICT (price_date) DO UPDATE SET ...`，同一天重复采集直接覆盖。

## 国际金价

### 主选：新浪财经沪金现货（纽约黄金期货主连）
```bash
RAW=$(curl -s --max-time 10 \
  'https://hq.sinajs.cn/list=hf_GC' \
  -H 'Referer: https://finance.sina.com.cn')
echo "$RAW" | iconv -f gbk -t utf-8
```
解析：`var hq_str_hf_GC="4071.592,,4071.800,4072.100,4092.400,4069.200,09:13:26,4098.600,4084.000,0,1,1,2026-07-29,纽约黄金,0"`

- 第一个字段（逗号前）= 实时美元/盎司价格（例：4071.592）
- 国际金价即该字段值，无需换算

```python
import re, subprocess
out = subprocess.run("curl -s --max-time 10 'https://hq.sinajs.cn/list=hf_GC' -H 'Referer: https://finance.sina.com.cn' | iconv -f gbk -t utf-8",
    shell=True, capture_output=True, text=True).stdout
m = re.search(r'hf_GC="([\d.]+)', out)
intl_usd = float(m.group(1)) if m else 0.0   # >0 才写入
```

### 备选：Metalprice API（已验证不稳定，可能完全无响应）
```bash
curl -s --max-time 10 'https://api.metals.live/v1/spot/gold'
```
返回 JSON 数组，取 `gold` 字段。

### 备选：ExchangerRate 换算（仅在其他来源均失败时跳过，不 fallback 旧数据）

## 国内金价（沪金现货，元/克）

换算公式：`dom_cny = round(intl_usd * usd_cny / 31.1035, 2)`

汇率：
```bash
curl -s --max-time 10 'https://api.exchangerate-api.com/v4/latest/USD' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['rates']['CNY'])"
```
备用汇率硬编码：7.25（超过 7.5 视为异常值跳过）

## 美10年TIPS（DFII10）

### 主选：Treasury.gov
```bash
MONTH=$(date -u '+%Y%m')
curl -s --max-time 10 \
  "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/${MONTH}/all?type=daily_treasury_real_yield_curve&field_tdr_date_value=${MONTH}&download=true" \
  | grep "$(date -u '+%m/%d/%Y')"
# 输出示例：07/28/2026,1.90,2.02,2.16,2.49,2.68
# 第4列（索引3）为10YR TIPS
```

### 备选：FRED
```bash
curl -s --max-time 10 \
  'https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFII10' | tail -3
```

TIPS 失败不影响金价写入，TIPS 字段留空。

## 入库 SQL

```sql
INSERT INTO gold_prices (price_date, intl_price_usd, intl_price_change,
  domestic_price_cny, domestic_price_change, tips_yield_10y, tips_yield_change)
VALUES ('${DATE}', ${INTL_USD}, ${INTL_CHG},
  ${DOM_CNY}, ${DOM_CHG}, ${TIPS_10Y}, ${TIPS_CHG})
ON CONFLICT (price_date) DO UPDATE SET
  intl_price_usd = EXCLUDED.intl_price_usd,
  intl_price_change = EXCLUDED.intl_price_change,
  domestic_price_cny = EXCLUDED.domestic_price_cny,
  domestic_price_change = EXCLUDED.domestic_price_change,
  tips_yield_10y = EXCLUDED.tips_yield_10y,
  tips_yield_change = EXCLUDED.tips_yield_change;
```

## 验证

```bash
docker exec radar-db psql -U radar -d radar \
  -c "SELECT * FROM gold_prices WHERE price_date='${DATE}';"
```
`intl_price_usd` 应在 3500~5000 范围；低于 3000 或高于 6000 → 立即停写，手动核查。
