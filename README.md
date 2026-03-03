# 摩天轮票务 · 小红书舆情监控

针对小红书平台的品牌舆情监控工具，批量分析笔记风险等级、自动生成举报文案、一键跳转投诉。

**线上地址：** https://yuqingguanli-production.up.railway.app

---

## 功能

- **Excel 批量上传**：支持 `.xlsx` / `.xls`，无条数限制
- **AI 风险分析**：四级风险分级（高/中/低/无），流式进度实时展示
- **智能缓存**：同一笔记不重复调用 AI，重复上传自动提示并跳转历史结果
- **一键投诉**：点击"去投诉"直接跳转小红书原帖，举报文案一键复制
- **投诉跟踪**：标记每条笔记的投诉状态（待投诉/已投诉/已处理/已驳回/转人工）
- **历史记录**：所有分析批次持久化存储，随时回查
- **导出 Excel**：分析结果带风险颜色标注导出

---

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Flask + gunicorn |
| 数据库 | PostgreSQL（Railway 托管） |
| AI | Moonshot Kimi API（兼容 OpenAI 格式） |
| 前端 | 原生 HTML/CSS/JS，SSE 实时进度 |
| 部署 | Railway（Nixpacks 自动构建） |

---

## 本地运行

**1. 安装依赖**
```bash
pip install -r requirements.txt
```

**2. 配置环境变量**

复制 `.env.example` 为 `.env`，填入：
```
API_KEY=你的 AI API Key
API_BASE_URL=https://api.moonshot.cn/v1
DATABASE_URL=postgresql://...
```

**3. 启动服务**
```bash
python app.py
```

访问 http://localhost:5001

---

## Excel 格式要求

上传文件必须包含以下列（用「社媒助手」插件导出默认已包含）：

| 列名 | 说明 |
|---|---|
| 笔记标题 | 必填 |
| 笔记内容 | 必填 |
| 笔记话题 | 必填 |
| 点赞量 | 必填 |
| 收藏量 | 必填 |
| 评论量 | 必填 |
| 分享量 | 必填 |
| 笔记链接 | 可选，有则显示"去投诉"按钮 |

---

## 文件说明

```
├── app.py               Flask 主应用，路由 + 分析调度
├── db.py                数据库初始化与连接
├── yuqing_analyzer.py   AI 分析核心（Prompt + 重试逻辑）
├── folder_watcher.py    本地文件夹监听，自动上传新 Excel（可选）
├── reporter.py          Playwright 自动举报脚本（本地运行，需登录 Chrome）
├── start_chrome.sh      以远程调试模式启动 Chrome（reporter.py 前置）
├── templates/index.html 前端单页应用
├── railway.toml         Railway 部署配置
└── requirements.txt     Python 依赖
```

---

## 风险分级

| 等级 | 说明 |
|---|---|
| 高风险 | 假冒官方、盗用品牌诈骗、严重不实指控 |
| 中风险 | 明确负面评价、疑似冒用品牌、引导私下交易 |
| 低风险 | 轻微吐槽，情绪温和，影响力有限 |
| 无风险 | 客观中性讨论或正面评价 |

结果按「风险等级 → 影响力分数」双维度排序。

**影响力公式：** `点赞 + 收藏×2 + 评论×3 + 分享×4`

---

## 部署（Railway）

项目已配置 `railway.toml`，推送代码后自动构建部署：

```bash
railway up
```

所需环境变量在 Railway 控制台 Variables 中配置：`API_KEY`、`API_BASE_URL`、`DATABASE_URL`。
