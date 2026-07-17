# 现有方案扫描与可借鉴方法

> 版本:v1.0 · 调研日期:2026-07-17
> 目的:全网扫描与本系统定位相近的**开源项目、商业产品、学术系统**,回答三个问题:哪些轮子不用重造、哪些方法已被验证可直接采用、我们的差异化空间是否依然成立。
> 与 `knowledgebase.md` 的关系:knowledgebase 第 3.5 节是竞品功能清单;本文件深入到**方法与架构层**,并覆盖开源生态。

---

## 第一部分:GitHub 开源项目

> 核实方式:GitHub REST API 当日实测(star / 最近 push / 许可证均为 2026-07-17 精确值)+ 各项目 README 原文。

### 1.1 arXiv 每日筛选/推送类

| 项目 | ★ | 活跃 | 许可证 | 方案 |
|---|---|---|---|---|
| [zotero-arxiv-daily](https://github.com/TideDra/zotero-arxiv-daily) | 5,695 | 2026-07 | AGPL-3.0 | Zotero 文库作画像,embedding 排序,邮件推送,Actions 零成本 |
| [daily-arXiv-ai-enhanced](https://github.com/dw-dengwei/daily-arXiv-ai-enhanced) | 2,903 | 当天 | 自定义 | 每日爬类目,DeepSeek 中文摘要,Pages 阅读站,偏好存浏览器本地 |
| [cv-arxiv-daily](https://github.com/Vincentqyw/cv-arxiv-daily) | 1,484 | 2026-07 | Apache-2.0 | 纯关键词,无 LLM |
| [daily-paper-reader](https://github.com/ziwenhahaha/daily-paper-reader) | 815 | 2026-07 | MIT | 多路召回→重排→LLM 精排的完整链路,Pages 阅读平台 |
| [gpt_paper_assistant](https://github.com/tatsu-lab/gpt_paper_assistant) | 548 | 2024-03 停更 | Apache-2.0 | 自然语言 topic 正反例 + 作者白名单,GPT 双维打分,$0.07/天 |
| [ArxivDigest](https://github.com/AutoLLM/ArxivDigest) | 446 | 2024-05 停更 | MIT | 兴趣描述 + GPT 逐篇打分,邮件 |
| [DailyArXiv](https://github.com/zezhishao/DailyArXiv) | 446 | 2026-07 | 无 | 结果发 GitHub Issues 当收件箱 |

**三个重点项目**:

- **zotero-arxiv-daily**(本类 star 第一):"文库即画像"——新论文得分 = 与用户 Zotero 文库论文的加权平均相似度,**越新加入文库权重越高**(自动跟随兴趣漂移);排序用免费本地 embedding,LLM 只做 TL;DR → 成本极低。缺陷:单用户、无反馈闭环、AGPL 不友好商用。
- **gpt_paper_assistant**(Tatsu Hashimoto,方法最精细):每个主题写"Relevant / Not relevant"**正反例判据**;作者白名单(S2 ID)命中给保底分;先按 h-index 粗筛再 GPT 批量(5 篇/批)输出 relevance/novelty 双分;**留存误判样本做回归测试基准来迭代 prompt**。全 cs.CL 每天 $0.07。
- **daily-paper-reader**:多路召回(BM25/精确/向量)→ 动态预算候选池 → 本地 reranker(Qwen3-Reranker-0.6B)→ LLM 补分,各阶段可单独复跑带命中追踪;执行前**线性预估费用与耗时**。

### 1.2 论文推荐/文献监控

| 项目 | ★ | 活跃 | 许可证 | 方案 |
|---|---|---|---|---|
| [paperai](https://github.com/neuml/paperai) | 1,767 | 2026-07 | Apache-2.0 | txtai 语义索引 + RAG(医学向) |
| [arxiv-sanity-lite](https://github.com/karpathy/arxiv-sanity-lite) | 1,651 | 2023-06 停更 | MIT | **tag 即训练集**:每 tag 训一个 tfidf+SVM |
| [pasa](https://github.com/bytedance/pasa)(字节) | 1,625 | 2025-05 | Apache-2.0 | 论文搜索 Agent:Crawler+Selector 双智能体,RL 训练,自主顺引文扩展 |
| [aminer-daily-paper](https://github.com/tlysanhuo/aminer-daily-paper) | 475 | 2026-07 | MIT | 多形态输入统一为 ResearchProfile,推荐附一句话理由,飞书卡片 |
| [RSS-GPT](https://github.com/yinan-c/RSS-GPT) / RSSBrew | 355 | 2025-09 | MIT | RSS 聚合去重+GPT 摘要再发布为新 RSS |
| [PaperFlow](https://github.com/OpenRaiser/PaperFlow) | 145 | 2026-07 | MIT | **画像→排序→反馈→画像更新闭环** + 兴趣漂移建模 + 公开 Benchmark |

### 1.3 综述/趋势工具

| 项目 | ★ | 活跃 | 许可证 | 方案 |
|---|---|---|---|---|
| [OpenScholar](https://github.com/AkariAsai/OpenScholar)(AllenAI) | 1,561 | 2025-08 | Apache-2.0 | 4500 万论文 datastore + 检索增强 LM,逐句引用 |
| [asreview](https://github.com/asreview/asreview) | 946 | 2026-07 | Apache-2.0 | 系统综述**主动学习**:人标少量→模型排序其余 |
| [bibliometrix](https://github.com/massimoaria/bibliometrix) | 645 | 2026-06 | 自定义 | 科学计量全家桶(R) |
| [litstudy](https://github.com/NLeSC/litstudy) | 220 | 2025-05 | Apache-2.0 | Python 一站式:多源元数据→统计→引文网络→主题建模 |
| [Local-Citation-Network](https://github.com/LocalCitationNetwork/LocalCitationNetwork.github.io) | 142 | 2026-05 | GPL-3.0 | **种子论文→局部引文网络→找"你漏读的高被引"**,全靠免费 API |
| [VOSviewer-Online](https://github.com/neesjanvaneck/VOSviewer-Online) | 137 | 2025-07 | MIT | VOSviewer 的 Web 开源版 |

### 1.4 周报/日报生成(跨领域)

| 项目 | ★ | 活跃 | 许可证 | 方案 |
|---|---|---|---|---|
| [meridian](https://github.com/iliane5/meridian) | 2,432 | 2025-05 | MIT | RSS→逐篇 LLM 分析→**embedding+UMAP+HDBSCAN 聚簇→簇级深析→合成简报**,Cloudflare 全家桶 |
| [gpt-newspaper](https://github.com/rotemweiss57/gpt-newspaper) | 1,468 | 停更 | MIT | 7-Agent 流水线(含 writer↔critique 自我批评循环) |
| [agents-radar](https://github.com/duanyytop/agents-radar) | 907 | 当天 | MIT | 10 数据源→双语日报+**日→周→月自动 rollup**,Pages+Telegram+飞书+RSS+**MCP** |
| [auto-news](https://github.com/finaldie/auto-news) | 897 | 2025-07 | MIT | 多源+LLM 去噪 80%+周度 Top-K Recap,Notion 阅读端 |

### 1.5 中文生态

| 项目 | ★ | 活跃 | 许可证 | 方案 |
|---|---|---|---|---|
| [ChatPaper](https://github.com/kaixindelele/ChatPaper) | 19,682 | 2026-03 | 自定义 | 中文标杆:arXiv 爬取+固定字段模板总结+翻译审稿 |
| [BestBlogs](https://github.com/ginobefun/BestBlogs) | 3,909 | 2026-07 | 无 | **AI 六维评分+编辑精审公共质量池**,早报/周刊/播客,RSS 支持 `minScore` 参数订阅(核心服务端未开源) |
| [TrendPublish](https://github.com/liyown/ai-trend-publish) | 3,059 | 2026-06 | MIT | 抓取→LLM 分析→模板渲染→**自动发布微信公众号** |
| [CloudFlare-AI-Insight-Daily](https://github.com/justlovemaki/CloudFlare-AI-Insight-Daily) | 1,729 | 当天 | GPL-3.0 | CF Workers+Gemini 日报站+播客稿 |
| 飞书系(ArXivToday-Lark 等) | 41–475 | 活跃 | 混合 | 飞书 webhook+消息卡片,门槛极低 |

### 1.6 可借鉴方法汇总(按主题,注明出处)

**兴趣建模**:①文库即画像+时间加权(zotero-arxiv-daily);②主题正反例判据 prompt(gpt_paper_assistant);③作者白名单独立建模、保底分(同上);④多形态冷启动统一坍缩为 ResearchProfile(aminer-daily-paper);⑤tag 即训练集(arxiv-sanity-lite);⑥反馈闭环+兴趣漂移+"画像周报"供纠偏(PaperFlow / asreview)。

**排序评分**:①双维/多维打分+双阈值截断(gpt_paper_assistant / BestBlogs 六维);②召回-重排-精排三段式(daily-paper-reader);③**聚簇后按簇叙事**而非逐篇罗列(meridian);④推荐理由一句话随分输出(aminer-daily-paper);⑤**给筛选器建离线基准集做回归测试**(gpt_paper_assistant / PaperFlow-Bench)。

**LLM 成本控制**:①廉价信号前置粗筛($0.07/天实证);②排序不用 LLM,交给本地 embedding/reranker;③批量打分(5–10 篇/批 JSONL);④模型分层(粗活用 Flash/DeepSeek,合成才用强模型;DeepSeek 全类目日摘要 ~0.2 元/天);⑤执行前费用预估展示;⑥**一次计算全员共享**(公共摘要池服务端算一次,个性化放客户端)。

**推送渠道**:邮件 / GitHub Pages / Issues 收件箱 / Slack / 飞书卡片 / 微信公众号自动发布(TrendPublish 有完整实现)/ 再发布为 RSS / 播客音频 / **MCP server 供 AI Agent 消费**(2026 新趋势)。

**部署**:①fork+Actions+Secrets+Pages 零服务器是事实标准(两个坑:公共仓库 Actions 60 天不动会停;多 workflow 并发写仓需 concurrency group+重试 push);②Cloudflare Workers 适合高频抓取;③纯前端+Supabase(pgvector)。

### 1.7 开源生态普遍缺什么(= 我们的差异化空间验证)

1. **没有"研究方向"级别的一等公民抽象**——兴趣单元都是 prompt/关键词/文库,没有"方向的论文池、时间线、代表工作"。
2. **趋势分析与日常追踪割裂**:追踪类只输出"今天读什么",趋势类(litstudy/bibliometrix)只做一次性手动分析;无人做"每日增量→滚动趋势"流水线。
3. **研究空白识别几乎无人做**(唯一雏形:Local-Citation-Network 的"漏读高被引检测")。
4. **评分不可校准**:除 gpt_paper_assistant 的 debug 集和 PaperFlow-Bench,没人度量自己筛选器的准确率,无跨日一致性控制。
5. **周报=日报堆叠**:做对聚簇叙事+跨期连续性的只有 meridian(新闻域)。
6. **反馈闭环稀缺**且有反馈的项目恰好都不带 LLM 摘要/周报能力。
7. **多用户/团队形态缺失**:几乎全是"fork 一份自己用"。
8. **数据面窄**:基本只看 arXiv,引用/代码/评审数据很少融合。

**MVP 组合拳建议**:zotero-arxiv-daily 的兴趣建模与成本结构 + gpt_paper_assistant 的双维打分与基准集 + meridian 的聚簇叙事周报 + Local-Citation-Network 的空白检测思路;分发学 agents-radar 多渠道矩阵;部署走 Actions 零服务器,量大迁 Cloudflare。**许可证注意**:zotero-arxiv-daily(AGPL)、ChatPaper/dw-dengwei(自定义)只能学方法不能抄代码;其余主力多为 MIT/Apache-2.0。

---

## 第二部分:商业产品方法深挖与中文生态

> 核实方式:一手来源直接抓取(论文全文 / 白皮书 PDF / 官方博客与帮助文档 / GitHub API / dblp),关键数字交叉抽查(2026-07-17)。

### 2.1 方法笔记(按产品)

**Scholar Inbox(ACL 2025 Demo,与我们形态最接近、披露最完整)**
- 推荐:GTE-Large 编码"标题+[SEP]+摘要",PCA 降到 256 维(消融无损);**每用户一个逻辑回归,每次评分后秒级重训**;负样本 = 显式差评 + **随机采 5000 篇未交互论文作 easy negatives**(防小样本边界外推失控);分数线性缩放到 [-100,100] 展示。
- 冷启动三件套:作者搜索导入正种子 + Scholar Maps 地图点选 + **主动学习**(优先请用户评"决策边界附近偏正"的论文)。
- Digest:每篇附 PDF 前 5 张图表预览;自选投递频率与星期几;**catch-up digest** 给长期未登录用户补课。数据:80 万评分 / 23k 用户 / 35% 月活。
- 坑:仅覆盖 OA 源;二元评分无强度;逻辑回归无法建模多兴趣簇(靠 embedding 兜底)。

**Undermind(白皮书 2024,穷尽度量化是全场最独特设计)**
- Agentic 检索:语义+引文+LLM 推理出候选 → GPT-4 全文片段三分类 → 自适应再检索(跟随引文链)→ **穷尽度估计**。
- **穷尽度模型(最值得抄)**:发现比例 f = 1 − e^(−n/τ)(n=已评估论文数,300 条真实查询拟合 τ=80)——评估 150 篇覆盖 ~85%,300 篇 ~98%;指数振幅直接回答"该主题总共约有多少文献 / 是否新颖"。
- **半独立交叉验证 recall**:用 Google Scholar 命中集被自己覆盖的比例估计召回率(α≈97.6%),无需全库标注。
- 注意:白皮书里"10× 优于 GS"的对照组是弱基线(GPT-4 关键词×前 10×仅 arXiv),需打折看。
- UX:Describe(AI 追问澄清)→ Explore → Build(逐篇解释"为何与你的目标相关")→ **Keep up 持续订阅**。

**Elicit(准确率沟通的标杆)**
- 2026-05 大规模评估(994 篇 Cochrane 综述):检索 recall 95.0%;摘要筛选 sensitivity 96.89% / specificity 92.54%(对照人类单人 86.6%、双人 97.5% → "超单人、近双人");提取 95.6% 正确。
- **关键演化**:2025-03 时 specificity 仅 62.8% → 一年提到 92.5%——高灵敏筛选的假阳性是最难啃的,且宣传页只报 recall。
- 人机协作:每个结论附原文引句+高亮位置;用户可覆盖 AI 判断并记录理由;非对称阈值(Maybe 保留,strict No 才剔除)。
- 可抄的评估协议:17 名非用户 PhD 用真实问题盲评多产品,**top-5 论断逐条核引用(正确 1 / 小错 0.5 / 大错 0)**+ Wilcoxon 检验。
- Ought 学术遗产:Factored Verification(分解式幻觉检测;实测 GPT-4 每份多论文摘要 0.84 个幻觉,自纠后 0.46,"幻觉往往微妙")。

**scite(引用语境分类的全部工程细节 + 反面教材)**
- 管线:GROBID(PDF)+ Pub2TEI(出版商 XML)统一 TEI → biblio-glutton 对 Crossref 匹配;引用语境定位率 PDF 路径 ~70%、XML 路径 ~95%。
- 分类器:SciBERT 微调;5 万条专家标注;**真实分布 mentioning 92.6% / supporting 6.5% / disputing 0.8%** 的极端不平衡是根本难题;生产原则:**调类权重保证每类 precision>80%,宁漏勿错**。当前 disputing P .85 / R .45。
- **第三方打脸数据(必读)**:Bakker et al. 实测 324 条引用撤稿文献的引文,人工判 contrasting 17 条,scite 判 0 条——**徽章上"0 条反驳"多半是"没抓到"而非"没人反驳",缺失 ≠ 不存在**,UI 必须提示覆盖率。

**Consensus(聚合 meter 的护栏设计)**
- 三条护栏:no black boxes(全部支撑结果展示在 meter 下方)、**抽取而非生成**(证据是论文逐字原句)、置信度不足直接排除不强行预测。
- Meter 2.0 修正 1.0 的"n=1 病例与 meta 分析同权"问题:每个立场附四个质量指标(平均发表日期 / SR+RCT 计数 / 期刊 SJR / 引用和)+ 质量胜出徽章 + Mixed 类。

**Zeta Alpha(检索工程参考 + 行业警示)**
- 工程数据点:10 亿向量纯 HNSW 需 >3.5TB RAM(~$22k/月),量化粗排+磁盘全精度 rescoring 降本 ~10×;RAGElo(LLM-judge 两两对比+Elo,开源)、NanoBEIR 轻量评测集。
- **产品轨迹警示**:从"AI 研究者发现平台"转型企业 RAG——面向个人研究者的发现工具变现困难,这是行业信号(印证我们按机构/团队场景设计付费的必要)。

**AMiner 与中文生态**
- AMiner:三元组订阅(机构/学者/关键词)→ LLM 筛选摘要 → 微信小程序/邮件;PaperSet 把追踪升维为"论文集"对象;学者图谱(OAG/OAG-BERT/OAG-Bench)全球领先且有开放数据;2026 新形态:把追踪打包成 agent 技能出售(38.8 元)。坑:单向广播无反馈学习、API 收费封闭、频繁改版。
- 百度学术:**开题分析**(关键词→趋势/学者机构全景)是极佳冷启动范式;DeepSeek-R1 已接入。CNKI:引证追踪+定题订阅是经典 alerting,但趋势站疑似停维护。
- 机器之心 SOTA! 模型库:论文-代码-模型-数据集结构化打通,国内"论文情报结构化"最佳样本。

**相邻领域(专利/金融/新闻)**
- PatSnap:"一句话建监控";周报按**子技术×公司二维聚合**而非平铺。
- IPRally / Patentfield:**用户自训分类器挂进监控管道**(万样本秒级训练);SDI 警报固定每周五发(消费仪式感)。
- AlphaSense:**事件警报与定期快照分离**——增量事件即时报,状态类信息定期汇总。
- **Feedly AI(信息量最大的相邻产品)**:1000+ 预置 AI 模型作**语义原子**,用户 AND/OR/NOT 布尔组合成 feed;内容去重阈值 85%+同源不去重;**归因式负反馈**(downvote 必须指明原因,选"其他"时不更新模型);官方调参目标**每 feed 每周 10–20 篇**(防警报疲劳第一原则)。
- Semantic Scholar Feeds:收藏即正样本;官方冷启动配方"5 正 + 3 负";推荐池只取近 3 个月论文(显式新颖性窗口)。

### 2.2 设计模式清单(44 条精选,注明出处)

**订阅建模**:语义原子+布尔组合(Feedly);一句话建监控(PatSnap/Undermind);实体×切面二元建模(AlphaSense);个人语料即画像(zotero-arxiv-daily/AMiner);订阅对象升维为"论文集"(AMiner PaperSet)。

**冷启动**:作者导入+地图点选+主动学习三件套(Scholar Inbox);显式配方"5 正 3 负"(S2 Feeds);关键词→领域全景报告作首次交互(百度开题分析)。

**评分排序**:重 embedding 轻分类器+秒级重训(Scholar Inbox);随机 easy negatives 正则(同);分数归一 [-100,100] 透明展示+每篇一行入选理由(Scholar Inbox/Undermind);粗排-精排-顶排三级漏斗(Consensus);质量信号分级展示+胜出徽章(Consensus Meter 2.0)。

**反馈闭环**:**归因式负反馈,模糊信号不更新模型**(Feedly——直接照抄);收藏免费变正样本(S2);用户 flag+双人复核改标签(scite);用户自训分类器挂进管道(IPRally/Patentfield)。

**去噪**:内容去重 85% 阈值+同源不去重(Feedly);**每 feed 每周 10–20 篇流量预算**(Feedly);召回池 3 个月时间窗(S2);源分层开关(Feedly)。

**报告组织**:子主题×机构二维聚合(PatSnap);事件/快照分离(AlphaSense);固定投递仪式(Patentfield 周五上午/Scholar Inbox 自选);图表预览进 digest(Scholar Inbox);catch-up 补课(同);**穷尽度进度条**(Undermind——直接可移植到研究空白功能);报告对齐交付物(PRISMA 图/PPT/LaTeX,Elicit/AMiner);newsletter 打开率分析(Feedly)。

**证据与信任**:**抽取而非生成**(Consensus/Elicit/scite/AlphaSense 四家共识);聚合徽章 hover 展开明细(scite/Consensus);置信度门控宁缺毋滥(Consensus);面向用户标签按 precision>80% 调参(scite);**"缺失≠不存在"覆盖率提示**(scite 教训);准确率沟通=金标准+人类基线+分阶段报数+第三方验证(Elicit)。

**评估方法(内部 QA 直接可用)**:半独立交叉验证 recall(Undermind);top-5 论断核引用打分+盲评(Elicit);LLM-judge 两两对比+Elo(RAGElo,开源);先建轻量评测集(NanoBEIR);主动学习攻少数类(scite)。

**分发商业**:榜单作内容营销飞轮(AMiner AI2000);能力技能化/MCP 化出售(AMiner);人工标准化摘要层是长期护城河(Derwent DWPI)。

### 2.3 中文生态:机会与差距

**机会**:①飞书卡片(可交互按钮)+微信小程序是构建"推送→评分→再学习"闭环的现成载体,而**这个闭环恰恰是所有现存中文产品都没做的**;②中英桥接是刚需(每个中文开源项目第一功能都是翻译);③DeepSeek 级成本(全量 arXiv 日摘要 ~0.2 元/天)使 per-user 模型+LLM 摘要成本结构完全可行;④AMiner/OAG 学者图谱地基现成且开放;⑤围绕开题/组会/结题/申报节点做交付物;⑥追踪正迁移到 agent 技能/MCP 形态,窗口期。

**差距**:①中文没有 OpenAlex 级开放学术 API(CNKI 付费墙/百度反爬/AMiner 收费),中文文献追踪无人做好;②反馈闭环普遍缺失(全是单向广播);③渠道锁死公众号,内容资产随停更蒸发;④产品持续性差,用户积累反复归零(启示:订阅与评分数据要设计成可迁移资产);⑤**策展媒体有信任没规模、工具有规模没信任——"AI 初筛+个人画像+推荐理由+证据锚定"的中间层至今空白**;⑥中文产品无一公开准确率评估——公开可复现的评估本身可成为信任差异化。

## 第三部分:LLM 科研助手系统(有论文有代码)

> 核实方式:实访 arXiv / GitHub / HuggingFace / 官方博客(2026-07-17);未核实项文中标注。

### 3.1 系统笔记

**OpenScholar(UW + Ai2 → Nature 2026-02 正式发表)** — arXiv:2411.14199,Apache-2.0 全开源(代码/模型/数据/datastore)
- 数据:peS2o 4500 万论文,正文按 **250 词切 chunk、chunk 前拼论文标题**,2.34 亿 passages。
- 检索器训练配方(可直接照搬):bi-encoder = Contriever 在 peS2o 上继续对比学习;cross-encoder = BGE-reranker,训练数据**自合成**(摘要生成 query → 召回 top-10 → Llama 3 70B 打 1–5 分,4–5 为正例)。
- Pipeline:检索→重排→初稿→**自反馈迭代(≤3 条,信息不足则补检索)**→**逐句引用验证**。
- 评测(ScholarQABench,2,967 专家查询):8B 模型 correctness 胜 GPT-4o;**GPT-4o 在生物医学开放问答中 78–90% 引用是幻觉**(裸 LLM 不可用的最强反证);专家对比中 GPT4o 版 70% 优于人类专家撰写。
- 现状:演进为 Ai2 的 Asta 生态(含 AstaBench:准确率-成本 Pareto 评测)。

**PaperQA2(FutureHouse)** — arXiv:2409.13740,Apache-2.0,~8.9k stars 持续活跃
- **"超人类"的真实含义**:LitQA2 上 precision 85.2% vs 人类 73.8%,但 accuracy 与人类持平(66.0% vs 67.7%)——**超人类的是"不说错",靠 21.9% 拒答率换来**。这是周报可信度应采纳的产品哲学:高 precision 优先、宁可拒答。
- 核心配方 **RCS(Reranking and Contextual Summarization)**:对每个 chunk 独立跑一次 LLM,产出"0–10 相关性评分 + 面向问题的上下文摘要",过滤后再综合——评分与摘要素材一石二鸟。
- Citation Traversal:沿引用图扩展补漏。ContraCrow:跨论文矛盾检测,每篇生物论文平均发现 2.34 处矛盾、专家验证 70% 一致。
- 后续平台四 agent 中的 **Owl 专做"有人做过 X 吗?"**——正是研究空白验证的范式。

**STORM / Co-STORM(Stanford)** — MIT,~30k stars,pip 包 `knowledge-storm`
- 方法:视角发现 → **5 个视角写手 × 5 轮对话式提问**(与"检索作答的专家"对话)→ 大纲生成 → 按大纲逐节检索写作带引用。
- 评测:组织性相对提升 25%,70% Wikipedia 资深编辑认为有用;已知问题:**来源偏见转移**。
- 对报告生成的启示:多视角提问把周报从"论文清单"升级为"有观点结构的综述";**大纲是独立可评测的中间产物**(heading recall 可做回归测试);Co-STORM 的动态 mind map 适合跨期方向知识库。

**GPT Researcher 与开源 deep research 框架**(GPT Researcher 28.4k★ Apache-2.0;deer-flow 77.3k★ MIT;smolagents 28.4k★;dzhng/deep-research 19.4k★ <500 行 TS;langchain open_deep_research 12k★ 等)
- 五个收敛的共同模式:query 分解(planner)、并行检索(executors)、来源引用绑定、**reflection 循环(知识缺口→新查询,配硬预算防死循环)**、独立报告合成阶段(先压缩成"事实+引用"卡片再入模板)。
- 实证:CodeAgent > JSON 工具调用(GAIA 33%→55%,smolagents)。

**自动科研 agent(AI-Scientist / Agent Laboratory 类)——主要是反面教训**
- Agent Laboratory:自动评审 6.1 分 vs 人类 3.8 分,**系统性虚高**;"成本降 84%"的基线是 AI Scientist 而非人类。
- MLR-Bench:**约 80% 案例含伪造/未验证实验结果**;PaperBench:最佳模型复现分 21%,未超 PhD;LLM 评审可被 prompt 注入操纵至"100% 接收级评分"(arXiv:2509.10248)。
- Kosmos(2025-11):数据分析陈述准确率 85.5%、文献综述 82.1%,**结论性陈述仅 57.9%**——越接近"下结论"越不可靠。
- 社区共识分层:**可靠**=RAG+溯源的综述、结构化写作;**部分可靠**=idea 候选生成;**不可靠**=自动评分、novelty 判断、实验结果、裸 LLM 引用。

**文献嵌入与个性化排序**
- **SPECTER2 至今无官方后继**(2026-07 核实);通用模型已在 MTEB 科学子任务领先,但 **NV-Embed-v2 是 CC-BY-NC 不可商用**,可商用选 gte-large(MIT)/ Qwen3-Embedding(Apache-2.0)。
- **Scholar Inbox 论文(arXiv:2504.08385,80 万真实评分)是个性化排序最佳公开配方**:实测 GTE-Large(降 256 维)> SPECTER2 > TF-IDF;**每用户一个 logistic regression**;正样本=upvote,负样本=downvote + 随机采 5000 篇未交互论文作隐式负样本;**5 正 + 3 负即可冷启动**;秒级重训;主动学习标注决策边界论文。
- S2 Recommendations API 实测可用(`positivePaperIds`+`negativePaperIds`);Graph API 可直接取 `embedding.specter_v2` 免自算。

**知识图谱路线的研究空白识别(最有直接价值)**
- **Impact4Cast**(arXiv:2402.08640, MLST 2025,代码 MIT + 全量数据):2100 万论文→概念演化图(37,960 概念)→138 维图特征→**预测"从未共同研究过的概念对"的未来引用影响,AUC>0.9**。"研究空白"被操作化为**高预测影响但尚无连边的概念对**。
- **Sourati & Evans**(Nature Human Behaviour 2023):把作者节点加入概念超图,预测提升最高 400%;反向使用可区分"快被做掉的 gap"与"人类盲点 gap"。
- **SciMuse**(arXiv:2405.17044,代码 MIT):附带 **3,000 条研究组长排序的专家基准**,可用于离线校准 idea 排序器。
- OpenAlex 官方 topic 分类器开源(MIT,4,516 topics 四级层级);**注意:OpenAlex 2026-02 起 API 强制 key + 每日限额、免费 snapshot 改季度更新**,大规模分析须走本地 snapshot。

### 3.2 按模块的借鉴映射表

| 我们的模块 | 借鉴来源 | 具体做法 |
|---|---|---|
| 数据底座 | OpenScholar / OpenAlex | 本地 snapshot 做底库;250 词 chunk+拼标题;引用图走 S2 Graph API |
| 检索 | OpenScholar 两段式 + PaperQA2 | bi-encoder 粗召(可直接用 OpenScholar Retriever 权重)+ cross-encoder 精排(训练数据自合成配方);方向拆 5–10 个持久化子查询并行;引用图 traversal 补漏 |
| 个性化排序 | **Scholar Inbox 配方** | 冻结通用嵌入(避开 NC 许可)+ 每方向一个线性模型;显式负样本+隐式随机负样本;5正3负冷启动;秒级重训 |
| 论文质量评分 | Agent Lab / MLR-Bench 反面教训 + NAIP | **不用 LLM 当绝对裁判**(虚高+可注入);客观信号 + NAIP 影响预测主排序;LLM 分仅作带依据的相对辅助;正文注入剥离 |
| 总结/证据汇总 | PaperQA2 RCS | 每 chunk 独立 map 出"评分+摘要"再综合;temperature=0 可审计;按环节分配模型 |
| 报告生成 | STORM + OpenScholar | 固定大纲模板 + 多视角提问 agent(方法演进/benchmark/工程/争议)+ 成稿后 ≤3 条 self-feedback + **逐句引用只能来自 reference 池** + Reviewer 校验"每条结论有来源、日期在本周内" |
| 趋势分析 | OpenAlex topics + BERTopic + Impact4Cast | 三路信号:Kleinberg burst、主题时序斜率、**概念图新边形成速率**;离群点当新兴主题早期信号 |
| 研究空白 | Impact4Cast + Owl + SciMuse + ContraCrow | **完整链条:KG link prediction 找高影响未连接概念对 → 检索验证"真无人做过"(Owl 范式,而非 LLM 断言)→ LLM 扩写 → SciMuse 专家基准校准排序**;附加栏目:跨论文 claim 矛盾检测 |
| 可信度工程 | OpenScholar 引用验证 + PaperQA2 拒答 | 每条断言绑可点击出处;宁缺毋滥并显示"高置信 N 条/存疑 M 条";反思循环配硬预算 |

### 3.3 这些系统普遍未解决的(= 我们的机会)

1. **时间维度缺失**:全部是一次性会话,没有"持续追踪 + 去重记忆 + 只报增量新知"——本周 vs 上周 diff、旧闻过滤、跨期知识累积都要自建,这正是本系统的核心差异点;
2. **个性化与深度综合从未结合**:Scholar Inbox 只排序不综合,OpenScholar 只综合不个性化——"按用户兴趣模型驱动的定向综述"是空白;
3. **评分可信度无解**(LLM 评审虚高+可注入+novelty 判断被证伪)→ 机会在客观信号+影响预测+候选式呈现;
4. **空白识别两条路线没人打通**:KG link prediction(可计算不可读)与 LLM idea 生成(可读不可信)各自为政;
5. **矛盾/争议情报几乎无人产品化**(ContraCrow 已证可行);
6. **报告质量无持续回归测试**:仿 ScholarQABench 建小型私有基准做 CI 式回归是低垂果实;
7. 成本-质量 Pareto 意识刚出现(AstaBench 2025);来源偏见转移无人处理。

## 第四部分:综合结论

### 4.1 三个问题的答案

**① 哪些轮子不用重造(直接采用/照搬)**

| 组件 | 来源 | 证据强度 |
|---|---|---|
| 个性化排序内核 | Scholar Inbox 配方(GTE 嵌入+per-user 逻辑回归+随机负例+主动学习冷启动) | ACL 2025 论文,80 万评分实测 |
| 检索器与训练配方 | OpenScholar(权重可下载,reranker 训练数据自合成法) | Nature 2026,Apache-2.0 |
| chunk 级"评分+摘要" | PaperQA2 RCS | LitQA2 评测,Apache-2.0 |
| 报告生成骨架 | STORM 多视角提问+大纲评测 / deep research 框架五模式 | NAACL 2024,MIT |
| 研究空白候选生成 | Impact4Cast(KG link prediction,AUC>0.9,代码+数据 MIT) | MLST 2025 |
| idea 排序校准基准 | SciMuse 3,000 条专家排序 | 开源 |
| 主题分类 | OpenAlex topic 分类器(4,516 topics,MIT) | 官方开源 |
| 无 ground truth 评估 | RAGElo(LLM-judge+Elo,开源) | Zeta Alpha 生产使用 |

**② 哪些方法已被验证、直接写进产品规范**

1. **反馈闭环**:秒级重训(Scholar Inbox)+ 归因式负反馈、模糊信号不更新模型(Feedly)+ 收藏即正样本(S2);
2. **防警报疲劳**:每方向每周 10–20 篇流量预算(Feedly)+ 事件/快照分离(AlphaSense)+ 内容去重 85% 阈值;
3. **证据产品三原则**:抽取而非生成、置信度门控宁缺毋滥、面向用户的标签按 precision>80% 调参 + "缺失≠不存在"覆盖率提示(scite 正反面教材);
4. **成本结构**:廉价信号前置 + 排序不用 LLM + 批量打分 + 模型分层($0.07/天与 0.2 元/天两个实证);
5. **质量回归**:留存误判样本做基准集(gpt_paper_assistant)→ 升级为 ScholarQABench 式私有基准做 CI 回归;
6. **穷尽度量化**:f = 1 − e^(−n/τ) 曲线 + 半独立交叉验证 recall(Undermind)——直接嵌入研究空白模块,回答"这个方向前人做了多少"。

**③ 差异化空间是否成立 → 成立,且比预想更清晰**

全景扫描后确认的四个无人区(与 knowledgebase 第 20 章结论互相印证):
- **时间维度**:所有 LLM 科研系统都是一次性会话,"持续追踪+去重记忆+增量新知+跨期叙事"无人做;
- **个性化 × 深度综合**:排序派(Scholar Inbox/S2)不综合,综合派(OpenScholar/PaperQA2)不个性化;
- **研究空白闭环**:KG 路线(可计算不可读)与 LLM 路线(可读不可信)没人打通成"KG 找 gap → 检索验证 → LLM 扩写 → 专家基准排序"的完整链;
- **中文市场中间层**:反馈闭环+中英桥接+结构化推送+公开评估,四件事现存玩家都没做。

### 4.2 对 MVP 的修正建议(回写 knowledgebase 第 17 章的输入)

1. 个性化排序从"简化四维评分"升级为 **Scholar Inbox 配方**(工程量更小、有验证);冷启动采纳"5 正 3 负"显式配方;
2. 周报增加**流量预算**(每方向每周 10–20 篇)与**归因式负反馈按钮**;
3. 质量门禁补充"**缺失≠不存在**"覆盖声明(与既有覆盖声明机制合并);
4. 部署路线确认:GitHub Actions 零服务器起步(注意 60 天停摆与并发写坑)→ 量大迁 Cloudflare;
5. 研究空白模块(二期)技术路线确定:Impact4Cast + Owl 检索验证 + SciMuse 基准校准 + 穷尽度曲线展示;
6. 新增待评估项:MCP server / agent 技能形态的分发(2026 窗口期)。

### 4.3 许可证与风险备忘

- 可商用采用:MIT(STORM、meridian、Impact4Cast、SciMuse 等)、Apache-2.0(OpenScholar、PaperQA2、GPT Researcher、asreview 等);
- **只能学方法不能抄代码**:zotero-arxiv-daily(AGPL)、ChatPaper / daily-arXiv-ai-enhanced / AI-Scientist(自定义许可)、NAIP 与 HKU AI-Researcher(无 LICENSE 文件);
- **嵌入模型许可**:NV-Embed-v2(CC-BY-NC)不可商用,选 gte-large(MIT)或 Qwen3-Embedding(Apache-2.0);
- 数据源:OpenAlex 2026 新政(强制 key+限额+快照改季度)再次确认——大规模分析走本地 snapshot。
