# 舆情监控工具 To B SaaS 化技术方案

## 一、数据库设计（PostgreSQL）

### 核心表结构
- **tenants** — 租户/公司表（name, plan, 月分析额度）
- **users** — 用户表（phone/email 登录, 关联 tenant_id, 角色: owner/admin/member）
- **brand_configs** — 品牌配置表（品牌名、监控关键词、风险规则 JSONB、举报罪名列表、影响力权重）
- **analysis_tasks** — 分析任务表（每次上传=一个任务，状态: uploaded/analyzing/done/failed）
- **note_results** — 笔记结果表（标题、内容、互动数据、风险等级、举报文案、举报状态）
- **report_records** — 举报记录表（跟踪举报状态和平台反馈）
- **audit_logs** — 操作日志表（审计用）

关键设计：`tenant_id` 冗余到 note_results 和 report_records，避免多表 JOIN 做租户隔离。

---

## 二、后端架构（FastAPI + Celery）

### 项目结构
```
yuqing-saas/
├── app/
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # pydantic-settings 配置
│   ├── database.py          # SQLAlchemy async engine
│   ├── models/              # ORM 模型（6 张表）
│   ├── schemas/             # Pydantic 请求/响应
│   ├── api/                 # 路由模块
│   │   ├── auth.py          # 注册/登录/刷新 Token
│   │   ├── brands.py        # 品牌配置 CRUD
│   │   ├── tasks.py         # 上传/启动分析/SSE 进度/导出
│   │   ├── notes.py         # 笔记结果查询
│   │   ├── reports.py       # 举报管理
│   │   └── dashboard.py     # 数据看板
│   ├── services/
│   │   ├── analyzer.py      # 从 yuqing_analyzer.py 迁移
│   │   └── prompt_builder.py # 根据 brand_config 动态生成 prompt
│   └── tasks/
│       └── analyze_task.py  # Celery 异步分析
├── docker-compose.yml
└── Dockerfile
```

### API 路由（共 18 个端点）
- 认证：register / login / refresh / me
- 品牌：CRUD（GET/POST/PUT/DELETE /api/brands）
- 任务：upload / start / list / detail / stream(SSE) / export / delete
- 笔记：list(分页+筛选) / detail / 更新举报状态
- 举报：submit / list / update
- 看板：overview / trends / top-risks

### 核心改造：Prompt 动态化
当前 SYSTEM_PROMPT 硬编码"摩天轮"→ 改为从 brand_configs 表读取，动态拼接品牌名、风险规则、举报罪名。

### 认证：JWT
- Access Token 2h + Refresh Token 7天
- payload 携带 tenant_id，所有查询自动附加租户隔离

### 异步分析：Celery + Redis
- 上传后触发 Celery 任务，后台逐条分析
- 通过 Redis pub/sub 推送进度 → SSE 端点消费

---

## 三、前端方案（Vue 3 + Naive UI）

### 页面
- /login — 登录/注册
- / — 数据看板（风险趋势图、TOP 排行）
- /brands — 品牌配置管理
- /tasks — 分析任务列表
- /tasks/:uid — 任务详情（上传+进度+结果表格）
- /reports — 举报记录管理

### 复用当前设计
暗色"监控中心"风格、RiskBadge、InfluenceBar、UploadZone 等组件可直接迁移。

---

## 四、部署方案

### Docker Compose（4 个服务）
- postgres:16 — 数据库
- redis:7 — 缓存 + 消息队列
- api — FastAPI + Celery Worker
- frontend — Vue 构建产物 + Nginx

### 阿里云推荐配置
初期（≤10 客户）：2核4G ECS + 1核2G RDS + 1G Redis ≈ **580 元/月**
中期（≤50 客户）：4核8G ECS + 2核4G RDS + 2G Redis ≈ **1,230 元/月**

### Nginx 要点
- 前端静态文件 + API 反向代理
- SSE 端点需关闭 proxy_buffering
- 文件上传限制 50MB

---

## 五、安全设计
- 租户隔离：所有查询强制 WHERE tenant_id
- 文件上传：后缀 + MIME 校验 + 大小限制
- 密码：bcrypt 哈希
- 速率限制：登录 5次/分，分析 10次/时/租户
- API Key：按租户隔离，数据库加密存储

---

## 六、AI 成本估算
- 单条笔记 ≈ ¥0.05（gpt-5）
- 可降级 gpt-4o-mini 降 10 倍成本
- 建议：brand_configs 增加 model 字段，让客户选精度/成本

---

## 七、实施路径

### 阶段一：基础骨架
- FastAPI + PostgreSQL + Alembic 迁移
- 用户注册/登录 + JWT
- 品牌配置 CRUD
- analyze_note() 迁移 + prompt 动态化

### 阶段二：核心功能
- Celery 异步分析
- SSE 进度推送
- 笔记结果存库 + 分页
- Excel 导出

### 阶段三：前端 + 部署
- Vue 3 前端全部页面
- Docker 容器化
- 阿里云部署

### 阶段四：增值功能
- 数据看板（趋势图）
- 举报状态跟踪
- 操作日志审计

---

## 八、你现在可以准备的
1. 注册阿里云账号 + 实名认证
2. 注册一个域名（如 yuqing.xxx.com）
3. 域名备案（国内服务器必须，约 1-2 周）
4. 找 2-3 个潜在客户聊需求，验证品牌配置化的方向
5. 确定定价模型（按条/按月/按品牌数）

---

## 九、Agent 分工方案（推荐工具组合）

### 需要 2-3 个 Agent，推荐组合：Cursor/Claude Code + Bolt.new

| Agent 角色 | 负责内容 | 推荐工具 | 月费 |
|-----------|---------|---------|------|
| 后端开发 | FastAPI、数据库、Celery、JWT、Prompt 动态化 | Cursor 或 Claude Code | ~$20 |
| 前端开发 | 登录页、品牌配置、看板、任务详情、结果表格 | Bolt.new（内置数据库+部署） | ~$20 |
| 部署运维 | Docker、Nginx、阿里云 ECS、CI/CD | Cursor/Claude Code + 手动操作 | 含上方 |

### 工具能力对比

| 工具 | 擅长 | 不擅长 | 价格 |
|------|------|--------|------|
| Cursor | IDE 内精细编码，后端逻辑 | 不能自动部署 | $20/月 |
| Claude Code | 复杂代码理解和生成 | 不能自动部署 | 按用量 |
| Bolt.new | 全栈快速生成，内置数据库和部署 | 复杂后端（多租户、Celery） | $20/月起 |
| Lovable | 前端页面生成，Supabase 集成 | 自定义后端、无 serverless | $25/月起 |
| v0 | UI 组件生成 | 整页应用、后端 | $20/月起 |
| Devin | 自主完成完整子任务 | 贵，复杂项目仍需人工介入 | $500/月 |

### 性价比最优方案

Cursor（或 Claude Code）+ Bolt.new，总计约 $40/月：
- Cursor/Claude Code → 后端全部 + 部署配置文件
- Bolt.new → 前端页面快速生成 + 简单后端原型

不建议用 Devin（$500/月），当前阶段性价比不高。
