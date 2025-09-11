# 甲骨文VPS部署指南

## 前置条件

1. **甲骨文VPS** 运行 Ubuntu
2. **Traefik** 已安装并配置
3. **Docker** 和 **Docker Compose** 已安装
4. **域名** `freq.subx.fun` 已指向您的VPS IP

## 部署步骤

### 1. 准备项目文件

将项目文件上传到VPS：

```bash
# 在本地打包项目
tar -czf freqtrade-signals.tar.gz .

# 上传到VPS
scp freqtrade-signals.tar.gz user@your-vps-ip:~/

# 在VPS上解压
ssh user@your-vps-ip
cd ~
tar -xzf freqtrade-signals.tar.gz
cd freqtrade-signals/
```

### 2. 配置Traefik中间件（可选）

如果您想添加安全头和限流，将中间件配置复制到Traefik配置目录：

```bash
sudo cp traefik-middleware.yml /etc/traefik/dynamic/
sudo systemctl reload traefik
```

### 3. 配置环境

检查并修改配置文件：

```bash
# 检查信号服务器配置
cat user_data/config_external_signals.json

# 如需要，修改端口和其他设置
nano user_data/config_external_signals.json
```

### 4. 部署服务

运行部署脚本：

```bash
./deploy.sh
```

### 5. 验证部署

部署完成后，访问以下URL验证：

- **API文档**: https://freq.subx.fun/docs
- **健康检查**: https://freq.subx.fun/health
- **信号列表**: https://freq.subx.fun/signals

## 管理命令

### 查看日志
```bash
docker-compose -f docker-compose.prod.yml logs -f
```

### 重启服务
```bash
docker-compose -f docker-compose.prod.yml restart
```

### 停止服务
```bash
docker-compose -f docker-compose.prod.yml down
```

### 更新部署
```bash
git pull  # 如果使用Git
./deploy.sh
```

## 安全建议

### 1. 防火墙配置

确保只开放必要端口：

```bash
# 检查当前防火墙状态
sudo ufw status

# 如果需要，只允许HTTP/HTTPS和SSH
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. 启用API认证（可选）

如果需要保护API，可以在Traefik中启用基本认证：

```bash
# 生成密码哈希
htpasswd -nb admin your_password

# 将结果添加到 traefik-middleware.yml 的 api-auth 部分
```

然后在 `docker-compose.prod.yml` 中添加认证中间件：

```yaml
labels:
  # ... 其他标签
  - "traefik.http.routers.signal-server.middlewares=secure-headers@file,api-auth@file"
```

### 3. 监控和日志

设置日志轮转：

```bash
# 创建日志轮转配置
sudo tee /etc/logrotate.d/docker-containers << EOF
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    size 10M
    missingok
    delaycompress
    copytruncate
}
EOF
```

## 故障排除

### 常见问题

1. **容器无法启动**
   ```bash
   docker-compose -f docker-compose.prod.yml logs
   ```

2. **Traefik无法路由**
   - 检查域名DNS解析
   - 确认Traefik网络存在
   - 查看Traefik日志

3. **SSL证书问题**
   - 确认Let's Encrypt配置正确
   - 检查域名可达性
   - 查看Traefik证书日志

### 健康检查失败

如果健康检查失败，检查：

```bash
# 检查容器内部健康状态
docker exec freqtrade-signal-server curl -f http://localhost:8000/health

# 检查端口绑定
docker port freqtrade-signal-server
```

## 性能优化

### 1. 资源限制

在 `docker-compose.prod.yml` 中添加资源限制：

```yaml
services:
  signal-server:
    # ... 其他配置
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
```

### 2. 缓存优化

考虑添加Redis缓存来提高性能：

```yaml
services:
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    networks:
      - traefik
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

## 备份策略

定期备份重要数据：

```bash
# 备份用户数据
tar -czf backup-$(date +%Y%m%d).tar.gz user_data/

# 备份到远程位置
rsync -av user_data/ user@backup-server:/backups/freqtrade-signals/
```