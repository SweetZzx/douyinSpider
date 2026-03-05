# Claude Code 项目配置

## 项目概述

抖音UP主视频查询Web应用，前后端分离架构。

## Git 仓库

- **SSH地址**: git@github.com:SweetZzx/douyinSpider.git
- **HTTPS地址**: https://github.com/SweetZzx/douyinSpider.git
- **Web地址**: https://github.com/SweetZzx/douyinSpider

### Git 工作流程

```bash
# 查看当前状态
git status

# 添加文件到暂存区
git add <file>
git add .  # 添加所有文件

# 提交变更
git commit -m "描述变更内容"

# 推送到远程仓库
git push origin main

# 拉取远程更新
git pull origin main

# 查看分支
git branch

# 切换分支
git checkout <branch>
```

## 技术栈（严禁更改）

### 后端
- **框架**: FastAPI
- **ORM**: SQLAlchemy 2.0+
- **数据库**: MySQL (使用 PyMySQL 驱动)
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
├── pyproject.toml        # Python 依赖配置（放在根目录）
├── uv.lock
├── .env                  # 环境变量
├── .venv/                # Python 虚拟环境
├── backend/              # Python 后端
│   ├── main.py           # FastAPI 入口
│   ├── config.py         # 配置管理
│   ├── db/               # 数据库模块
│   │   ├── database.py   # 连接配置
│   │   ├── models.py     # 数据模型
│   │   └── crud.py       # CRUD 操作
│   ├── routers/          # API 路由
│   ├── services/         # 业务服务
│   └── lib/              # 核心库（抖音API等）
└── frontend/             # Vue 前端
    ├── src/
    └── package.json
```

## 编码规范

### Python
- 文件编码: UTF-8，文件头使用 `# -*- encoding: utf-8 -*-`
- 导入顺序: 标准库 → 第三方库 → 本地模块
- 使用 loguru 进行日志记录，不用 logging
- 异步操作使用 async/await

### 前端
- 使用 Vue 3 Composition API (setup 语法)
- 使用 TypeScript
- 组件放在 `src/components/`
- 页面放在 `src/views/`

## 数据库规范

- **必须使用 MySQL**，禁止使用 SQLite 或其他数据库
- 数据库连接字符串格式: `mysql+pymysql://user:password@host:port/database`
- 模型定义在 `backend/db/models.py`
- CRUD 操作在 `backend/db/crud.py`
- 使用 SQLAlchemy ORM，不使用原生 SQL

## 环境变量

配置文件: `.env`

关键配置:
- `DATABASE_URL`: MySQL 连接字符串
- `COOKIE`: 抖音 Cookie
- `LOG_LEVEL`: 日志级别

## API 规范

- 路由前缀: `/api`
- 响应格式: JSON
- 错误处理: 统一返回 `{"error": "message"}` 格式

## 运行命令

```bash
# 后端开发
uv run python -m backend.main

# 前端开发
cd frontend && npm run dev
```

## 服务器部署信息

### 服务器配置
- **地址**: 47.110.242.66 (阿里云)
- **用户**: root
- **项目路径**: /opt/douyin-spider
- **后端端口**: 77
- **前端端口**: 7777 (nginx 代理)
- **日志路径**: /opt/douyin-spider/logs/

### 常用命令

```bash
# 启动后端
cd /opt/douyin-spider && source .venv/bin/activate && nohup uvicorn backend.main:app --host 0.0.0.0 --port 77 > logs/backend.log 2>&1 &

# 停止后端
pkill -f 'uvicorn.*backend.main.*port 77'

# 重启后端
pkill -f 'uvicorn.*backend.main.*port 77' && cd /opt/douyin-spider && source .venv/bin/activate && nohup uvicorn backend.main:app --host 0.0.0.0 --port 77 > logs/backend.log 2>&1 &

# 查看后端日志
tail -f /opt/douyin-spider/logs/backend.log

# 查看应用日志
tail -f /opt/douyin-spider/logs/app_*.log

# 查看后端进程
ps aux | grep uvicorn | grep 77
```

### 部署同步

```bash
# 同步后端代码
scp -r backend pyproject.toml .env root@47.110.242.66:/opt/douyin-spider/

# 同步前端代码
scp -r frontend/dist/* root@47.110.242.66:/opt/douyin-spider/frontend/
```

### Nginx 配置
- 配置文件: /etc/nginx/conf.d/douyin-spider.conf

## 禁止事项

1. **不要**将数据库从 MySQL 改为 SQLite 或其他数据库
2. **不要**引入新的 ORM 框架（如 Django ORM、Peewee 等）
3. **不要**更改项目结构（如移动 pyproject.toml 到 backend 目录）
4. **不要**在前端使用 Options API，使用 Composition API
5. **不要**使用 print() 进行日志输出，使用 loguru
