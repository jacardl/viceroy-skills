# 金价 + TIPS 采集参考

## 国际金价（Kitco）
```
browser.open https://www.kitco.com/charts/livegold.html
```
提取伦敦现货金价（USD/盎司）和涨跌幅度。

## 国内金价（沪金现货）

### 主选：雪球 SGE:au99.99
```bash
export PATH="$PATH:/Users/apple/.npm-global/bin"
~/.agent-reach-venv314/bin/python3 -c "
from agent_reach.channels.xueqiu import XueqiuChannel
ch = XueqiuChannel()
q = ch.get_stock_quote('SGE:au99.99')
print(q['current'], q['percent'])
"
```
> ⚠️ 返回 `price=1.55`（原始单位），需通过 `国际金价(USD/盎司) × USD/CNY汇率 ÷ 31.1035` 换算

### 备选：沪金 ETF SH518880 × 32.15
```bash
~/.agent-reach-venv314/bin/python3 -c "
from agent_reach.channels.xueqiu import XueqiuChannel
ch = XueqiuChannel()
q = ch.get_stock_quote('SH518880')
print(q['current'], q['percent'])
"
```

## 美10年TIPS（DFII10）

### Treasury.gov（主选）
```bash
# 获取当月数据
curl -s --max-time 10 \
  "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/2026/all?type=daily_treasury_real_yield_curve&field_tdr_date_value=202607&download=true" \
  | grep "$(date -u '+%m/%d/%Y')"
# 输出示例：07/23/2026,1.90,2.02,2.16,2.49,2.68
# 第4列（索引3）为10YR TIPS收益率
```

### FRED（备选）
```bash
curl -s --max-time 10 \
  "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFII10" | tail -3
```

## 入库字段
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
