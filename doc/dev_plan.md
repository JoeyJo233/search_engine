# 多模态家具搜索引擎 · 实施计划 (dev_plan)

> 一个面向 IKEA 搜索工程师面试的练手项目:在 ABO 家具子集上,端到端实现
> **召回 → 排序 → 评估** 的多模态搜索引擎,并为 AI search 预留扩展接口。
>
> - **目标**:面试展示型 + 边做边学,2–4 周(兼职节奏)
> - **数据**:Amazon Berkeley Objects (ABO) 家具/家居子集(图片 + 文本元数据)
> - **形态**:文搜文 / 文搜图 / 图搜图 三种多模态检索
> - **基础设施**:本地优先,文档中映射到 GCP 服务
> - **语言/栈**:Python + FastAPI + FAISS/Qdrant + CLIP + rank-bm25
>
> 最后更新:2026-05-30

---

## 0. 设计总览

```
                          ┌─────────────────────────────────┐
                          │   离线:数据摄取 & 索引构建        │
  ABO 家具子集 ──▶ Ingest ──▶ Embedding ──▶ Index             │
  (图 + 元数据)     清洗/筛选   文本向量       向量索引(FAISS)│
                              图片向量(CLIP) 词法索引(BM25)  │
                          └─────────────────────────────────┘
                                          │
                          ┌───────────────▼─────────────────┐
                          │   在线:查询服务 (FastAPI)         │
  用户查询 ──▶ Query ──▶ Retrieval ──▶ Ranking ──▶ 结果       │
  (文字/图片)  理解(极简) 词法+向量召回  重排打分              │
                          └───────────────┬─────────────────┘
                                          │
                          ┌───────────────▼─────────────────┐
                          │   评估:NDCG 等指标 + A/B 模拟      │
                          └─────────────────────────────────┘

  预留扩展位(本期只留接口):LLM 查询理解/改写 · RAG 导购 ·
                            神经/学习排序 · 个性化 · 真·GCP 部署
```

**设计原则**
- 每个模块单一职责、接口清晰、可独立测试。
- 检索/排序的核心逻辑自己写(理解原理),ANN 和 BM25 用成熟库(不重复造轮子)。
- 所有"以后想做"的能力都做成抽象接口 + 一个朴素实现,扩展时只换实现不动主干。

---

## 1. 技术选型

| 环节 | 选型 | 说明 / GCP 对应 |
|------|------|-----------------|
| 语言 | Python 3.11+ | 搜索/ML 生态最全 |
| 包管理 | `uv` 或 `venv + pip` | 轻量 |
| 词法检索 | `rank-bm25` | 经典 BM25,纯 Python,易读 → GCP: Vertex AI Search 的词法层 |
| 文本/图片 embedding | `sentence-transformers` + `open_clip` (CLIP) | 文搜文用文本模型,跨模态用 CLIP → GCP: Vertex AI Embeddings |
| 向量索引 | `faiss-cpu`(先)/ 可换 `qdrant` | ANN 近邻检索 → GCP: Vertex AI Vector Search |
| 服务 | `FastAPI` + `uvicorn` | 在线查询接口 → GCP: Cloud Run |
| 前端 | 极简:Streamlit 或单页 HTML+JS | 输入文字/上传图片看结果 |
| 数据处理 | `pandas` / `pyarrow` | ABO 元数据是 JSON/CSV |
| 评估 | 自写指标 + `pandas` | NDCG/Recall → GCP: BigQuery 做指标分析 |
| 测试 | `pytest` | 单元 + 回归(golden set) |

> 选型可按学习需要微调;原则是"核心逻辑透明,基础设施用成熟件"。

---

## 2. 目录结构(目标形态)

