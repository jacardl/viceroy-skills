# Reference: 东航 APP 超级智能体标书分析样例

This reference captures the worked examples that produced:

- `Projects/项目_东航 Agent 智能体/东航APP超级智能体应标准备材料清单_v1.2_2026-06-08.md` / internal v1.3.
- `Projects/项目_东航 Agent 智能体/东航APP超级智能体交付阶段交付物清单_v1.0_2026-06-08.md`.

## Source tender

- `raw/tendors/【招标文件】东航APP超级智能体建设项目 发售稿.md`
- Key compared sections:
  - First chapter / bidder instructions front table: project number, tender guarantee, highest price limit, file copies, validity period, joint bid/subcontract restrictions.
  - Chapter 2 bidder instructions: guarantee, validity, signature, sealing, quotation correction rules.
  - Chapter 4 technical specification: starred clauses, commitment letters, model/data/security/document delivery requirements.
  - Chapter 6 evaluation method: conformity review, economic score, business score, technical score.

## Main lessons extracted

1. Do not only read the scoring table. Conformity review is not scored but can reject the bid.
2. Do not mix old assumptions or generic bid-prep materials into the scoring table. In the East China case, the clearly readable business score had only 4 items: model filing, CS4+, CNVD, and CCRC data security certification.
3. Every row should include concrete numbers when present:
   - Tender guarantee: RMB 50,000.00.
   - Highest price limit: RMB 4,320,000.00 including tax.
   - Bid validity: 90 calendar days.
   - Electronic file: 1 stamped scanned PDF.
   - Paper files: 1 original + 4 copies.
   - Quote correction threshold: (omissions + calculation correction) / bid price <= 10%.
4. Every row should include original source index:
   - Chapter / section / table row.
   - Clause number where available.
   - Markdown line numbers if available from the read/search output.
5. Technical scoring video items must be listed one-by-one and named against the scoring item.
6. If the tender has internal inconsistency, mark it as a clarification point. Example: CUDA item showed score column 3 but text said 4.
7. Technical specification starred clauses and commitment letters should be separated as “mandatory technical response materials,” not confused with scored technical rows.
8. Delivery-stage extraction is a separate output from bid-prep scoring extraction. It must read requirements, technical specifications, resource lists, contract data sheet, service order, acceptance template, IP/source-code clauses, and after-sales clauses.
9. Delivery outputs must preserve all operational numbers: 1 month data delivery, 5 months initial acceptance, 6 months go-live, 12 months final acceptance, 2,000 records per scenario, 15 dialogue rounds, 16–32 cards, 30/30/30/10 payment, 6% VAT invoice, 8T object storage, RTO<10s, 0.05% daily liquidated damages, etc.
10. Contract conflicts must be highlighted as clarification points. In the East China case: “15 working days delivery” in the contract template conflicts with “5/6/12 month” project milestones; “final acceptance (go-live)” payment wording conflicts with separate go-live/final-acceptance milestones.

## East China output structure

```markdown
# 0. Scope
# 1. Conformity review mandatory materials / conditions
# 2. Economic bid materials
# 3. Business scoring materials
# 4. Technical scoring materials
# 5. Technical scoring video / attachment naming
# 6. Technical specification mandatory response materials
# 7. Materials excluded from this checklist
# 8. Execution priority
```

## Conformity review table pattern

```markdown
| 序号 | 符合性项目 | 招标要求摘要 | 需准备 / 确认的材料（含具体数值） | 原文索引 |
|---|---|---|---|---|
| 1 | 投标保证金 | 不存在未提交、保证金不足、形式不符合要求 | 投标保证金缴纳凭证 / 保函。金额：人民币伍万元整（50,000.00 元）。收款单位：上海东航招标咨询有限公司；开户行：招商银行上海外滩支行；账号：215902897510001。保证金形式：银行电汇、网银、银行保函、电子保函；银行电汇 / 网银须由投标人单位银行账户支付；银行保函须按格式九提供基本账户开户银行出具的保函原件；投标保证金应在投标有效期内保持有效。 | 第一章《投标邀请书》/ 投标人须知前附表：序号12；第二章《投标人须知》第14条；第六章《评标办法》符合性评审序号1 |
```

## Business score table pattern

```markdown
| 序号 | 评分项 | 分值 | 招标要求 | 必备材料 | 原文索引 |
|---|---|---:|---|---|---|
| 1 | 企业资质 | 3 分 | 投标人或所投大模型产品具有自研大模型产品，且大模型产品具备网信办备案证明；提供备案证明编号及备案证明材料得 3 分；原厂或原厂商关联公司提供 | 大模型产品备案编号；备案证明材料；原厂 / 原厂关联公司关系证明或授权证明 | 第六章《评标办法》商务标评审序号1 |
```

## Technical score table pattern

```markdown
| 序号 | 评分项 | 分值 | 必须准备的材料 | 视频 / 证明要求 | 原文索引 |
|---|---|---:|---|---|---|
```

## Video naming pattern

```text
T01_模型及智能体评估能力_视频演示.mp4
T02_模型长期记忆能力_视频演示.mp4
T03_注册中心能力_视频演示.mp4
...
```
