# Douyin Spider Web

抖音UP主视频管理系统 - 关注你喜欢的UP主，自动追踪新视频发布。

## 功能特性

- **UP主管理**：添加、删除关注的UP主，支持拖拽分组
- **视频追踪**：自动爬取UP主视频，记录互动数据（点赞、评论、分享、收藏）
- **新视频提醒**：定时检查新视频，首页展示最新动态
- **分组管理**：自定义分组，拖拽UP主到不同分组
- **数据看板**：统计关注UP主数量、视频总数、新视频数
- **Cookie管理**：支持Web界面配置和验证Cookie

## 技术栈

### 后端
- **框架**: FastAPI
- **ORM**: SQLAlchemy 2.0+
- **数据库**: MySQL (PyMySQL)
- **定时任务**: APScheduler
- **日志**: loguru
- **配置管理**: pydantic-settings
- **包管理**: uv

### 前端
- **框架**: Vue 3 + TypeScript
- **UI库**: Element Plus
- **构建工具**: Vite
- **包管理**: npm

## 项目结构

```
myDouyinSpider/
├── pyproject.toml        # Python 依赖配置
├── uv.lock
├── .env.example          # 环境变量示例
├── backend/              # Python 后端
│   ├── main.py           # FastAPI 入口
│   ├── config.py         # 配置管理
│   ├── db/               # 数据库模块
│   │   ├── database.py   # 连接配置
│   │   ├── models.py     # 数据模型
│   │   └── crud.py       # CRUD 操作
│   ├── routers/          # API 路由
│   │   └── api.py        # 统一API接口
│   ├── services/         # 业务服务
│   │   └── scheduler.py  # 定时任务
│   └── lib/              # 核心库
│       └── douyin/       # 抖音API封装
└── frontend/             # Vue 前端
    ├── src/
    │   ├── views/        # 页面组件
    │   ├── components/   # 通用组件
    │   ├── services/     # API服务
    │   └── types/        # TypeScript类型
    └── package.json
```

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- MySQL 5.7+
- uv（Python包管理器）

### 1. 克隆项目

```bash
git clone git@github.com:SweetZzx/douyinSpider.git
cd douyinSpider/myDouyinSpider
```

### 2. 后端配置

```bash
# 安装 uv（如未安装）
pip install uv

# 安装依赖
uv sync

# 复制环境变量配置
cp .env.example .env

# 编辑 .env 文件，配置数据库和Cookie
# DATABASE_URL=mysql+pymysql://user:password@host:port/database
# COOKIE=你的抖音Cookie
```

### 3. 数据库配置

创建MySQL数据库：

```sql
CREATE DATABASE douyin_spider CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

表结构会在首次启动时自动创建。

### 4. 启动后端

```bash
# 开发模式
uv run python -m backend.main

# 或使用 uvicorn
uv run uvicorn backend.main:app --reload --port 77
```

### 5. 前端配置

```bash
cd frontend

# 安装依赖
npm install

# 开发模式
npm run dev

# 生产构建
npm run build
```

## 配置说明

### 环境变量 (.env)

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| COOKIE | 抖音Cookie（必需） | - |
| DATABASE_URL | MySQL连接字符串 | mysql+pymysql://root@localhost:3306/douyin_spider |
| DOWNLOAD_PATH | 下载路径 | ./downloads |
| LOG_LEVEL | 日志级别 | DEBUG |
| LOG_PATH | 日志路径 | ./logs |

### 获取抖音Cookie

1. 打开浏览器，访问 https://www.douyin.com
2. 登录你的账号
3. 按F12打开开发者工具 -> Network -> 任意请求 -> Headers
4. 复制Cookie值

## API 接口

### 基础接口

- `GET /api` - API信息
- `GET /api/health` - 健康检查

### 设置

- `GET /api/settings` - 获取设置
- `GET /api/settings/cookie/verify` - 验证Cookie
- `POST /api/settings/cookie` - 设置Cookie

### UP主管理

- `GET /api/authors` - 获取UP主列表
- `POST /api/authors` - 添加UP主
- `DELETE /api/authors/{id}` - 删除UP主
- `POST /api/authors/{id}/refresh` - 刷新UP主视频

### 分组管理

- `GET /api/groups` - 获取分组列表
- `POST /api/groups` - 创建分组
- `PUT /api/groups/{id}` - 更新分组
- `DELETE /api/groups/{id}` - 删除分组
- `PUT /api/authors/{id}/group` - 移动UP主到分组

### 视频管理

- `GET /api/videos` - 获取视频列表（支持分页和筛选）
- `GET /api/videos/new` - 获取新视频
- `POST /api/videos/check` - 手动检查新视频
- `POST /api/videos/read-all` - 标记全部已读

### 数据看板

- `GET /api/dashboard` - 获取看板数据

## 服务器部署

### 服务器信息

- **地址**: 47.110.242.66 (阿里云)
- **后端端口**: 77
- **前端端口**: 7777 (nginx代理)

### 部署命令

```bash
# 同步后端代码
scp -r backend pyproject.toml .env root@47.110.242.66:/opt/douyin-spider/

# 同步前端代码
scp -r frontend/dist/* root@47.110.242.66:/opt/douyin-spider/frontend/

# 启动后端
cd /opt/douyin-spider && source .venv/bin/activate && nohup uvicorn backend.main:app --host 0.0.0.0 --port 77 > logs/backend.log 2>&1 &

# 停止后端
pkill -f 'uvicorn.*backend.main.*port 77'

# 查看日志
tail -f /opt/douyin-spider/logs/app_*.log
```

## 开发指南

### 编码规范

- Python文件使用UTF-8编码，文件头添加 `# -*- encoding: utf-8 -*-`
- 导入顺序：标准库 -> 第三方库 -> 本地模块
- 使用loguru记录日志，不使用print()
- 异步操作使用async/await
- 前端使用Vue 3 Composition API (setup语法)

### 数据库规范

- 使用SQLAlchemy ORM，不使用原生SQL
- 模型定义在 `backend/db/models.py`
- CRUD操作在 `backend/db/crud.py`

## 注意事项

1. Cookie会过期，需要定期更新
2. 爬取频率过高可能被限制，建议使用定时任务默认间隔（30分钟）
3. 仅供学习交流，请勿用于商业用途

## License

MIT
