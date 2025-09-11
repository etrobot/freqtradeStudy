# Freqtrade 外部信号系统

这个项目将freqtrade改造为接收外部买卖信号的自动交易系统。

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装freqtrade
pip install freqtrade

# 安装额外依赖
pip install fastapi uvicorn flask requests
```

### 2. 启动信号服务器

```bash
# 启动信号接收服务器
python signal_server.py
```

服务器将在 `http://localhost:8000` 启动，API文档: `http://localhost:8000/docs`

### 3. 启动freqtrade

```bash
# 使用外部信号配置启动freqtrade
freqtrade trade --config user_data/config_external_signals.json --strategy ExternalSignalStrategy
```

### 4. 发送交易信号

#### 方法1: 使用命令行工具

```bash
# 发送买入信号
python signal_client.py buy BTC/USDT --price 45000

# 发送卖出信号
python signal_client.py sell ETH/USDT --price 2800

# 发送自定义信号
python signal_client.py send BTC/USDT buy --confidence 0.9 --stop-loss 42000 --take-profit 48000 --reason "突破关键阻力位"

# 查看所有信号
python signal_client.py get

# 查看特定交易对信号
python signal_client.py get --pair BTC/USDT

# 清除信号
python signal_client.py clear BTC/USDT
```

#### 方法2: 使用API

```bash
# 发送买入信号
curl -X POST "http://localhost:8000/signals" \
  -H "Content-Type: application/json" \
  -d '{
    "pair": "BTC/USDT",
    "action": "buy",
    "confidence": 0.85,
    "stop_loss": 42000,
    "take_profit": 48000,
    "reason": "技术分析买入信号"
  }'

# 获取信号
curl "http://localhost:8000/signals/BTC/USDT"
```

#### 方法3: TradingView Webhook

1. 启动webhook服务器:
```bash
python tradingview_webhook.py
```

2. 在TradingView中设置Webhook URL: `http://your-server:5000/webhook/tradingview`

3. Pine Script示例:
```pinescript
//@version=5
strategy("External Signal", overlay=true)

longCondition = ta.crossover(ta.sma(close, 14), ta.sma(close, 28))
if (longCondition)
    strategy.entry("Long", strategy.long)
    alert('{"action": "buy", "symbol": "{{ticker}}", "price": {{close}}}', alert.freq_once_per_bar)
```

## 📁 文件结构

```
├── user_data/
│   ├── strategies/
│   │   └── ExternalSignalStrategy.py    # 外部信号策略
│   ├── config_external_signals.json    # 外部信号配置
│   └── external_signals.json           # 信号存储文件
├── signal_server.py                     # 信号接收服务器
├── signal_client.py                     # 信号发送客户端
├── tradingview_webhook.py              # TradingView webhook服务器
└── README_EXTERNAL_SIGNALS.md          # 本文档
```

## 🔧 配置说明

### 策略配置

在 `user_data/strategies/ExternalSignalStrategy.py` 中可以配置:

- `signal_file_path`: 信号文件路径
- `signal_api_url`: 信号API地址
- `signal_check_interval`: 检查信号间隔（秒）
- `minimal_roi`: ROI设置
- `stoploss`: 默认止损

### 信号格式

```json
{
  "pair": "BTC/USDT",
  "action": "buy",           // buy, sell, hold, exit
  "confidence": 0.85,        // 0.0 - 1.0
  "stop_loss": 42000,        // 可选
  "take_profit": 48000,      // 可选
  "reason": "突破阻力位",     // 可选
  "source": "technical",     // 可选
  "timestamp": 1694567890    // 自动生成
}
```

## 🎯 使用场景

### 1. 技术分析信号
```bash
python signal_client.py send BTC/USDT buy \
  --confidence 0.9 \
  --reason "RSI超卖反弹" \
  --source "technical_analysis"
```

### 2. 基本面分析信号
```bash
python signal_client.py send ETH/USDT buy \
  --confidence 0.7 \
  --reason "ETF批准利好消息" \
  --source "fundamental_analysis"
```

### 3. 情绪分析信号
```bash
python signal_client.py send BTC/USDT sell \
  --confidence 0.6 \
  --reason "市场恐慌情绪" \
  --source "sentiment_analysis"
```

### 4. 紧急退出
```bash
python signal_client.py send BTC/USDT exit \
  --confidence 1.0 \
  --reason "紧急止损"
```

## 🔍 监控和调试

### 查看freqtrade日志
```bash
tail -f user_data/logs/freqtrade.log
```

### 查看信号服务器日志
信号服务器会在控制台输出接收到的信号信息。

### 检查信号文件
```bash
cat user_data/external_signals.json | jq
```

## ⚠️ 注意事项

1. **测试环境**: 建议先在 `dry_run: true` 模式下测试
2. **信号时效**: 信号默认5分钟内有效
3. **风险管理**: 设置合理的止损和仓位大小
4. **网络延迟**: 考虑信号传输和执行的延迟
5. **备份策略**: 保持传统技术指标作为备用

## 🔒 安全建议

1. 使用HTTPS和API密钥验证
2. 限制信号服务器的访问IP
3. 定期更新webhook密钥
4. 监控异常交易活动

## 🚀 高级功能

### 多信号源融合
可以修改策略来融合多个信号源:
- 技术分析信号
- 基本面分析信号
- 情绪分析信号
- 新闻事件信号

### 信号权重系统
根据信号来源和历史准确率分配权重。

### 自动止损调整
根据市场波动性动态调整止损位置。

## 📞 支持

如有问题，请查看:
1. Freqtrade官方文档: https://www.freqtrade.io/
2. 项目日志文件
3. API文档: http://localhost:8000/docs