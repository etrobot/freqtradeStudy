FROM python:3.13-slim

WORKDIR /app

# 环境优化
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# 仅安装运行时所需的系统依赖（无需构建 TA-Lib）
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 安装最小化 Python 依赖，仅用于运行 FastAPI 信号服务器
# 注意：Freqtrade 将在独立容器中使用官方镜像运行，不在本镜像中安装
RUN pip install --no-cache-dir \
    fastapi==0.116.1 \
    uvicorn==0.35.0 \
    pydantic>=2,<3

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p logs user_data

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 默认命令
CMD ["python", "signal_server.py"]
