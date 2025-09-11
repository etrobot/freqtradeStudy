#!/bin/bash

# Freqtrade 外部信号系统部署脚本
# 适用于甲骨文VPS + Traefik + Let's Encrypt

set -e

echo "🚀 开始部署 Freqtrade 外部信号系统..."

# 检查必要的文件
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "❌ 错误: docker-compose.prod.yml 文件不存在"
    exit 1
fi

if [ ! -f "Dockerfile" ]; then
    echo "❌ 错误: Dockerfile 文件不存在"
    exit 1
fi

# 检查Traefik网络是否存在
if ! docker network ls | grep -q "traefik"; then
    echo "📡 创建 Traefik 网络..."
    docker network create traefik
fi

# 停止现有容器（如果存在）
echo "🛑 停止现有容器..."
docker-compose -f docker-compose.prod.yml down || true

# 构建镜像
echo "🔨 构建 Docker 镜像..."
docker-compose -f docker-compose.prod.yml build

# 启动服务
echo "🚀 启动服务..."
docker-compose -f docker-compose.prod.yml up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose -f docker-compose.prod.yml ps

# 检查健康状态
echo "🏥 检查健康状态..."
for i in {1..30}; do
    if curl -f https://freq.subx.fun/health >/dev/null 2>&1; then
        echo "✅ 服务健康检查通过!"
        break
    fi
    echo "等待服务启动... ($i/30)"
    sleep 2
done

echo "🎉 部署完成!"
echo "📊 API文档: https://freq.subx.fun/docs"
echo "🔍 健康检查: https://freq.subx.fun/health"
echo "📝 查看日志: docker-compose -f docker-compose.prod.yml logs -f"