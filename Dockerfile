FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY pyproject.toml uv.lock ./

# 安装uv包管理器
RUN pip install uv

# 安装Python依赖
RUN uv sync --frozen

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p logs user_data

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:6677/health || exit 1

# 默认命令
CMD ["python", "signal_server.py"]