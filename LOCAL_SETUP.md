# Windows 本地运行指南

本项目已统一为 Docker Compose 部署。MySQL、Redis、MinIO、Milvus、后端和前端数据均落在项目目录的 `data/`、`log/` 中。建议在 Docker Desktop 中把镜像磁盘放到空间充足的非系统盘。

说明：MinIO 官方社区版从 2026 年起不再发布可直接拉取的镜像，Compose 已固定到由未修改 AGPLv3 社区源码构建的兼容镜像及其 SHA-256 摘要，避免误用需要商业许可证、会拒绝 S3 请求的 AIStor 镜像。

## 必装软件

1. **Git for Windows 2.40+**：用于拉取和管理代码。
2. **Docker Desktop 4.x（WSL 2 后端）**：用于运行全部项目服务。安装时启用 WSL 2，并确认 Docker Desktop 有足够的磁盘空间。

只使用容器运行时，不需要在 Windows 宿主机另外安装 Python、Node.js、MySQL、Redis、MinIO 或 Milvus。Python 3.12、Node.js 24、数据库及 OCR 工具均由镜像提供。

## 首次配置

在 PowerShell 中进入项目：

```powershell
git clone https://github.com/baixigua/group-9-rag-system.git
Set-Location group-9-rag-system
```

从示例创建本地配置，并用编辑器打开 `.env`。每位部署者必须填写自己的阿里云百炼 API Key，不要把密钥发到聊天、截图或提交到 Git：

```powershell
Copy-Item .env.example .env
```

```dotenv
ALIYUN_ACCESS_KEY_SECRET=你的百炼APIKey
```

`.env` 已被 Git 忽略。首次启动前还必须把 MySQL、JWT 和 MinIO 的 `change-me-*` 占位值换成自己的强密码。

只有直连百炼失败时才需要代理。本机使用 Clash Verge 时保持“规则模式”、系统代理开启，并确认混合端口为 `7897`，然后在 `.env` 中填写：

```dotenv
OUTBOUND_PROXY=http://host.docker.internal:7897
```

## 启动

确认 Docker Desktop 已启动，然后执行：

```powershell
docker compose config --quiet
docker compose up -d --build
docker compose ps
```

首次构建需下载镜像和 Python/Node 依赖，耗时取决于网络。以后日常启动只需：

```powershell
docker compose up -d
```

## 访问地址

| 功能 | 地址 |
|---|---|
| Web 前端 | http://127.0.0.1:3000 |
| FastAPI 文档 | http://127.0.0.1:8000/docs |
| Django API 文档 | http://127.0.0.1:8001/docs/ |
| MinIO 控制台 | http://127.0.0.1:9001 |
| Attu（Milvus 管理） | http://127.0.0.1:8080 |
| Portainer | https://127.0.0.1:9443 |

项目 MySQL 对宿主机使用 `127.0.0.1:3307`，不会占用本机现有 MySQL 的 3306。容器端口仅绑定到 `127.0.0.1`，不会直接暴露给局域网。

## 用户使用流程

1. 浏览器打开 http://127.0.0.1:3000 。
2. 首次使用点击“注册”，填写用户名、邮箱、手机号和密码，然后登录。
3. 打开“知识库”，点击“创建知识库”，普通用户选择个人（私有）范围。
4. 进入知识库详情后点击“上传”，可上传 TXT、Markdown、PDF、DOCX、PPTX 和常见图片；图片及扫描 PDF 会执行 OCR。
5. 等待页面提示上传成功后，可在知识库详情中直接检索，也可打开“AI 对话”，选择知识库后提问。
6. 回答下方会显示引用来源；可在知识库页面查看或删除已上传文档。

## 检查和排错

```powershell
docker compose ps
docker compose logs --tail 100 api
docker compose logs --tail 100 django
docker compose logs --tail 100 milvus
```

健康检查：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health/ready
```

若修改了依赖或 Dockerfile，重新构建对应服务：

```powershell
docker compose up -d --build api django frontend
```

## 停止与清理

仅停止服务、保留数据：

```powershell
docker compose stop
```

移除容器但保留 `data/` 中的数据：

```powershell
docker compose down
```

项目数据使用项目目录下的 `data/` 挂载。不要随意删除该目录，否则数据库、对象文件和向量数据会丢失。
