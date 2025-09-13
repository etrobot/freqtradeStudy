#!/usr/bin/env python3
"""
信号系统测试脚本
用于测试外部信号系统的各种功能
"""

import time
import requests
import json
from datetime import datetime
from signal_client import SignalClient

def test_signal_server():
    """测试信号服务器"""
    print("🧪 测试信号服务器连接...")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ 信号服务器连接正常")
            return True
        else:
            print("❌ 信号服务器响应异常")
            return False
    except Exception as e:
        print(f"❌ 无法连接信号服务器: {e}")
        return False

def test_signal_flow():
    """测试完整的信号流程"""
    print("\n🔄 测试信号流程...")
    
    client = SignalClient()
    
    # 测试数据
    test_pairs = ["BTC/USDT", "ETH/USDT"]
    test_actions = ["buy", "sell", "hold"]
    
    for pair in test_pairs:
        for action in test_actions:
            print(f"📤 发送 {action} 信号给 {pair}")
            
            success = client.send_signal(
                pair=pair,
                action=action,
                confidence=0.8,
                stop_loss=45000 if action == "buy" else 47000,
                take_profit=50000 if action == "buy" else 43000,
                reason=f"测试{action}信号",
                source="test"
            )
            
            if success:
                print(f"✅ {pair} {action} 信号发送成功")
            else:
                print(f"❌ {pair} {action} 信号发送失败")
            
            time.sleep(1)  # 避免过快发送
    
    # 测试获取信号
    print("\n📥 测试获取信号...")
    for pair in test_pairs:
        signals = client.get_signals(pair)
        if signals:
            print(f"✅ 获取到 {pair} 的信号")
            print(f"   最新动作: {signals.get('action', 'unknown')}")
        else:
            print(f"❌ 未获取到 {pair} 的信号")

def test_webhook():
    """测试webhook功能"""
    print("\n🔗 测试Webhook功能...")
    
    # 模拟TradingView webhook数据
    webhook_data = {
        "symbol": "BTCUSDT",
        "action": "buy",
        "price": 45000,
        "message": "测试webhook信号"
    }
    
    try:
        response = requests.post(
            "http://localhost:5000/webhook/test",
            json=webhook_data,
            timeout=5
        )
        
        if response.status_code == 200:
            print("✅ Webhook测试成功")
            result = response.json()
            print(f"   返回数据: {result}")
        else:
            print("❌ Webhook测试失败")
            
    except Exception as e:
        print(f"❌ Webhook连接失败: {e}")
        print("   请确保webhook服务器已启动")

def test_signal_validation():
    """测试信号验证"""
    print("\n🔍 测试信号验证...")
    
    client = SignalClient()
    
    # 测试无效信号
    invalid_tests = [
        {"pair": "INVALID", "action": "invalid_action"},
        {"pair": "BTC/USDT", "action": "buy", "confidence": 1.5},  # 超出范围
        {"pair": "BTC/USDT", "action": "buy", "confidence": -0.1},  # 负数
    ]
    
    for test in invalid_tests:
        print(f"📤 测试无效信号: {test}")
        success = client.send_signal(**test)
        if not success:
            print("✅ 无效信号被正确拒绝")
        else:
            print("❌ 无效信号被错误接受")

def performance_test():
    """性能测试"""
    print("\n⚡ 性能测试...")
    
    client = SignalClient()
    
    start_time = time.time()
    success_count = 0
    total_tests = 10
    
    for i in range(total_tests):
        success = client.send_signal(
            pair="BTC/USDT",
            action="buy",
            confidence=0.8,
            reason=f"性能测试 #{i+1}",
            source="performance_test"
        )
        if success:
            success_count += 1
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"📊 性能测试结果:")
    print(f"   总测试数: {total_tests}")
    print(f"   成功数: {success_count}")
    print(f"   成功率: {success_count/total_tests*100:.1f}%")
    print(f"   总耗时: {duration:.2f}秒")
    print(f"   平均延迟: {duration/total_tests*1000:.1f}ms")

def cleanup_test_data():
    """清理测试数据"""
    print("\n🧹 清理测试数据...")
    
    client = SignalClient()
    test_pairs = ["BTC/USDT", "ETH/USDT"]
    
    for pair in test_pairs:
        success = client.clear_signals(pair)
        if success:
            print(f"✅ 清理 {pair} 的测试信号")
        else:
            print(f"❌ 清理 {pair} 失败")

def main():
    """主测试函数"""
    print("🚀 Freqtrade 外部信号系统测试")
    print("=" * 40)
    
    # 基础连接测试
    if not test_signal_server():
        print("❌ 信号服务器未启动，请先运行: python signal_server.py")
        return
    
    # 运行所有测试
    test_signal_flow()
    test_webhook()
    test_signal_validation()
    performance_test()
    
    # 询问是否清理测试数据
    response = input("\n🗑️  是否清理测试数据? (y/n): ")
    if response.lower() == 'y':
        cleanup_test_data()
    
    print("\n✅ 所有测试完成!")
    print("\n📋 下一步:")
    print("1. 启动freqtrade: bash start_external_signals.sh")
    print("2. 发送真实信号: python signal_client.py buy BTC/USDT --price 45000")
    print("3. 监控交易: tail -f user_data/logs/freqtrade.log")

if __name__ == "__main__":
    main()