#!/usr/bin/env python3
"""
TradingView Webhook 示例
展示如何从TradingView接收信号并转发给freqtrade
"""

from flask import Flask, request, jsonify
import requests
import json
import logging
from datetime import datetime

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# 配置
SIGNAL_SERVER_URL = "http://localhost:8000"
WEBHOOK_SECRET = "your_webhook_secret_here"  # 用于验证webhook的密钥

@app.route('/webhook/tradingview', methods=['POST'])
def tradingview_webhook():
    """
    接收TradingView的webhook信号
    
    TradingView Pine Script 示例:
    
    //@version=5
    strategy("External Signal Strategy", overlay=true)
    
    // 策略逻辑
    longCondition = ta.crossover(ta.sma(close, 14), ta.sma(close, 28))
    shortCondition = ta.crossunder(ta.sma(close, 14), ta.sma(close, 28))
    
    if (longCondition)
        strategy.entry("Long", strategy.long)
        // 发送webhook
        alert('{"action": "buy", "symbol": "{{ticker}}", "price": {{close}}, "message": "SMA交叉买入信号"}', alert.freq_once_per_bar)
    
    if (shortCondition)
        strategy.entry("Short", strategy.short)
        // 发送webhook
        alert('{"action": "sell", "symbol": "{{ticker}}", "price": {{close}}, "message": "SMA交叉卖出信号"}', alert.freq_once_per_bar)
    """
    
    try:
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data received"}), 400
        
        # 验证webhook密钥（可选）
        webhook_key = request.headers.get('X-Webhook-Key')
        if WEBHOOK_SECRET and webhook_key != WEBHOOK_SECRET:
            return jsonify({"error": "Invalid webhook key"}), 401
        
        # 记录接收到的数据
        app.logger.info(f"收到TradingView信号: {data}")
        
        # 解析TradingView数据
        symbol = data.get('symbol', '').upper()
        action = data.get('action', '').lower()
        price = float(data.get('price', 0))
        message = data.get('message', 'TradingView信号')
        
        # 转换symbol格式
        if 'USDT' in symbol:
            pair = symbol.replace('USDT', '/USDT')
        elif 'USD' in symbol:
            pair = symbol.replace('USD', '/USD')
        else:
            pair = symbol
        
        # 计算止损止盈（可根据需要调整）
        stop_loss = None
        take_profit = None
        
        if action == 'buy' and price > 0:
            stop_loss = price * 0.95  # 5% 止损
            take_profit = price * 1.10  # 10% 止盈
        elif action == 'sell' and price > 0:
            stop_loss = price * 1.05  # 5% 止损
            take_profit = price * 0.90  # 10% 止盈
        
        # 构造信号数据
        signal_data = {
            "pair": pair,
            "action": action,
            "confidence": 0.8,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "reason": message,
            "source": "tradingview",
            "timestamp": datetime.now().timestamp()
        }
        
        # 发送到信号服务器
        response = requests.post(
            f"{SIGNAL_SERVER_URL}/signals",
            json=signal_data,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            app.logger.info(f"信号转发成功: {result['message']}")
            return jsonify({
                "success": True,
                "message": "Signal processed successfully",
                "signal_id": result.get('signal_id')
            })
        else:
            app.logger.error(f"信号转发失败: {response.text}")
            return jsonify({"error": "Failed to forward signal"}), 500
            
    except Exception as e:
        app.logger.error(f"处理webhook失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/webhook/test', methods=['POST'])
def test_webhook():
    """测试webhook端点"""
    data = request.get_json()
    app.logger.info(f"测试webhook收到数据: {data}")
    return jsonify({"success": True, "received_data": data})

@app.route('/health')
def health():
    """健康检查"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    print("启动TradingView Webhook服务器...")
    print("Webhook URL: http://localhost:5000/webhook/tradingview")
    print("测试URL: http://localhost:5000/webhook/test")
    
    app.run(host='0.0.0.0', port=5000, debug=True)