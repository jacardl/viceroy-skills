# Radar DB Schema

## Tables

### `news_articles`
| column | type | notes |
|--------|------|-------|
| id | SERIAL | PK |
| article_date | DATE | 采集日期（⚠️ 不是 `date`） |
| category | VARCHAR(50) | `ai`, `github`, `politics` |
| title | TEXT | |
| content | TEXT | |
| source | VARCHAR(255) | 来源 |
| url | TEXT | |
| lang | VARCHAR(10) | `zh`/`en` |
| summary | TEXT | 摘要 |
| description | TEXT | 完整描述 |

### `gold_prices`
| column | type | notes |
|--------|------|-------|
| id | uuid | PK（⚠️ 不是 SERIAL） |
| price_date | DATE | （⚠️ 不是 `date`） |
| intl_price_usd | DOUBLE PRECISION | 国际金价（美元） |
| intl_price_change | DOUBLE PRECISION | 国际金价涨跌 |
| domestic_price_cny | DOUBLE PRECISION | 国内金价（人民币/克） |
| domestic_price_change | DOUBLE PRECISION | 国内金价涨跌 |
| tips_yield_10y | DOUBLE PRECISION | 10年期TIPS收益率 |
| tips_yield_change | DOUBLE PRECISION | TIPS收益率变化 |
| shanghai_gold_rmb_per_gram | DOUBLE PRECISION | 上海金交所价格 |
| gold_note | TEXT | 采集备注+汇总文字 |
| created_at | TIMESTAMP | |

⚠️ **不要使用旧列名**：`price`, `unit`, `prev_price`, `change_pct` 均已废弃。
⚠️ **`tips_rates` 表不存在**，TIPS 数据写入 `gold_prices.tips_yield_10y`。

### `tips_rates`
**此表不存在。** TIPS 数据在 `gold_prices.tips_yield_10y`。

## 验证查询

```sql
-- 当日各类条数（用 article_date，不是 date）
SELECT category, COUNT(*) FROM news_articles WHERE article_date = '2026-08-26' GROUP BY category;

-- 当日金价（用 price_date）
SELECT * FROM gold_prices WHERE price_date = '2026-08-26';
```

## DB 访问

```bash
docker exec radar-db psql -U radar -d radar -t -c "SQL"
```
