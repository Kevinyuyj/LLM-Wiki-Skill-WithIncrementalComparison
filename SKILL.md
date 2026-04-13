---
name: knowledge-ingest
description: Kevin 知识库 ingest 工作流 — 从 raw/ 和 copilot-conversations/ 读取，增量处理后生成 LLM-WIKI 衍生笔记
version: 2.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [knowledge-base, ingest, wiki, llm-wiki]
    category: note-taking
    related_skills: [llm-wiki, obsidian]
    config:
      - key: wiki.path
        description: Wiki 根目录路径
        default: "~/wiki"
        prompt: Wiki directory path
---

# Knowledge Ingest 工作流 (Kevin's System)

> 基于 LLM-WIKI Skill 原版目录结构：`entities/` `concepts/` `comparisons/` `queries/`

## 核心原则

**raw/ 和 copilot-conversations/ 都是神圣不可侵犯的原始资料库**
- 永远保持原状：不修改、不移动、不删除
- ingest 只读取分析，在 wiki 衍生目录创建笔记

## 目录结构（严格遵循 LLM-WIKI）

```
wiki/                          # LLM-WIKI 根目录
├── SCHEMA.md                  # 领域定义、约定、标签体系
├── index.md                   # 内容目录
├── log.md                    # 操作日志
├── .ingest_manifest.json     # 增量追踪清单
├── raw/                      # Layer 1 原始资料（不动）
│   ├── articles/
│   ├── papers/
│   ├── transcripts/
│   ├── assets/
│   ├── workingdocs/
│   └── diarys/
├── entities/                  # Layer 2 衍生：人物/组织/产品/模型
├── concepts/                  # Layer 2 衍生：概念/主题
├── comparisons/               # Layer 2 衍生：对比分析
└── queries/                   # Layer 2 衍生：归档 Q&A
```

## 触发词

当用户说 **"ingest"** 时，执行完整 ingest 流程（见下方步骤 0-7）。

---

## 完整 Ingest 详细步骤

### 步骤 0：Session 首次 ingest 前的 Orientation

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
   - content_hash = SHA256(文件内容)  ← 使用 shasum -a 256 或等效工具
   - mtime = 文件修改时间
   - size = 文件大小
d) manifest 中的 key 使用相对路径（如 "raw/workingdocs/xxx.md"）
```

### 步骤 3：对比 manifest 与当前状态

```
当前文件路径列表 = set(遍历 raw/ 得到的路径)
manifest 路径列表 = set(manifest 的所有 key)

A. manifest 有，但当前没有 → 文件被删除
   → 从 manifest 中删除该条目

B. 当前有，manifest 没有 → 新文件
   → 标记为待处理

C. manifest 有，当前也有
   ├── content_hash 不同 → 内容变了 → 标记为待处理
   └── content_hash 相同 → 完全一样 → 跳过
```

### 步骤 4：遍历 copilot-conversations/ 对话文件

> ⚠️ 实际路径：位于 wiki 内部 `wiki/copilot/copilot-conversations/`（不是独立目录）

```
a) 路径：{wiki_path}/copilot/copilot-conversations/
b) 遍历该目录下所有文件
c) 过滤：跳过 .DS_Store 等系统文件
d) 用相同逻辑检查是否有新增/变化（基于 content_hash）
e) 标记待处理的对话文件
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
   - 所有新增页面加入对应 section（entities/concepts/comparisons/queries）
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
a) 列出所有新增/更新的 wiki 页面（entities/concepts/comparisons/queries）
b) 列出跳过的文件（无变化）
c) manifest 清理情况（如有文件被删除）
d) 整体统计：处理了 X 个 raw 文件，Y 个对话文件，更新了 Z 个 wiki 页面
```

---

### 判断标准

#### 何时创建 wiki 页面（Page Thresholds）

```
- 当一个 entity/concept 出现在 2+ 个 source 中 → 创建/更新页面
- 或当一个 entity/concept 在某个 source 中是核心主题 → 创建/更新页面
- 单纯一次提及/脚注级别 → 不创建页面
```

#### copilot-conversations/ 对话归档价值判断

判断标准与 Query 步骤完全一致：**"痛苦到不想重新推导"**

| 价值 | 类型 | 示例 | 归档？ |
|------|------|------|--------|
| 低 | 纯格式修复讨论 | 表格对齐、Markdown格式调整 | ❌ 跳过 |
| 低 | 内容已被 wiki 现有页面覆盖 | MCP 等概念已有笔记 | ❌ 跳过 |
| 高 | 具体实用技巧，难以重新推导 | Obsidian块引用、某工具的独特用法 | ✅ queries/ |

#### queries 归档标准

```
- 简单问答/即时能答 → 不归档
- 深度分析/复杂判断/难以重新推导 → 归档到 queries/
```

#### 踩坑记录（2026-04-13 实践更新）

❌ `.DS_Store` 文件必须过滤，不能纳入 manifest
❌ manifest key 使用相对路径，不使用绝对路径
❌ copilot-conversations/ 路径在 wiki 内部，不是独立目录
❌ 不要自创 knowledge/notes/diary 等 LLM-WIKI 未定义的目录

---

## 验证清单

ingest 完成后确认：
- [ ] raw/ 下所有文件保持原样（未移动、未修改）
- [ ] copilot-conversations/ 下所有文件保持原样
- [ ] 在 wiki 对应目录（entities/concepts/comparisons/queries）创建了衍生笔记
- [ ] index.md 已更新
- [ ] log.md 已记录本次 ingest
- [ ] manifest 已更新

## 错误示范（踩坑记录）

❌ 把 raw/ 文件移动到 entities/ 或 concepts/（严禁移动，只创建衍生笔记）
❌ 修改 raw/ 文件内容
❌ 删除 raw/ 文件
❌ 在 raw/ 之外创建 knowledge/notes/diary 等未定义目录
