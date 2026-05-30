# Multimodal Furniture Search Engine

一个自学/面试准备用的**多模态商品搜索引擎**项目 —— 面向 IKEA 搜索工程师岗位。
在 [Amazon Berkeley Objects (ABO)](https://www.amazon.science/code-and-datasets/amazon-berkeley-objects-abo-dataset) 家具子集上,
端到端实现 **召回 (retrieval) → 排序 (ranking) → 评估 (evaluation)**,
支持**文搜文 / 文搜图 / 图搜图**三种多模态检索,并为 AI search 预留扩展接口。

## 这个项目想达成什么

- **边做边学**:亲手走一遍电商搜索的完整流程,理解每一层在做什么、为什么。
- **面试展示**:可交互 demo + 可讲述的架构与权衡,覆盖排序、评估、A/B 测试、前沿技术等核心考点。
- **本地优先**:全部在本机用开源工具跑通,文档中标注每一块对应的 GCP 服务。

## 技术栈

Python · FastAPI · CLIP (open_clip) · sentence-transformers · FAISS/Qdrant · rank-bm25

## 文档

| 文档 | 内容 |
|------|------|
| [doc/takeaway.md](doc/takeaway.md) | **理论知识与面试准备** —— 电商搜索目标函数、排序 (LTR/NDCG)、A/B 测试、GCP 服务映射、前沿技术、高频面试题 |
| [doc/dev_plan.md](doc/dev_plan.md) | **开发文档** —— 技术架构、选型、目录结构、分阶段实施计划、AI search 扩展位 |

## Getting Started

需要 Python ≥ 3.11 和 [uv](https://docs.astral.sh/uv/)。

```bash
# 1. 安装依赖并创建虚拟环境
uv sync                 # 基础 + dev(pytest)
# 后续阶段按需安装重量级依赖:
# uv sync --extra ingest --extra ml --extra serve

# 2. 跑测试,确认环境就绪
uv run pytest
```

> **数据集**:本项目用 [Amazon Berkeley Objects (ABO)](https://amazon-berkeley-objects.s3.amazonaws.com/index.html) 家具子集
> (`abo-listings.tar` + `abo-images-small.tar`,约 3GB,CC BY-NC 4.0)。
> 数据**不进 repo**,需本地下载到 `data/raw/`。下载脚本将在 Phase 1 提供(`python -m furnsearch.ingest.download`)。

## 状态

🚧 开发中 · Phase 0(项目骨架)已完成,Phase 1(数据摄取)进行中。
详见 [doc/dev_plan.md](doc/dev_plan.md) 的分阶段计划。

## 范围说明

- 本项目**不使用** IKEA 官方数据;使用公开数据集 (ABO),"宜家场景"仅为练习语境。
- 排序评估采用品类/属性的 **proxy relevance** 标签(非人工标注),局限在开发文档中说明。
