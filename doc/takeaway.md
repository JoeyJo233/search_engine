# 宜家搜索引擎工程师 · 学习讲义

> 面向 IKEA Search Engine 团队的 Software Engineer 面试准备。
> 关键词主线:**GCP · 搜索结果排序 · 新 feature 对销量的影响 · 如何测试 · 搜索引擎前沿技术**
>
> 最后更新:2026-05-30

---

## 目录

1. [整体心智模型:电商搜索的目标函数](#一整体心智模型电商搜索的目标函数)
2. [搜索结果的排序 (Ranking)](#二搜索结果的排序-ranking)
3. [新 Feature 是增加还是降低销量?](#三新-feature-是增加还是降低销量)
4. [如何测试? (How to test)](#四如何测试-how-to-test)
5. [GCP:这套系统跑在哪儿](#五gcp这套系统跑在哪儿)
6. [搜索引擎前沿技术 (Frontier Tech)](#六搜索引擎前沿技术-frontier-tech)
7. [高频面试题自测清单](#七高频面试题自测清单)
8. [准备优先级建议](#八准备优先级建议)

---

## 一、整体心智模型:电商搜索的目标函数

宜家的搜索是典型的 **e-commerce search(电商搜索)**,它和 Google 那种 web search 最大的区别是:**它不只追求"相关",还要服务商业目标(销量、转化、利润、库存)**。

- 普通 web search 优化的是:**relevance(相关性)**。
- 电商搜索优化的是一个**多目标函数**:

```
排序得分 ≈ f(相关性, 转化率, 业务价值)
            ↑relevance  ↑会不会买   ↑利润/库存/战略品类
```

> **面试金句**:"In e-commerce search, relevance is necessary but not sufficient — we ultimately optimize for business outcomes like conversion and revenue, while keeping the customer experience trustworthy."

这条主线把所有关键词串起来:

| 关键词 | 在主线中的位置 |
|--------|----------------|
| 排序 | 怎么定义和优化这个 `f` |
| 新 feature 增加还是降低销量 | 怎么衡量改动对目标的影响 |
| 如何测试 | 用什么方法可信地衡量 |
| GCP | 在哪儿跑这套系统 |
| 前沿技术 | 这个 `f` 未来怎么演进 |

---

## 二、搜索结果的排序 (Ranking)

这是面试最可能深挖的部分。分三层来讲。

### 2.1 检索 → 排序的两阶段架构(必须会画)

```
用户 query
   │
   ▼
[Query Understanding]  拼写纠错 / 同义词 / 意图识别 / 类目预测
   │
   ▼
[Retrieval / 召回]     从百万 SKU 里粗筛出几百~几千个候选
   │   ├─ 词法召回 (lexical): BM25 / inverted index (Elasticsearch/Solr)
   │   └─ 语义召回 (semantic): 向量检索 (embedding + ANN)
   ▼
[Ranking / 精排]       对候选做精细打分排序 (Learning to Rank)
   │
   ▼
[Re-ranking / 业务层]  打散、多样性、库存、促销、赞助位
   │
   ▼
返回结果
```

**为什么分两阶段?** 对几百万商品逐个跑复杂模型太慢,所以先用便宜的方法召回,再用贵的模型精排。这是 **latency vs. quality 的工程权衡**,面试官爱听。

### 2.2 排序用到的信号 (features)

| 类别 | 例子 |
|------|------|
| **文本相关性** | BM25 分、query 和标题/描述的匹配度、embedding 相似度 |
| **商品质量** | 评分、评论数、退货率、图片质量 |
| **行为信号** | 历史点击率 (CTR)、加购率、转化率 (CVR) |
| **业务信号** | 库存、利润率、是否促销、是否战略品类、配送时效 |
| **个性化** | 用户历史、地理位置(就近门店有货)、设备 |
| **上下文** | 季节(圣诞/夏季)、时段 |

> **宜家特色**:**线上线下结合**。搜索结果可能要考虑"附近门店是否有货""能否当天自提",这是纯电商没有的维度,面试时提一句会加分。

### 2.3 Learning to Rank (LTR)

三种范式:

- **Pointwise**:把排序当回归/分类(预测每个 item 的分数)。简单但忽略相对顺序。
- **Pairwise**:学"A 应该排在 B 前面"(如 RankNet、LambdaRank)。
- **Listwise**:直接优化整个列表的指标(如 LambdaMART、ListNet)。
  - **LambdaMART(GBDT)是工业界经典 baseline**,务必记住。

**评估指标**(高频):

- 离线:**NDCG**(最常用,考虑位置折扣)、**MRR**、**MAP**
- 在线:**CTR、CVR、GMV、search abandonment rate(无点击搜索率)**

---

## 三、新 Feature 是增加还是降低销量?

这考的是**实验设计和因果推断**思维,不只是写代码。

### 3.1 核心陷阱:相关 ≠ 因果

> 你不能上线一个新 feature,看到销量涨了就说"是我的功劳"——可能正好赶上促销季。**必须用对照实验把其他因素隔离掉。**

### 3.2 答题框架(建议背下来)

当被问"你做了个新 feature,怎么知道它是增加还是降低销量?",用这个结构:

1. **明确指标 (Metrics)**
   - 主指标 (primary / OEC):转化率、人均 GMV、订单量
   - 护栏指标 (guardrail):延迟、无结果率、退货率、毛利率(防止"卖更多但都退货/都是低利润品")
   - 反指标 (counter-metric):防止局部优化损害全局
2. **A/B Test**:随机分流,对照组 vs. 实验组。
3. **统计显著性**:看差异是否 statistically significant(p-value / 置信区间),还要看是否 **practically significant**(业务上值不值)。
4. **下结论**:涨了 → 全量上线;跌了或持平 → 回滚/迭代。

> **金句**:"A new feature might increase clicks but decrease revenue — that's why we always pair the primary metric with guardrail metrics like margin and return rate."

---

## 四、如何测试? (How to test)

搜索团队语境下,"如何测试"**主要指在线实验 (A/B testing)**,其次才是传统软件测试。

### 4.1 A/B Testing(在线实验)— 重中之重

```
全部流量
   │
   ├──── 50% ──→ Control(旧排序)
   │
   └──── 50% ──→ Treatment(新排序)
                  ↓
          比较两组的 转化率 / GMV / 延迟
```

要点清单:

- **随机分流**:按用户(user-level)分,而不是按请求,避免同一用户看到忽好忽坏的结果。
- **样本量 & 统计功效 (power)**:实验前算需要多少流量、跑多久,才能检测出预期效果。
- **A/A test**:先跑两个完全一样的组,验证分流系统本身没偏差。
- **新奇效应 (novelty effect)**:新功能刚上线大家好奇点得多,要跑够长时间。
- **网络效应 / interference**:搜索一般还好,但要知道这个概念。
- **离线评估先行**:上线 A/B 前,先用历史数据做 **offline evaluation**(replay 历史 query 看 NDCG 变化),便宜又快,过了再上线。

**进阶概念(加分)**:**interleaving**——把两个排序结果交错展示给同一用户,比 A/B 更敏感、更省流量,搜索排序专用。

### 4.2 传统软件测试

- **单元测试 / 集成测试**:query 解析、召回逻辑、打分函数。
- **回归测试 (golden set)**:维护一批"标准 query → 期望结果",防止改动把已知好的结果改坏。
- **人工标注 / relevance judgement**:人工评估 query-doc 相关性(可结合用 LLM 辅助标注)。
- **Shadow / canary 部署**:新模型先影子运行或小流量灰度,观察再放量。

---

## 五、GCP:这套系统跑在哪儿

宜家是 **GCP 的大客户**,搜索团队大概率全栈在 GCP 上。要能把上面的架构**映射到 GCP 服务**。

| 搜索环节 | GCP 服务 |
|---------|---------|
| **数据仓库 / 分析** | **BigQuery**(算指标、跑 A/B 分析的核心,务必熟悉) |
| **数据管道 (ETL/流式)** | **Dataflow**(Apache Beam)、**Pub/Sub**(实时点击/行为流) |
| **向量检索 / 语义搜索** | **Vertex AI Vector Search**(原 Matching Engine)— ANN 服务 |
| **ML 训练/部署** | **Vertex AI**(训练 LTR/embedding 模型、模型部署、Feature Store) |
| **托管搜索** | **Vertex AI Search**(原 Retail/Discovery Search,Google 专门给电商的搜索方案) |
| **服务部署** | **GKE**(Kubernetes)、**Cloud Run** |
| **存储** | **Cloud Storage**(模型/数据)、**Bigtable**(低延迟在线特征) |

> **重点记 3 个**:**BigQuery**(数据/实验分析)、**Vertex AI**(ML)、**Vertex AI Search / Vector Search**(Google 的电商搜索托管方案)。
>
> **加分点**:Google 有专门产品 **Vertex AI Search for commerce / Retail Search**,就是给宜家这类零售商做搜索和推荐的。提一句会很对路。

如果 GCP 经验不多,面试前花时间在 **BigQuery(写 SQL 算转化率/做实验分析)** 上最划算。

---

## 六、搜索引擎前沿技术 (Frontier Tech)

按重要性排序。把前沿和**宜家业务**绑定最有说服力。

### 6.1 语义搜索 / 向量检索 (Semantic / Vector Search) ★★★

- 传统词法搜索(BM25)搜 "comfy chair for reading" 可能搜不到标题写 "armchair" 的商品(词不匹配)。
- **Embedding** 把 query 和商品映射到向量空间,用**语义相似度**召回,解决"同义不同词"。
- 配合 **ANN(近似最近邻)** 算法(HNSW、ScaNN)做大规模快速检索。Google 的 **ScaNN** 是这领域名作。
- **Hybrid search**:词法 + 语义结合,是目前工业界主流。

### 6.2 LLM 在搜索中的应用 ★★★(当前最热)

- **Query understanding**:理解复杂/口语化 query("我想要适合小公寓的可折叠餐桌")。
- **Query rewriting / expansion**:扩展同义词、纠正、补全意图。
- **RAG(检索增强生成)**:搜索 + 生成式回答,做"导购助手"("帮我搭配一个北欧风客厅")。
- **生成式标注**:用 LLM 替代部分人工 relevance 标注,降本。
- **Conversational / agentic search**:多轮对话式购物。

### 6.3 神经排序与多模态 ★★

- **Neural ranking / Learning to Rank** 用深度模型(超越 GBDT)。
- **Multimodal search**:**以图搜图、文搜图**(宜家场景超合适——"找跟这张图风格像的沙发")。基于 CLIP 类的图文联合 embedding。

### 6.4 个性化 & 实时性 ★

- 实时行为信号融入排序(刚浏览过的风格立即影响结果)。
- Session-based / sequential modeling。

> **最贴宜家的三个方向**:多模态(家居视觉性强)、RAG 导购、语义搜索(用户描述生活场景而非商品名)。

---

## 七、高频面试题自测清单

1. 给定百万级商品,设计宜家的搜索系统架构。(画两阶段图)
2. 怎么衡量"搜索做得好不好"?线上线下指标各说几个。
3. 你上线一个新排序模型,怎么证明它带来更多销量而不是损害体验?(A/B + guardrail)
4. 相关性高的结果转化率却低,你怎么排查和处理?
5. BM25 和向量检索的区别?什么时候用哪个?为什么要 hybrid?
6. 如何把 LLM 用到搜索里?有什么风险(延迟、幻觉、成本)?
7. A/B test 跑了一周显示涨 0.5%,你敢上线吗?(谈显著性、功效、guardrail、长期效应)
8. 设计一个测试方案,验证"拼写纠错功能"是否值得做。

---

## 八、准备优先级建议

时间有限时,按这个顺序投入:

1. **排序两阶段架构 + LTR + NDCG**(必考,技术核心)
2. **A/B testing + guardrail metrics + 因果思维**(团队明显重视)
3. **BigQuery 实操**(写 SQL 算转化率、做实验分析)
4. **向量检索 + hybrid search + LLM 在搜索的应用**(前沿,显视野)
5. **GCP 服务映射**(知道每块用什么服务即可)

---

### 可以继续深入的方向

- "系统设计题:设计宜家搜索"的**完整答题脚本**
- 一套**模拟面试题 + 参考答案**
- **BigQuery SQL 示例**:怎么算转化率 / 分析 A/B 实验