```
search_engine/
├── README.md                    # 项目简介 + 文档导航
├── pyproject.toml
├── doc/
│   ├── takeaway.md              # 理论知识 + 面试准备
│   └── dev_plan.md              # 本文件:架构 + 实施计划
├── data/
│   ├── raw/                     # ABO 原始下载(gitignore)
│   ├── processed/               # 清洗后的家具子集 parquet
│   └── index/                   # 构建好的向量/词法索引(gitignore)
├── src/
│   └── furnsearch/
│       ├── config.py            # 路径、模型名、超参
│       ├── ingest/              # [P1] 数据摄取
│       │   ├── download.py
│       │   └── build_subset.py  # 筛家具品类、统一 schema
│       ├── embedding/           # [P2] 向量化
│       │   ├── text_encoder.py
│       │   └── image_encoder.py # CLIP
│       ├── index/               # [P2] 索引
│       │   ├── vector_index.py  # FAISS 封装(可换 Qdrant)
│       │   └── lexical_index.py # BM25 封装
│       ├── retrieval/           # [P3] 召回
│       │   ├── retriever.py     # 词法/向量/融合,统一接口
│       │   └── fusion.py        # RRF / 加权融合
│       ├── ranking/             # [P4] 排序
│       │   ├── ranker.py        # 抽象接口 Ranker
│       │   └── feature_ranker.py# 特征加权实现(留 LTR 扩展位)
│       ├── query/               # 查询理解(本期极简,留扩展位)
│       │   └── understander.py  # 抽象接口 + passthrough 实现
│       ├── service/             # [P5] 在线服务
│       │   ├── app.py           # FastAPI
│       │   └── schemas.py       # 请求/响应模型
│       └── eval/                # [P6] 评估
│           ├── metrics.py       # NDCG / Recall@k / MRR
│           ├── offline_eval.py  # 跑评估集出报告
│           └── ab_sim.py        # A/B 测试模拟
├── frontend/                    # [P5] 极简前端
├── notebooks/                   # 探索/学习用
└── tests/                       # pytest
```

---

## 3. 分阶段实施计划

> 每个 Phase 结束都有一个**可验证的产出**和**学习目标**。建议按顺序做,每个 Phase 单独提交。

### Phase 0 · 项目骨架(0.5 天)
- 初始化 `pyproject.toml`、目录结构、`config.py`、`.gitignore`、`pytest` 骨架。
- 写 `README` 的"如何运行"占位。
- **产出**:空壳能 import,`pytest` 能跑通 0 个测试。
- **学习点**:项目工程化结构。

### Phase 1 · 数据摄取(1–2 天)
- `download.py`:从 AWS S3 公开桶拉 ABO 元数据(`s3://amazon-berkeley-objects/`),按需拉对应图片。
- `build_subset.py`:筛选家具/家居品类(沙发、桌椅、收纳、灯具、床品等),统一成 schema:
  `{id, title, description, category, color, material, price?, image_path}`。
- 控制规模(建议 3k–10k 商品,够练且本地跑得动)。
- **产出**:`data/processed/furniture.parquet` + 本地图片;一份数据 EDA notebook。
- **学习点**:真实电商数据的脏乱与清洗;schema 设计。
- **测试**:schema 校验、空值检查。

### Phase 2 · Embedding & 索引(2–3 天)
- `text_encoder.py`:用 sentence-transformers 把 title+description 编码成文本向量。
- `image_encoder.py`:用 CLIP 把商品图编码成图片向量(同时支持把文本编码进 CLIP 空间,供文搜图)。
- `vector_index.py`:FAISS 封装(`build / save / load / search(query_vec, k)`),抽象成接口便于换 Qdrant。
- `lexical_index.py`:rank-bm25 封装(`build / search(query_text, k)`)。
- 离线脚本:一键构建全部索引到 `data/index/`。
- **产出**:可加载的三套索引(文本向量、CLIP 图片向量、BM25)。
- **学习点**:embedding 原理、CLIP 图文联合空间、ANN(FAISS)、向量 vs 词法。
- **测试**:索引构建后能检索出 self(查自己 top1 是自己)。

### Phase 3 · 检索/召回(2–3 天)
- `retriever.py`:统一召回接口,支持三种模式:
  - **文搜文**:BM25 + 文本向量,RRF/加权融合 (hybrid)
  - **文搜图**:query 文本 → CLIP 文本向量 → 检索图片向量
  - **图搜图**:query 图片 → CLIP 图片向量 → 检索图片向量
- `fusion.py`:实现 Reciprocal Rank Fusion 和加权分数融合,可切换对比。
- **产出**:给定 query(文字或图片),返回 top-k 候选(带各路得分)。
- **学习点**:hybrid search、召回融合、两阶段架构的"召回"阶段。
- **测试**:几条人工 query 的 sanity check。

### Phase 4 · 排序(2 天)
- `ranker.py`:抽象接口 `Ranker.rank(query, candidates) -> ranked`。
- `feature_ranker.py`:可解释的特征加权排序。特征示例:
  相关性分(召回分)、品类匹配、(模拟的)评分/热度、价格合理性、图文一致性。
- 权重可配置,方便后面做 A/B 对比"不同排序策略"。
- **预留扩展位**:`Ranker` 接口让后续可插入 LTR/神经排序而不改调用方。
- **产出**:候选 → 最终有序结果。
- **学习点**:精排 vs 召回、特征工程、可解释排序、为什么后面要上 LTR。
- **测试**:权重变化对排序的影响符合预期。

### Phase 5 · 服务 + 前端(2–3 天)
- `service/app.py`:FastAPI,端点:
  - `GET /search?q=...&mode=text|t2i` 文本查询
  - `POST /search/image`(上传图片)图搜图
  - 返回结构化结果(id、标题、图片、各阶段得分,便于讲解/调试)
