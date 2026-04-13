---
name: knowledge-ingest
description: Kevin 知识库 ingest 工作流 — 增量版，基于 SHA256 content-hash 对比，只处理新增/变化的文件
version: 2.1.0
author: Kevinyuyj
license: MIT
github: https://github.com/Kevinyuyj/LLM-Wiki-Skill-WithIncrementalComparison
based_on: karpathy-llm-wiki (https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
metadata:
  hermes:
    tags: [knowledge-base, ingest, wiki, llm-wiki, incremental]
    category: note-taking
    related_skills: [llm-wiki, obsidian]
    config:
      - key: wiki.path
        description: Wiki 根目录路径
        default: "~/wiki"
---

# Knowledge Ingest 工作流 — Incremental Version

> 基于 [Karpathy's LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)，核心改进：**SHA256 content-hash 增量对比**，避免全量重复处理。

---

## 原版 vs 我们的增量版 — 核心差异

| | 原版 LLM-WIKI | 我们的增量版 |
|---|---|---|
| **触发时行为** | 读取 raw/ 全部文件，重复分析 | 对比 manifest，只处理新增/变化的文件 |
| **重复处理** | 每次都重新分析所有文件 | 相同内容跳过，节省 LLM 调用 |
| **内容去重** | 无 | 文件移动/重命名不影响判断（hash 相同则跳过） |
| **文件删除检测** | 无 | manifest 自动清理孤儿条目 |
| **增量状态管理** | 无 | `.ingest_manifest.json` 持久化 manifest |
| **copilot 对话处理** | 未定义 | 独立处理流程，价值判断标准与 Query 一致 |
| **Wiki 维护收尾** | 手动或部分自动 | ingest 后自动更新 index + log + manifest |

---

## 我们新增了什么（相对于原版 LLM-WIKI Skill）

### 1. 增量 manifest 系统

```json
// .ingest_manifest.json — 增量状态持久化
{
  "raw/workingdocs/article.md": {
    "content_hash": "a3f5c8...",   // SHA256 — 真正的内容指纹
    "mtime": 1744531200,
    "size": 12345,
    "processed_at": "2026-04-13T10:00:00Z"
  }
}
```

### 2. 三段式增量判断

```
A. manifest 有，当前没有  → 文件被删除 → 清理 manifest 条目
B. 当前有，manifest 没有  → 新文件 → 标记待处理
C. 都有，比较 content_hash
   ├── hash 不同 → 内容变化 → 标记待处理
   └── hash 相同 → 完全一样 → 跳过
```

### 3. copilot-conversations/ 独立处理

- 对话文件与 raw 文件**并行处理**，各自独立判断增量
- 归档判断标准：**"痛苦到不想重新推导"**
- 格式修复讨论 → 跳过；具体实用技巧 → 归档 queries/

### 4. 全自动 Wiki 收尾

ingest 完成后自动执行：
- index.md 更新（新增页面加入目录，总页数 +1）
- log.md 追加（记录本次处理了哪些文件）
- manifest 更新（新增/变化条目写入，删除条目移除）

---

## 目录结构

```
wiki/
├── SCHEMA.md                  # 领域定义、约定、标签体系
├── index.md                   # 内容目录
├── log.md                    # 操作日志
├── .ingest_manifest.json     # ⭐ 增量状态追踪（我们新增）
├── raw/                      # Layer 1 原始资料（不动）
│   ├── articles/
│   ├── papers/
│   ├── workingdocs/
│   └── diarys/
├── entities/                  # Layer 2 衍生：人物/组织/产品/模型
├── concepts/                  # Layer 2 衍生：概念/主题
├── comparisons/               # Layer 2 衍生：对比分析
└── queries/                   # Layer 2 衍生：归档 Q&A
```

> **注意**：`copilot-conversations/` 实际位于 `wiki/copilot/copilot-conversations/`，不是独立目录。

---

## 触发词

当用户说 **"ingest"** 时，执行完整流程（步骤 0-7）。

---

## 完整 Ingest 详细步骤

### 步骤 0：Orientation（每次 session 首次 ingest 前）

```
a) 读取 wiki/SCHEMA.md → 了解领域、约定、标签体系
b) 读取 wiki/index.md → 知道已有哪些页面
c) 读取 wiki/log.md（最近20-30行）→ 知道最近做了什么
d) 确认 manifest 路径：wiki/.ingest_manifest.json
```

### 步骤 1：读取 manifest

```
a) 读取 wiki/.ingest_manifest.json
   - 如文件不存在 → 创建空对象 {}
b) manifest 结构：{文件路径: {content_hash, mtime, size, processed_at}}
```

### 步骤 2：遍历 raw/ 所有文件，构建当前状态

```
a) 遍历 raw/ 及其所有子目录，收集所有文件
b) 过滤：跳过 .DS_Store 等系统文件
c) 对每个文件计算：
   - content_hash = SHA256(文件内容)
   - mtime = 文件修改时间
   - size = 文件大小
d) manifest 中的 key 使用相对路径（如 "raw/workingdocs/xxx.md"）
```

### 步骤 3：对比 manifest 与当前状态

```
A. manifest 有，但当前没有 → 文件被删除
   → 从 manifest 中删除该条目

B. 当前有，manifest 没有 → 新文件
   → 标记为待处理

C. manifest 有，当前也有
   ├── content_hash 不同 → 内容变了 → 标记为待处理
   └── content_hash 相同 → 完全一样 → 跳过
```

### 步骤 4：遍历 copilot-conversations/ 对话文件

```
a) 路径：{wiki_path}/copilot/copilot-conversations/
b) 遍历该目录下所有文件（跳过 .DS_Store）
c) 用相同逻辑检查是否有新增/变化（基于 content_hash）
d) 标记待处理的对话文件
```

### 步骤 5：执行 Ingest（对所有待处理文件）

#### A. 处理 raw/ 文件

```
对于每个待处理的 raw 文件：
a) 读取文件内容
b) 分析内容，提炼：
   - 人物/组织/产品/模型 → entities/
   - 概念/主题 → concepts/
   - 对比分析类 → comparisons/
c) 检查 index.md 是否已有相关页面
   - 有 → 更新现有页面（追加新信息，更新 updated 日期）
   - 无 → 创建新页面
d) 每个页面要求：
   - frontmatter 完整（title, created, updated, type, tags, sources）
   - 至少 2 个 [[wikilinks]]
   - tags 必须在 SCHEMA.md 标签体系内
```

#### B. 处理 copilot-conversations/ 对话

```
对于每个待处理的对话文件：
a) 读取对话内容
b) 分析每条 Q&A：
   - 判断标准："痛苦到不想重新推导"（与 Query 步骤标准一致）
     ├── 否 → 跳过
     └── 是 → 提取有价值内容 → queries/
c) 原对话文件：不做任何改动
d) 归档到 queries/ 时：
   - frontmatter 完整
   - 来源标注：copilot-conversations/原始文件名
   - [[wikilinks]] 引用相关 entities/concepts
```

### 步骤 6：Wiki 维护收尾（自动完成）

```
a) 更新 index.md：
   - 所有新增页面加入对应 section
   - 更新 "Total pages" 总数
   - 更新 "Last updated" 日期

b) 写入 manifest：
   - wiki/.ingest_manifest.json 更新所有被处理文件的 hash/mtime/size/processed_at
   - 清理 manifest 中已被删除的文件条目

c) 更新 log.md：
   ## [YYYY-MM-DD] ingest | N raw 文件处理，M 对话文件分析
   - 新增/更新的 entities/concepts/comparisons/queries 列表
   - manifest 更新情况（新增/变化/删除 各多少）
```

### 步骤 7：报告结果给用户

```
a) 列出所有新增/更新的 wiki 页面
b) 列出跳过的文件（无变化）
c) manifest 清理情况（如有文件被删除）
d) 整体统计：处理了 X 个 raw 文件，Y 个对话文件，更新了 Z 个 wiki 页面
```

---

## 判断标准

### Page Thresholds（何时创建 wiki 页面）

```
- 当一个 entity/concept 出现在 2+ 个 source 中 → 创建/更新页面
- 或当一个 entity/concept 在某个 source 中是核心主题 → 创建/更新页面
- 单纯一次提及/脚注级别 → 不创建页面
```

### copilot-conversations/ 归档价值判断

| 价值 | 类型 | 示例 | 归档？ |
|------|------|------|--------|
| 低 | 纯格式修复讨论 | 表格对齐、Markdown 格式调整 | ❌ 跳过 |
| 低 | 内容已被 wiki 现有页面覆盖 | MCP 等概念已有笔记 | ❌ 跳过 |
| 高 | 具体实用技巧，难以重新推导 | Obsidian 块引用、某工具独特用法 | ✅ queries/ |

### queries 归档标准

```
- 简单问答/即时能答 → 不归档
- 深度分析/复杂判断/难以重新推导 → 归档到 queries/
```

---

## 验证清单

ingest 完成后确认：
- [ ] raw/ 下所有文件保持原样（未移动、未修改）
- [ ] copilot-conversations/ 下所有文件保持原样
- [ ] 在 wiki 对应目录创建了衍生笔记
- [ ] index.md 已更新
- [ ] log.md 已记录本次 ingest
- [ ] manifest 已更新

---

## 错误示范

❌ 把 raw/ 文件移动到 entities/ 或 concepts/（严禁移动，只创建衍生笔记）
❌ 修改 raw/ 文件内容
❌ 删除 raw/ 文件
❌ 在 raw/ 之外创建 knowledge/notes/diary 等未定义目录
❌ `.DS_Store` 纳入 manifest（必须过滤）
❌ manifest key 使用绝对路径（应使用相对路径）

---

## 版本历史

| 版本 | 日期 | 改动 |
|------|------|------|
| 2.1.0 | 2026-04-13 | 增量 manifest 系统、copilot 对话处理流程、自动化 wiki 收尾 |
| 2.0.0 | 2026-04-13 | 重大修正：统一 LLM-WIKI 目录结构（entities/concepts/comparisons/queries） |
| 1.0.0 | 2026-04-12 | 初始版本（自创 knowledge/notes/diary 目录，后废弃） |
