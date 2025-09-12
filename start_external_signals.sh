#!/bin/bash

# Freqtrade 外部信号系统启动脚本

echo "🚀 启动 Freqtrade 外部信号系统"
echo "================================"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 检查必要文件
if [ ! -f "user_data/strategies/ExternalSignalStrategy.py" ]; then
    echo "❌ 策略文件不存在"
    exit 1
fi

if [ ! -f "user_data/config_external_signals.json" ]; then
    echo "❌ 配置文件不存在"
    exit 1
fi

# 创建日志目录
mkdir -p user_data/logs

# 启动信号服务器（后台运行）
echo "📡 启动信号服务器..."
python3 signal_server.py > user_data/logs/signal_server.log 2>&1 &
SIGNAL_SERVER_PID=$!
echo "信号服务器 PID: $SIGNAL_SERVER_PID"

# 等待信号服务器启动
sleep 3

# 检查信号服务器是否启动成功
if curl -s http://localhost:6677/health > /dev/null; then
    echo "✅ 信号服务器启动成功"
    echo "📊 API文档: http://localhost:6677/docs"
else
    echo "❌ 信号服务器启动失败"
    kill $SIGNAL_SERVER_PID 2>/dev/null
    exit 1
fi

# 可选：启动TradingView Webhook服务器
read -p "🔗 是否启动TradingView Webhook服务器? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔗 启动TradingView Webhook服务器..."
    python3 tradingview_webhook.py > user_data/logs/webhook_server.log 2>&1 &
    WEBHOOK_PID=$!
    echo "Webhook服务器 PID: $WEBHOOK_PID"
    sleep 2
    echo "✅ Webhook服务器启动成功"
    echo "🔗 Webhook URL: http://localhost:5000/webhook/tradingview"
fi

# 启动模式选择
echo ""
echo "选择启动模式:"
echo "1) 模拟交易 (推荐)"
echo "2) 实盘交易 (谨慎使用)"
read -p "请选择 (1-2): " -n 1 -r
echo

case $REPLY in
    1)
        echo "🧪 启动模拟交易模式..."
        MODE="dry_run"
        ;;
    2)
        echo "⚠️  启动实盘交易模式..."
        echo "请确保已配置正确的API密钥!"
        read -p "确认继续? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "取消启动"
            kill $SIGNAL_SERVER_PID 2>/dev/null
            kill $WEBHOOK_PID 2>/dev/null
            exit 0
        fi
        MODE="live"
        ;;
    *)
        echo "无效选择，使用模拟模式"
        MODE="dry_run"
        ;;
esac

# 启动freqtrade
echo "🤖 启动Freqtrade..."
echo "配置文件: user_data/config_external_signals.json"
echo "策略: ExternalSignalStrategy"
echo "模式: $MODE"
echo ""

if [ "$MODE" = "dry_run" ]; then
    freqtrade trade \
        --config user_data/config_external_signals.json \
        --strategy ExternalSignalStrategy \
        --logfile user_data/logs/freqtrade.log
else
    # 实盘交易需要额外确认
    echo "⚠️  实盘交易模式 - 最后确认"
    echo "1. 已配置正确的交易所API密钥"
    echo "2. 已设置合理的仓位大小"
    echo "3. 已设置止损保护"
    read -p "确认所有设置正确? (yes/no): " -r
    if [[ $REPLY = "yes" ]]; then
        freqtrade trade \
            --config user_data/config_external_signals.json \
            --strategy ExternalSignalStrategy \
            --logfile user_data/logs/freqtrade.log
    else
        echo "取消启动"
    fi
fi

# 清理后台进程
echo ""
echo "🛑 停止服务..."
kill $SIGNAL_SERVER_PID 2>/dev/null
kill $WEBHOOK_PID 2>/dev/null
echo "✅ 所有服务已停止"