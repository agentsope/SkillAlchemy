# Bio-Fraud Forensics · 生物医学论文数据造假筛查

> 「Report what you can see, interpret it with hedges and alternatives, and let an authorized body decide intent — never accuse.」

A screening methodology that reverse-engineers how real biomedical fraud was caught — from
PubPeer, Data Colada, Science Integrity Digest, ORI, and forensic tooling — into a reproducible
per-paper checklist. A detective's lens, not a verdict machine.

## 安装

    cp -r agentsop-bio-fraud-forensics ~/.claude/skills/agentsop-bio-fraud-forensics/

## 触发方式

- 「帮我看看这篇论文/这张图/这个 Western blot 有没有造假迹象」
- 分享一张图、凝胶条带、补充数据 `.xlsx` 或一个 DOI，问「这数据可信吗 / 像不像 P 过」
- 「这些统计量可能吗」「跑一下 GRIM / statcheck」「这是纸厂论文吗 / tortured phrases」
- 「去哪儿查这篇有没有被质疑 / 撤稿」（验证路由）
- 「帮我写一条 PubPeer 级、可复核的图像/数据质疑评论」

## 七个操作模型

| # | 模型 | 一句话 |
|---|------|--------|
| M1 | 造假分类学 | 分清捏造/篡改与诚实错误，只说「显著偏离」不说意图 |
| M2 | 图像取证 | 每条带是指纹；翻转/旋转/叠加确认，背景纹理才是铁证 |
| M3 | 统计取证 | GRIM/GRIMMER/statcheck 从正文证伪；calcChain 揪出挪动的行 |
| M4 | 曝光站点手法萃取+路由 | 把 PubPeer/博客当侦查食谱复现；红旗→验证平台 |
| M5 | 纸厂与系统性信号 | 信号是「跨批次复现」：tortured phrases、错误基因试剂、模板图、卖署名网络 |
| M6 | 证据分级与红线 | 三级措辞 + 禁用词 + 无辜解释门；披露事实+对冲+替代解释 |
| M7 | 可复现筛查流程与标注 | 最便宜信号先查；陌生人能照着复现才算数（7 字段标注） |

## 它怎么说话

- **标志立场**：红旗 ≠ 证据；只报「观察到的异常」和「请作者澄清的问题」，绝不替任何人定性「造假」。
- **绝不会做**：替作者扣「fraud/fabricated/misconduct」帽子（除非引用官方裁定）；生成公开指控或挂人帖；从图里推断「意图」。
- **三级措辞**：Tier 1 观察到的异常（默认）→ Tier 2 需作者澄清的问题（过无辜解释门后）→ Tier 3 官方已认定（只能引用，从不自创）。

## 边界

侦查/评估方法论，不是「指控生成器」，也不含「发现之后如何上报处置」（按需求移除）。
仅限生物医学/生命科学论文——图像造假信号不可照搬到物理/CS。工具与平台演进快，需实地核实当前状态；
法律框架以美国（ORI / 言论意见原则）为主，他法域诽谤风险更高。信息截止 2026 年 5 月。

## 免责

基于公开资料与真实案例提炼的筛查方法，输出为「待澄清的观察」，不构成对任何个人或机构的不端认定。
