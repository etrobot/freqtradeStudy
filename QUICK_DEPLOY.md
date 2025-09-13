# 甲骨文VPS快速部署指南

## 🚀 一键部署命令

在您的甲骨文VPS上执行以下命令：

```bash
# 1. 克隆或上传项目到VPS
# 假设您已经将项目文件上传到 ~/freqtrade-signals/

cd ~/freqtrade-signals/

# 2. 确保Traefik网络存在
docker network create traefik 2>/dev/null || true

# 3. 一键部署
chmod +x deploy.sh
./deploy.sh
```

## 📋 部署前检查清单

- [ ] 甲骨文VPS运行Ubuntu
- [ ] Docker和Docker Compose已安装
- [ ] Traefik已安装并运行
- [ ] 域名 `freq.subx.fun` 已指向VPS IP
- [ ] 防火墙允许80/443端口

## 🔧 快速验证

部署完成后，检查以下URL：

```bash
# 健康检查
curl https://freq.subx.fun/health

# API文档
open https://freq.subx.fun/docs

# 测试信号接口
curl -X POST "https://freq.subx.fun/signals" \
  -H "Content-Type: application/json" \
  -d '{
    "pair": "BTC/USDT",
    "action": "buy",
    "confidence": 0.8,
    "reason": "测试信号"
  }'
```

## 🛠️ 常用管理命令

```bash
# 查看服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看实时日志
docker-compose -f docker-compose.prod.yml logs -f

# 重启服务
docker-compose -f docker-compose.prod.yml restart

# 停止服务
docker-compose -f docker-compose.prod.yml down

# 更新并重新部署
git pull && ./deploy.sh
```

## 🔐 安全配置（可选）

### 启用API认证

1. 生成密码哈希：
```bash
htpasswd -nb admin your_password
```

2. 将结果添加到 `traefik-middleware.yml`

3. 复制中间件配置：
```bash
sudo cp traefik-middleware.yml /etc/traefik/dynamic/
sudo systemctl reload traefik
```

4. 在 `docker-compose.prod.yml` 中启用认证中间件：
```yaml
- "traefik.http.routers.signal-server.middlewares=secure-headers@file,api-auth@file"
```

## 📊 监控设置

### 查看系统资源使用
```bash
# 容器资源使用
docker stats freqtrade-signal-server

# 系统资源
htop
df -h
```

### 设置日志轮转
```bash
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

## 🚨 故障排除

### 服务无法启动
```bash
# 检查容器日志
docker-compose -f docker-compose.prod.yml logs

# 检查Traefik日志
docker logs traefik

# 检查端口占用
netstat -tlnp | grep :8000
```

### SSL证书问题
```bash
# 检查证书状态
curl -I https://freq.subx.fun

# 强制重新申请证书
docker exec traefik traefik healthcheck
```

### 域名解析问题
```bash
# 检查DNS解析
nslookup freq.subx.fun
dig freq.subx.fun

# 检查从外部访问
curl -I http://freq.subx.fun
```

## 📱 TradingView Webhook配置

在TradingView中设置Webhook URL：
```
https://freq.subx.fun/signals/webhook
```

Webhook消息格式：
```json
{
  "symbol": "{{ticker}}",
  "action": "buy",
  "price": {{close}},
  "message": "TradingView信号: {{strategy.order.action}}"
}
```

## 🔄 自动更新脚本

创建自动更新脚本：
```bash
cat > update.sh << 'EOF'
#!/bin/bash
cd ~/freqtrade-signals/
git pull
./deploy.sh
EOF

chmod +x update.sh
```

设置定时更新（可选）：
```bash
# 每天凌晨2点检查更新
echo "0 2 * * * /home/ubuntu/freqtrade-signals/update.sh" | crontab -
```