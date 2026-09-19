#!/usr/bin/env node
// bundle-check.js — 检查 GEO 周报项目关键脚本/文件是否齐全
//
// 用法:
//   node bundle-check.js
//
// 检查项：
//   1. 项目根目录存在
//   2. 关键 Python 脚本存在（render / inline / split / push）
//   3. 关键 source 文件存在（classify / translate / cli）
//   4. j2 模板存在
//   5. 凭据文件存在（APP_SECRET / 封面图）
//   6. SPEC 文档存在
//   7. .env 存在且含必要 key
//
// 不依赖第三方 npm 包；只用 Node.js 内置 fs + path。

import { existsSync, statSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { homedir } from 'node:os';

const PROJECT = '/Users/apple/Downloads/User/geo-report';
const HOME = homedir();

const CHECKS = [
  // 关键 Python 脚本
  { type: 'file', path: `${PROJECT}/src/geo_report/cli.py`, label: 'CLI 入口（cli.py）' },
  { type: 'file', path: `${PROJECT}/src/geo_report/classify.py`, label: '分类模块（classify.py）' },
  { type: 'file', path: `${PROJECT}/src/geo_report/translate.py`, label: '翻译模块（translate.py）' },
  { type: 'file', path: `${PROJECT}/src/geo_report/report/templates/weekly.html.j2`, label: 'HTML 模板（weekly.html.j2）' },
  { type: 'file', path: `${PROJECT}/scripts/13_render_only.py`, label: '渲染脚本（13_render_only.py）' },
  { type: 'file', path: `${PROJECT}/scripts/14_publish_to_zhili.py`, label: '推草稿箱脚手架（14_publish_to_zhili.py）' },
  { type: 'file', path: `${PROJECT}/scripts/15_split_zhili.py`, label: '拆篇脚本（15_split_zhili.py）' },
  { type: 'file', path: `${PROJECT}/scripts/16_inline_css.py`, label: 'inline 化脚本（16_inline_css.py）' },

  // 依赖
  { type: 'file', path: `${HOME}/.hermes/skills/zhiligithub/scripts/push.py`, label: '复用推草稿脚本（zhiligithub push.py）' },

  // 凭据
  { type: 'file', path: `${HOME}/.hermes/keys/wx_appsecret.txt`, label: 'WeChat APP_SECRET' },
  { type: 'file', path: '/tmp/zhili_cover.jpg', label: '周报封面图（/tmp/zhili_cover.jpg）' },

  // SPEC
  { type: 'file', path: `${PROJECT}/docs/specs/SPEC_ITEM_PIPELINE.md`, label: '管线 SPEC' },
  { type: 'file', path: `${PROJECT}/docs/specs/SPEC_REPORT_TEMPLATE.md`, label: '模板 SPEC' },
  { type: 'file', path: `${PROJECT}/docs/specs/SPEC_DATA_SCHEMA.md`, label: '数据 schema SPEC' },
  { type: 'file', path: `${PROJECT}/docs/specs/SPEC_INDEX.md`, label: 'SPEC 索引' },

  // AGENTS.md
  { type: 'file', path: `${PROJECT}/AGENTS.md`, label: '项目协作基础规范' },
];

const ENV_CHECKS = [
  { key: 'PG_HOST', label: 'Postgres host' },
  { key: 'PG_PORT', label: 'Postgres port' },
  { key: 'PG_USER', label: 'Postgres user' },
  { key: 'PG_DBNAME', label: 'Postgres database' },
  { key: 'PG_SCHEMA', label: 'Postgres schema' },
  { key: 'MINIMAX_API_KEY', label: 'minimax API key' },
];

function ok(msg) { console.log(`[OK]   ${msg}`); }
function fail(msg) { console.error(`[FAIL] ${msg}`); return false; }
function warn(msg) { console.error(`[WARN] ${msg}`); }

let pass = true;

console.log(`\n=== GEO 周报 bundle-check ===`);
console.log(`项目根: ${PROJECT}\n`);

console.log('-- 文件检查 --');
for (const c of CHECKS) {
  if (existsSync(c.path)) {
    ok(`${c.label}: ${c.path}`);
  } else {
    if (c.path.includes('/tmp/zhili_cover.jpg')) {
      warn(`${c.label}: 不存在（运行时用 xiaohu-ip-studio 生成）`);
    } else {
      pass = fail(`${c.label}: 不存在 (${c.path})`);
    }
  }
}

console.log('\n-- .env 检查 --');
const envPath = join(PROJECT, '.env');
if (!existsSync(envPath)) {
  pass = fail(`.env 文件不存在: ${envPath}`);
} else {
  const content = readFileSync(envPath, 'utf-8');
  for (const e of ENV_CHECKS) {
    const re = new RegExp(`^(?:export\\s+)?${e.key}\\s*=\\s*(.+)$`, 'm');
    const m = content.match(re);
    if (m && m[1].trim().length > 0) {
      ok(`${e.label} (${e.key}) 已设置`);
    } else {
      pass = fail(`${e.label} (${e.key}) 未设置或为空`);
    }
  }
}

console.log(`\n${pass ? '✅ 所有检查通过' : '❌ 有缺失项'}`);
process.exit(pass ? 0 : 1);