- `schemas.py`:Pydantic 请求/响应模型。
- 极简前端(Streamlit 最快):输入框 + 图片上传 + 结果网格(显示商品图)。
- **产出**:浏览器里能演示三种搜索的可交互 demo。
- **学习点**:把搜索能力服务化;延迟观察;demo 讲故事。
- **测试**:接口集成测试。
- **GCP 映射**:文档说明如何 Cloud Run 部署。

### Phase 6 · 评估 & A/B 模拟(2–3 天)
- 构造**评估集**:用 ABO 的品类/属性作为"代理相关性标签"(proxy relevance),
  生成若干 query→相关商品 的判定;在文档中坦白这是 proxy(非人工标注)。
- `metrics.py`:NDCG@k、Recall@k、MRR、(可选)Precision@k。
- `offline_eval.py`:跑两套配置(如 纯向量 vs hybrid;排序权重 A vs B)出对比报告。
- `ab_sim.py`:**A/B 测试模拟**——用一个简单的"点击/转化"行为模型(相关性越高越可能点/买),
  对两种策略各跑 N 次,输出转化率差异 + 显著性(t-test / 置信区间),演示"如何判断新 feature 增加还是降低销量"。
- **产出**:一份评估报告(指标表 + A/B 模拟结论)。
- **学习点**:NDCG、离线评估、A/B 测试、guardrail 指标、显著性——**面试核心考点**。
- **GCP 映射**:说明真实场景下这些日志/指标如何落 BigQuery 分析。

### Phase 7 · 收尾 & 面试材料(1 天)
- README:架构图、运行步骤、demo 截图/录屏。
- 一页"设计决策与权衡"文档(为面试准备):为什么 hybrid、为什么两阶段、proxy label 的局限、下一步会怎么上 LTR/LLM/GCP。
- 把 `learning_handout.md` 里的知识点和本项目对应起来。
- **产出**:可对外讲述的完整项目 + 面试话术。

---

## 4. AI Search 扩展位(本期不实现,接口已留)

| 扩展能力 | 接入点 | 简述 |
|----------|--------|------|
| LLM 查询理解/改写 | `query/understander.py` | 把 passthrough 换成 LLM:纠错、扩展、意图/品类识别 |
| RAG 导购问答 | 新增 `rag/` 模块 | 检索结果喂给 LLM 生成"搭配建议/导购回答" |
| 神经 / 学习排序 (LTR) | `ranking/ranker.py` 接口 | 用 LambdaMART / 神经排序替换 feature_ranker |
| 个性化 | retriever/ranker 入参加 user context | 历史/地理/会话信号融入排序 |
| 真·GCP 部署 | service + index 层 | 索引→Vertex AI Vector Search,服务→Cloud Run,日志→BigQuery |

---

## 5. 里程碑节奏建议(2–4 周)

| 周 | 内容 |
|----|------|
| 第 1 周 | Phase 0–2:骨架 + 数据 + embedding/索引(打地基,学 embedding/CLIP/FAISS) |
| 第 2 周 | Phase 3–4:召回融合 + 排序(搜索引擎主干,最核心) |
| 第 3 周 | Phase 5–6:服务/前端 + 评估/A-B(能演示 + 会评估,面试亮点) |
| 第 4 周 | Phase 7 + 缓冲:打磨、写面试材料、可选启动一个 AI search 扩展 |

---

## 6. 风险与对策

| 风险 | 对策 |
|------|------|
| ABO 数据量大、下载慢 | 只下元数据 + 子集对应的图片;规模控制在 3k–10k |
| 本地算 CLIP embedding 慢 | 用 CPU 小模型 / 批处理 / 一次算好缓存到磁盘 |
| 没有人工相关性标签 | 用 proxy label,文档坦白局限(面试反而是加分点) |
| 范围膨胀 | 严守 MVP;AI search 一律先留接口不实现 |
| 图片版权 | ABO 为研究用途公开;若公开 repo,图片不入库、只存路径/ID |

---

## 7. 验收标准 (Definition of Done)

- [ ] 能在本地一键构建索引(`make index` 或脚本)
- [ ] FastAPI 服务能跑,三种搜索(文搜文/文搜图/图搜图)都返回合理结果
- [ ] 前端能交互演示
- [ ] 评估脚本能输出 NDCG 等指标 + 一份 A/B 模拟对比结论
- [ ] `pytest` 全绿(含 ingest/index/retrieval/ranking 关键单测)
- [ ] README + 面试用"设计决策"文档完成
- [ ] 代码中 AI search 扩展接口清晰、有注释说明如何接
```

