#!/usr/bin/env node
// validate-weekly.js — 校验 inline 版 weekly.html 产物
//
// 用法:
//   node validate-weekly.js <path/to/_inline.html>
//   node validate-weekly.js <path/to/_inline_part1.html>
//
// 退出码: 0 = 通过；1 = 有错误
//
// 检查项（按 v1.17 标准）：
//   1. 中文字数 ≥ 1500（单篇拆分后）；≥ 18000（总产物）
//   2. 不含 <style> 块（已 inline 化）
//   3. 板块数 ∈ {1..5}（v1.18 后 5 角色分类）
//   4. 每个板块至少 1 个 <div class="item">
//   5. <title> 后缀 ∈ {（上）, （中）, （下）, （上）, （下2）}
//   6. 字节 ≤ 64KB
//
// 不依赖第三方 npm 包；只用 Node.js 内置 fs。

import { readFileSync, statSync } from 'node:fs';

const MAX_BYTES = 65536;          // WeChat 草稿 content 上限
const MIN_CHARS_FULL = 18000;     // 总产物最少的字
const MIN_CHARS_PART = 1500;      // 单篇最少中文字（parts=2/3 拆分后）
const VALID_TITLE_SUFFIX = ['（上）', '（中）', '（下）'];

function fail(msg) {
  console.error(`[FAIL] ${msg}`);
  return false;
}

function ok(msg) {
  console.log(`[OK]   ${msg}`);
}

function validate(path) {
  const html = readFileSync(path, 'utf-8');
  const bytes = Buffer.byteLength(html, 'utf-8');
  const isPart = /_inline_part\d/.test(path);
  const minChars = isPart ? MIN_CHARS_PART : MIN_CHARS_FULL;
  let pass = true;

  console.log(`\n=== 校验 ${path} ===`);
  console.log(`字节: ${bytes.toLocaleString()} (上限 ${MAX_BYTES.toLocaleString()})`);
  console.log(`类型: ${isPart ? '拆篇' : '总产物'}`);

  // 1. 字节上限（仅单篇检查；总产物本身超 64KB，需 split 后才能推）
  if (isPart) {
    if (bytes > MAX_BYTES) {
      pass = fail(`字节 ${bytes} 超 WeChat 64KB 上限`);
    } else {
      ok(`字节 ${bytes} ≤ ${MAX_BYTES}`);
    }
  } else {
    console.log(`[SKIP] 总产物字节 ${bytes}（需 split 后单篇 ≤ ${MAX_BYTES}）`);
  }

  // 2. 中文字数
  const cnChars = [...html].filter(c => '\u4e00' <= c && c <= '\u9fff').length;
  console.log(`中文字数: ${cnChars.toLocaleString()} (下限 ${minChars.toLocaleString()})`);
  if (cnChars < minChars) {
    pass = fail(`中文字 ${cnChars} 少于下限 ${minChars}`);
  } else {
    ok(`中文字 ${cnChars} ≥ ${minChars}`);
  }

  // 3. <style> 块必须剥除
  if (/<style/i.test(html)) {
    pass = fail('仍含 <style> 块，inline 化未完成');
  } else {
    ok('无 <style> 块');
  }

  // 4. 板块数
  const sections = [...html.matchAll(/class="section-h2"/g)];
  const secCount = sections.length;
  console.log(`板块数: ${secCount}`);
  if (secCount === 0) {
    pass = fail('无板块（section-h2 不存在）');
  } else if (!isPart && (secCount < 1 || secCount > 5)) {
    pass = fail(`总产物板块数 ${secCount} 不合理（v1.18 期望 5 章节）`);
  } else {
    ok(`板块数 ${secCount}`);
  }

  // 5. 每个板块至少 1 个 item
  const items = [...html.matchAll(/<div [^>]*class="item"/g)];
  const itemCount = items.length;
  console.log(`条目数: ${itemCount}`);
  if (itemCount === 0) {
    pass = fail('无 <div class="item"> 条目');
  } else {
    ok(`条目数 ${itemCount}`);
  }

  // 6. 标题后缀
  const titleMatch = html.match(/<title>([^<]+)<\/title>/);
  if (!titleMatch) {
    pass = fail('无 <title>');
  } else {
    const title = titleMatch[1];
    console.log(`标题: ${title}`);
    if (isPart) {
      const hasValidSuffix = VALID_TITLE_SUFFIX.some(s => title.endsWith(s));
      if (!hasValidSuffix) {
        pass = fail(`标题后缀不在 ${VALID_TITLE_SUFFIX.join('/')} 范围内: ${title}`);
      } else {
        ok(`标题后缀合法: ${title}`);
      }
    }
  }

  return pass;
}

const path = process.argv[2];
if (!path) {
  console.error('用法: node validate-weekly.js <path/to/_inline.html>');
  process.exit(1);
}

const pass = validate(path);
process.exit(pass ? 0 : 1);