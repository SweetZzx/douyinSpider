# Douyin Spider Web

<div align="center">

**抖音UP主视频管理与AI文案仿写系统**

一站式解决方案：从监控UP主新视频到AI创意文案仿写

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com)
[![Vue 3](https://img.shields.io/badge/Vue-3.4+-brightgreen.svg)](https://vuejs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://www.typescriptlang.org)
[![LangChain](https://img.shields.io/badge/LangChain-0.3+-orange.svg)](https://python.langchain.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 📖 项目简介

Douyin Spider Web 是一个**抖音UP主视频管理与AI文案仿写系统**，为内容创作者提供一站式解决方案：从关注UP主、监控新视频发布，到提取视频文案并使用AI生成创意仿写。

### 💡 解决什么问题？

作为内容创作者，你是否遇到过：
- 👀 想要关注优质UP主，但手动检查新视频太麻烦？
- 🎯 看到优秀的抖音视频，想仿写其文案但手动听写太慢？
- ⏰ 需要大量参考优质文案来激发创作灵感，但效率低下？
- 🤖 想要AI辅助创作，但缺少集成的便捷工具？

### ✨ 我们的解决方案

**两大核心功能一体化**：

```
【UP主视频监控】
添加UP主 → [自动监控] → 新视频提醒 → 快速浏览优质内容

         ↓

【AI文案仿写】
选中视频 → 提取音频 → 语音转写 → AI仿写 → 创意文案
```

**核心特点**：
- **自动监控** - 后台定时检查新视频，第一时间获取优质内容
- **AI驱动** - 支持自定义配置任何兼容OpenAI API的大模型服务（智谱AI、通义千问、DeepSeek等）
- **全自动化** - 从视频监控到文案仿写，一站式完成
- **灵活定制** - 支持自定义提示词模板，适配不同创作风格
- **智能管理** - UP主分组、新视频提醒、历史记录完整管理

### 🎯 核心功能

#### 📢 UP主视频监控

1. **➕ 添加关注UP主** - 输入UP主主页或视频链接，自动获取UP主信息
2. **🔄 自动监控新视频** - 后台每30分钟自动检查新视频发布
3. **🔔 新视频提醒** - Dashboard首页实时显示新视频数量和列表
4. **📊 数据统计** - 展示关注UP主数、视频总数、新视频数
5. **🏷️ 分组管理** - 支持按分组筛选和管理UP主（如：美食、科技、教育）
6. **⚡ 手动刷新** - 一键手动检查所有UP主的新视频
7. **✅ 标记已读** - 新视频可单独标记已读或全部已读

#### ✨ AI文案仿写

1. **🎬 选择视频** - 从视频列表中选择要仿写的视频
2. **🔊 一键提取音频** - 自动从视频中提取音频文件
3. **📝 智能语音转写** - ASR自动识别语音为文字（支持多种转写模型）
4. **🤖 AI智能仿写** - 基于大语言模型生成创意文案
5. **💾 保存与管理** - 保存转写文本和仿写结果
6. **✏️ 手动编辑** - 支持手动修改和优化仿写结果

#### 🎨 AI创作辅助

- **💬 对话式创作** - 与AI助手实时对话生成文案（支持多轮对话）
- **📋 提示词模板** - 自定义和管理创作风格模板（仿写/写作分类）
- **🔧 模型自定义配置** - 在设置页面配置语音转写和文案仿写的模型参数：
  - API地址（如：`https://open.bigmodel.cn/api/paas/v4`）
  - API密钥
  - 模型名称（如：`glm-4.7`、`glm-asr-2512`）
- **🌐 多模型支持** - 支持任何兼容OpenAI API格式的大模型服务：
  - 智谱AI（GLM系列）
  - 通义千问（DashScope）
  - DeepSeek
  - 其他OpenAI兼容服务

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 (Vue 3)                         │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌─────────┐  │
│  │ Dashboard │  │ 视频列表  │  │ 文案仿写  │  │ 设置   │  │
│  │  新视频提醒 │  │  UP主管理 │  │ 文案创作  │  │ 提示词 │  │
│  └───────────┘  └───────────┘  └───────────┘  └─────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/JSON
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                      后端 (FastAPI)                         │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌─────────┐  │
│  │ JWT认证   │  │ 速率限制  │  │ 音频提取  │  │ 语音转写 │  │
│  └───────────┘  └───────────┘  └───────────┘  └─────────┘  │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌─────────┐  │
│  │ AI仿写    │  │ LLM服务  │  │ UP主管理  │  │ 视频管理 │  │
│  └───────────┘  └───────────┘  └───────────┘  └─────────┘  │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌─────────┐  │
│  │ 抖音API   │  │ 定时任务  │  │ 提示词管理 │  │ 分组管理 │  │
│  │30分钟检查 │  │  新视频   │  │            │  │         │  │
│  └───────────┘  └───────────┘  └───────────┘  └─────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
                       ▼               ▼
┌────────────────────┐   ┌─────────────────────┐
│   MySQL 数据库     │   │   LLM 服务         │
│  UP主/视频/转写    │   │  可自定义配置       │
│  提示词/系统配置   │   │  智谱/通义/DeepSeek │
└────────────────────┘   └─────────────────────┘
```

---

## 🚀 核心工作流

### 工作流一：UP主视频监控

```
添加UP主 → 后台定时检查(30分钟) → 新视频提醒 → 浏览视频 → 选择仿写
   ↓              ↓                    ↓            ↓          ↓
 [自动]        [自动监控]           [Dashboard]   [快速查看]  [进入工作流二]
```

### 工作流二：快速仿写流程

```
选择视频 → 提取音频 → 语音转写 → AI仿写 → 创意文案
   ↓         ↓          ↓          ↓          ↓
 [一键]    [自动]     [自动]     [智能]     [输出]
```

### 工作流三：对话式创作

```
选择提示词模板 → 输入需求 → AI对话 → 迭代优化 → 完成文案
     ↓            ↓         ↓        ↓         ↓
   [多样化]    [灵活]    [实时]   [精准]   [满意]
```

---

## 🛠️ 技术栈

### 后端技术

| 技术 | 版本 | 说明 |
|------|------|------|
| **FastAPI** | 0.109+ | 现代化的Python Web框架 |
| **SQLAlchemy** | 2.0+ | Python ORM框架 |
| **MySQL** | 5.7+ | 关系型数据库 |
| **LangChain** | 0.3+ | LLM应用框架 |
| **智谱AI** | latest | 大语言模型 |
| **通义千问** | latest | 阿里云大模型 |
| **APScheduler** | 3.10+ | 定时任务调度 |
| **Loguru** | latest | 简单易用的日志库 |
| **bcrypt** | 5.0+ | 密码哈希 |
| **slowapi** | 0.1.9+ | 速率限制 |

### 前端技术

| 技术 | 版本 | 说明 |
|------|------|------|
| **Vue** | 3.4+ | 渐进式JavaScript框架 |
| **TypeScript** | 5.0+ | JavaScript超集 |
| **Element Plus** | latest | Vue 3 UI组件库 |
| **Vite** | 5.0+ | 下一代前端构建工具 |

### AI服务（可自定义配置）

| 服务类型 | 说明 |
|----------|------|
| **LLM服务** | 支持任何兼容OpenAI API格式的大模型（在设置页面自定义配置） |
| **ASR服务** | 支持语音转写服务（如智谱ASR、讯飞语音等） |
| **本地转写** | PyWhisperCpp 本地语音转写（可选） |

**支持的LLM服务商**（通过配置API地址和密钥）：
- 智谱AI (GLM-4.7, GLM-4-Flash等)
- 通义千问 (DashScope)
- DeepSeek
- 其他OpenAI API兼容服务

---

## 📁 项目结构

```
douyinSpider/
├── README.md                   # 项目说明文档
├── CLAUDE.md                   # Claude Code 项目配置
├── pyproject.toml              # Python 依赖配置
├── uv.lock                     # Python 依赖锁定文件
├── .env                        # 环境变量（不提交到Git）
│
├── backend/                    # Python 后端
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 配置管理
│   ├── auth.py                 # JWT认证模块
│   ├── exceptions.py           # 自定义异常和异常处理器
│   │
│   ├── db/                     # 数据库模块
│   │   ├── database.py         # 数据库连接配置
│   │   ├── models.py           # SQLAlchemy 数据模型
│   │   └── crud.py             # CRUD 操作（含事务管理）
│   │
│   ├── routers/                # API 路由
│   │   ├── api.py              # 主API路由
│   │   ├── auth.py             # 认证路由
│   │   ├── audio.py            # 音频提取路由
│   │   └── transcribe.py       # 语音转写路由
│   │
│   ├── services/               # 业务服务
│   │   ├── scheduler.py        # APScheduler定时任务
│   │   ├── audio_extractor.py  # 音频提取服务
│   │   ├── transcriber.py      # 语音转写服务
│   │   ├── llm.py              # LLM服务（多模型支持）
│   │   └── content_rewrite.py  # 文案仿写服务（核心）
│   │
│   └── lib/                    # 核心库
│       └── douyin/             # 抖音API封装
│           ├── request.py      # 请求封装
│           ├── client.py       # API客户端
│           ├── parser.py      # 数据解析器
│           └── target.py      # 目标处理器
│
└── frontend/                   # Vue 前端
    ├── index.html              # HTML入口
    ├── vite.config.ts          # Vite配置
    ├── package.json            # npm依赖配置
    │
    └── src/
        ├── main.ts             # TypeScript入口
        ├── App.vue             # 根组件
        │
        ├── views/              # 页面组件
        │   ├── Login.vue       # 登录页
        │   ├── Dashboard.vue   # 数据看板
        │   ├── Videos.vue      # 视频列表（仿写工作台）
        │   ├── Settings.vue    # 设置页
        │   ├── Prompts.vue     # 提示词管理
        │   ├── ContentWriting.vue  # 文案创作（对话式）
        │   └── ContentRewrite.vue  # 文案仿写
        │
        ├── components/         # 通用组件
        │   ├── VideoCard.vue   # 视频卡片
        │   └── VideoList.vue   # 视频列表
        │
        ├── services/           # API服务
        │   ├── api.ts          # 主API服务
        │   └── auth.ts         # 认证服务
        │
        ├── router/             # 路由配置
        │   └── index.ts        # 路由定义
        │
        ├── types/              # TypeScript类型
        │   └── index.ts        # 类型定义
        │
        └── styles/             # 样式文件
            └── main.css        # 全局样式
```

---

## 🚀 快速开始

### 环境要求

- **Python**: 3.10 或更高版本
- **Node.js**: 18.0 或更高版本
- **MySQL**: 5.7 或更高版本
- **uv**: 最新版本（Python包管理器）
- **API密钥**: 大语言模型API密钥（推荐使用智谱AI）

### 1. 克隆项目

```bash
# 使用SSH
git clone git@github.com:SweetZzx/douyinSpider.git

# 或使用HTTPS
git clone https://github.com/SweetZzx/douyinSpider.git

# 进入项目目录
cd douyinSpider
```

### 2. 后端配置

#### 2.1 安装依赖

```bash
# 安装uv（如未安装）
pip install uv

# 同步依赖
uv sync
```

#### 2.2 配置环境变量

创建 `.env` 文件：

```bash
# JWT密钥（生产环境请使用强密钥）
JWT_SECRET_KEY=your-secret-key-here

# 数据库配置（请使用强密码）
DATABASE_URL=mysql+pymysql://your_user:your_password@localhost:3306/douyin_spider

# Cookie配置（从浏览器获取，用于获取视频）
COOKIE=your-douyin-cookie-here

# 下载路径
DOWNLOAD_PATH=./downloads

# 日志配置
LOG_LEVEL=INFO
LOG_PATH=./logs

# ========== AI服务配置（默认配置，可在界面中修改） ==========

# 智谱AI配置（推荐）
ZHIPU_API_KEY=your-zhipu-api-key
ZHIPU_API_BASE=https://open.bigmodel.cn/api/paas/v4
ZHIPU_MODEL=glm-4.7

# 讯飞语音识别配置（可选）
XUNFEI_APPID=your-xunfei-appid
XUNFEI_API_KEY=your-xunfei-api-key
XUNFEI_API_SECRET=your-xunfei-secret

# 说明：
# - .env中配置的是默认值
# - 在系统设置页面可以自定义配置语音转写和文案仿写模型
# - 支持任何兼容OpenAI API格式的服务（智谱AI、通义千问、DeepSeek等）
```

### 3. 数据库配置

```sql
-- 登录MySQL
mysql -u root -p

-- 创建数据库
CREATE DATABASE douyin_spider CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. 启动后端

```bash
# 开发模式（自动重载）
uv run python -m backend.main

# 访问API文档
# http://localhost:77/docs
```

### 5. 前端配置

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 开发模式
npm run dev

# 访问前端
# http://localhost:5173
```

### 6. 构建生产版本

```bash
# 在frontend目录下
npm run build

# 构建产物在 frontend/dist/ 目录
```

---

## 💡 使用指南

### UP主管理

#### 添加UP主并监控新视频

1. 进入「Dashboard」页面，查看当前数据统计
2. 点击「关注UP主」统计卡片或进入UP主管理页面
3. 点击「添加UP主」按钮
4. 粘贴UP主主页链接或单个视频链接
5. 系统自动识别UP主信息并添加到数据库
6. 后台自动爬取该UP主的视频列表
7. **自动监控**：系统每30分钟自动检查所有UP主的新视频
8. **新视频提醒**：Dashboard首页会显示新视频数量和列表
9. **分组管理**：可以为UP主设置分组，方便筛选管理
10. **手动刷新**：点击「检查新视频」按钮可立即检查

#### 新视频提醒使用

- Dashboard首页「新视频提醒」卡片显示最新的新视频
- 支持按分组筛选新视频
- 点击「已读」标记单个视频为已读
- 点击「全部已读」一键清空新视频列表
- 点击视频标题可跳转到抖音查看视频
- 新视频会根据UP主添加时间判断（添加后发布的视频才算新视频）

### 快速仿写文案

#### 方式一：从视频列表仿写

1. 进入「视频列表」页面
2. 选择要仿写的视频
3. 点击「提取音频」按钮
4. 等待音频提取完成
5. 点击「语音转写」按钮
6. 等待转写完成，查看原始文案
7. 点击「AI仿写」按钮
8. 等待AI生成仿写文案
9. 复制或编辑仿写结果

#### 方式二：对话式创作

1. 进入「文案创作」页面
2. 选择提示词模板（可选）
3. 输入你的需求或原文
4. 与AI助手实时对话
5. 迭代优化文案
6. 获得满意的创意文案

### 提示词模板管理

1. 进入「提示词管理」页面
2. 查看已有的提示词模板
3. 创建新模板或复制现有模板
4. 设置默认模板
5. 在文案创作/仿写时使用模板

---

## ⚙️ 配置说明

### AI服务配置

系统支持**在Web界面中自定义配置**任何兼容OpenAI API格式的大模型服务。

#### 方式一：在Web界面配置（推荐）

1. 登录系统后，进入「设置」页面
2. 点击「🔧 模型设置」标签
3. 分别配置语音转写模型和文案仿写模型：
   - **API地址**：如 `https://open.bigmodel.cn/api/paas/v4`
   - **API密钥**：你的服务密钥
   - **模型名称**：如 `glm-4.7`（文案仿写）、`glm-asr-2512`（语音转写）
4. 点击「保存配置」按钮
5. 配置会加密保存在数据库中，后续任务将使用新配置

#### 方式二：通过环境变量配置（默认值）

在 `.env` 文件中配置默认值（可在界面中覆盖）：

```bash
# 智谱AI配置
ZHIPU_API_KEY=your-api-key
ZHIPU_API_BASE=https://open.bigmodel.cn/api/paas/v4
ZHIPU_MODEL=glm-4.7
```

#### 常用LLM服务商

| 服务商 | 获取API密钥 | 推荐模型 |
|--------|------------|----------|
| **智谱AI** | https://open.bigmodel.cn | glm-4.7, glm-4-flash |
| **通义千问** | https://dashscope.aliyun.com | qwen-plus, qwen-turbo |
| **DeepSeek** | https://platform.deepseek.com | deepseek-chat |
| **OpenAI** | https://platform.openai.com | gpt-4o, gpt-4o-mini |

### 环境变量详解

| 变量名 | 是否必需 | 默认值 | 说明 |
|--------|----------|--------|------|
| `JWT_SECRET_KEY` | ✅ 是 | - | JWT签名密钥 |
| `DATABASE_URL` | ✅ 是 | - | MySQL连接字符串 |
| `COOKIE` | ✅ 是 | - | 抖音Cookie（获取视频用） |
| `ZHIPU_API_KEY` | ❌ 否 | - | 智谱AI密钥（默认LLM） |
| `ZHIPU_API_BASE` | ❌ 否 | - | 智谱AI API地址 |
| `ZHIPU_MODEL` | ❌ 否 | - | 智谱AI模型名称 |
| `XUNFEI_APPID` | ❌ 否 | - | 讯飞语音识别AppID |
| `XUNFEI_API_KEY` | ❌ 否 | - | 讯飞语音识别API Key |
| `XUNFEI_API_SECRET` | ❌ 否 | - | 讯飞语音识别Secret |
| `DOWNLOAD_PATH` | ❌ 否 | `./downloads` | 音频下载路径 |
| `LOG_LEVEL` | ❌ 否 | `INFO` | 日志级别 |

---

## 📡 API 接口

### 认证接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 用户登录 |
| POST | `/api/auth/logout` | 用户登出 |
| POST | `/api/auth/verify` | 验证Token |

### 文案仿写接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/content-rewrite` | 文案仿写（纯文本） |
| POST | `/api/videos/{id}/rewrite` | 视频文案仿写（保存到数据库） |
| PUT | `/api/videos/{id}/rewrite` | 手动更新仿写文案 |
| POST | `/api/chat` | AI对话式创作 |

### 音频处理接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/audio/extract` | 提取视频音频 |
| GET | `/api/audio/{id}` | 获取音频文件 |
| POST | `/api/transcribe` | 语音转写 |

### 提示词管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/prompt-templates` | 获取提示词模板列表 |
| POST | `/api/prompt-templates` | 创建提示词模板 |
| PUT | `/api/prompt-templates/{id}` | 更新提示词模板 |
| DELETE | `/api/prompt-templates/{id}` | 删除提示词模板 |
| POST | `/api/prompt-templates/{id}/set-default` | 设置默认模板 |
| POST | `/api/prompt-templates/{id}/copy` | 复制提示词模板 |

**完整API文档：** 启动后端后访问 http://localhost:77/docs

---

## 🌐 服务器部署

> ⚠️ **注意**：以下为部署示例，请根据您的实际服务器配置进行调整

### 同步代码

```bash
# 同步后端代码
scp -r backend pyproject.toml .env user@your-server:/path/to/app/

# 同步前端代码（先构建）
cd frontend && npm run build
scp -r dist/* user@your-server:/path/to/app/frontend/
```

### 使用systemd管理

创建 `/etc/systemd/douyin-spider.service` 文件：

```ini
[Unit]
Description=Douyin Spider Web Service
After=network.target mysql.service

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/app
Environment="PATH=/path/to/app/.venv/bin"
ExecStart=/path/to/app/.venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 77
Restart=always

[Install]
WantedBy=multi-user.target
```

管理服务命令：

```bash
# 启动服务
systemctl start douyin-spider

# 停止服务
systemctl stop douyin-spider

# 重启服务
systemctl restart douyin-spider

# 查看状态
systemctl status douyin-spider

# 查看日志
journalctl -u douyin-spider -f
```

### 使用systemd管理

```bash
# 启动服务
systemctl start douyin-spider

# 停止服务
systemctl stop douyin-spider

# 重启服务
systemctl restart douyin-spider

# 查看状态
systemctl status douyin-spider

# 查看日志
journalctl -u douyin-spider -f
```

---

## 🔒 安全性

本项目实现了多层安全防护：

- ✅ JWT令牌认证 + bcrypt密码哈希
- ✅ 速率限制（防暴力破解）
- ✅ 事务管理（数据一致性）
- ✅ SQL注入防护（ORM参数化查询）

---

## ❓ 常见问题

### Q1: AI仿写失败？

**A:** 检查以下几点：
1. 是否配置了有效的API密钥（智谱AI或通义千问）
2. API密钥是否有足够的余额
3. 网络连接是否正常
4. 查看后端日志获取详细错误信息

### Q2: 语音转写不准确？

**A:** 语音转写准确率取决于：
1. 音频质量
2. 背景噪音
3. 说话人发音清晰度
4. 可以使用「手动编辑」功能修正转写结果

### Q3: 如何提高仿写质量？

**A:**
1. 使用高质量的原始文案
2. 自定义提示词模板
3. 通过对话式创作多次迭代
4. 参考「提示词管理」中的示例模板

### Q4: Cookie有什么用？

**A:** Cookie用于：
1. 访问抖音API获取视频信息
2. 下载视频和音频文件
3. Cookie会定期过期，需要更新

---

## 🎯 适用场景

### 内容创作者

- 短视频创作者需要快速仿写热门文案
- 营销人员需要批量生成创意文案
- 自媒体创作者需要灵感来源

### 团队协作

- 内容团队统一文案风格
- 提高文案创作效率
- 积累和复用优质模板

---

## 📄 License

MIT License

Copyright (c) 2026 SweetZzx

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给个Star支持一下！**

Made with ❤️ by SweetZzx

</div>
