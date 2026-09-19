# 凭据与文件路径

## WeChat 推送

| 项 | 值 |
|---|---|
| APPID | `wx38a91c353554588a`（硬编码于 `~/.hermes/skills/zhiligithub/scripts/push.py`） |
| APP_SECRET | `~/.hermes/keys/wx_appsecret.txt` |
| 封面图 | `/tmp/zhili_cover.jpg`（900×383，墨蓝 #1B365D） |

## 数据库

- PostgreSQL 15 实例：`radar`
- schema：`geo`（共享 radar 实例，schema 隔离）
- 表：`sources` / `ingest_raw` / `items` / `reports` / `ai_tools`
- 凭据：`.env`（`PGHOST` / `PGUSER` / `PGPASSWORD` / `PGDATABASE`）

## API keys

- `MINIMAX_API_KEY` 在 `.env`
- ⚠️ **已通过对话明文泄露 — 建议 rotate**
- GT 匿名端点 `translate.googleapis.com` 无需 key

## 关键文件

| 文件 | 用途 |
|---|---|
| `src/geo_report/cli.py` | `cmd_publish_weekly`（render + inline + split + push 一行命令） |
| `src/geo_report/classify.py` | `is_strongly_geo` / `classify_industry` / `INDUSTRY_KEYWORDS`（v1.17 待改 2 板块） |
| `src/geo_report/translate.py` | `translate_zh_batch` / `summarize_full_article` |
| `src/geo_report/report/templates/weekly.html.j2` | HTML 模板（v1.17 待改 2 板块） |
| `scripts/13_render_only.py` | 渲染 + 4 项验证门禁 |
| `scripts/15_split_zhili.py` | 按字节拆篇 |
| `scripts/16_inline_css.py` | 样式 A inline 化 |
| `scripts/14_publish_to_zhili.py` | 推草稿箱脚手架（dry-run 用） |
| `~/.hermes/skills/zhiligithub/scripts/push.py` | 推草稿箱（复用） |
| `docs/specs/SPEC_ITEM_PIPELINE.md` | 管线规范（v1.17 待更新） |
| `docs/specs/SPEC_REPORT_TEMPLATE.md` | 模板规范 |
| `docs/specs/SPEC_DATA_SCHEMA.md` | 数据 schema |

## 输出路径

| 文件 | 大小（v1.17 实测） |
|---|---|
| `data/reports/liusheng_geo_<DATE>.html` | ~93KB（含完整样式 A） |
| `data/reports/liusheng_geo_<DATE>_inline.html` | ~120KB（inline CSS +30%） |
| `data/reports/liusheng_geo_<DATE>_inline_part1.html` | ~25KB（上篇） |
| `data/reports/liusheng_geo_<DATE>_inline_part2a.html` | ~35KB（中篇） |
| `data/reports/liusheng_geo_<DATE>_inline_part2b.html` | ~59KB（下篇） |

## 项目路径

- 项目根：`/Users/apple/Downloads/User/geo-report/`
- skill 目录：`~/.minimax/skills/geo-report-publish/`
- 推送依赖：`~/.hermes/skills/zhiligithub/scripts/push.py`