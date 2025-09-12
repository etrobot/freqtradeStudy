#!/usr/bin/env python3
"""
信号客户端工具
用于发送交易信号到信号服务器
"""

import requests
import json
import argparse
from datetime import datetime
from typing import Optional

class SignalClient:
    def __init__(self, server_url: str = "http://localhost:6677"):
        self.server_url = server_url.rstrip('/')
    
    def send_signal(self, pair: str, action: str, confidence: float = 0.8,
                   stop_loss: Optional[float] = None, take_profit: Optional[float] = None,
                   reason: Optional[str] = None, source: str = "manual") -> bool:
        """发送交易信号"""
        signal_data = {
            "pair": pair,
            "action": action,
            "confidence": confidence,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "reason": reason,
            "source": source,
            "timestamp": datetime.now().timestamp()
        }
        
        try:
            response = requests.post(f"{self.server_url}/signals", json=signal_data)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 信号发送成功: {result['message']}")
                return True
            else:
                print(f"❌ 信号发送失败: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False
    
    def get_signals(self, pair: Optional[str] = None) -> dict:
        """获取信号"""
        try:
            if pair:
                response = requests.get(f"{self.server_url}/signals/{pair}")
            else:
                response = requests.get(f"{self.server_url}/signals")
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ 获取信号失败: {response.text}")
                return {}
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return {}
    
    def clear_signals(self, pair: str) -> bool:
        """清除指定交易对的信号"""
        try:
            response = requests.delete(f"{self.server_url}/signals/{pair}")
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {result['message']}")
                return True
            else:
                print(f"❌ 清除失败: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description="交易信号客户端")
    parser.add_argument("--server", default="http://localhost:6677", help="信号服务器地址")
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 发送信号命令
    send_parser = subparsers.add_parser("send", help="发送交易信号")
    send_parser.add_argument("pair", help="交易对 (例: BTC/USDT)")
    send_parser.add_argument("action", choices=["buy", "sell", "hold", "exit"], help="操作类型")
    send_parser.add_argument("--confidence", type=float, default=0.8, help="信号置信度 (0.0-1.0)")
    send_parser.add_argument("--stop-loss", type=float, help="止损价格")
    send_parser.add_argument("--take-profit", type=float, help="止盈价格")
    send_parser.add_argument("--reason", help="信号原因")
    send_parser.add_argument("--source", default="manual", help="信号来源")
    
    # 获取信号命令
    get_parser = subparsers.add_parser("get", help="获取交易信号")
    get_parser.add_argument("--pair", help="指定交易对")
    
    # 清除信号命令
    clear_parser = subparsers.add_parser("clear", help="清除交易信号")
    clear_parser.add_argument("pair", help="交易对")
    
    # 快速买入/卖出命令
    buy_parser = subparsers.add_parser("buy", help="快速买入信号")
    buy_parser.add_argument("pair", help="交易对")
    buy_parser.add_argument("--price", type=float, help="当前价格")
    buy_parser.add_argument("--sl-percent", type=float, default=5.0, help="止损百分比")
    buy_parser.add_argument("--tp-percent", type=float, default=10.0, help="止盈百分比")
    
    sell_parser = subparsers.add_parser("sell", help="快速卖出信号")
    sell_parser.add_argument("pair", help="交易对")
    sell_parser.add_argument("--price", type=float, help="当前价格")
    sell_parser.add_argument("--sl-percent", type=float, default=5.0, help="止损百分比")
    sell_parser.add_argument("--tp-percent", type=float, default=10.0, help="止盈百分比")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    client = SignalClient(args.server)
    
    if args.command == "send":
        client.send_signal(
            pair=args.pair,
            action=args.action,
            confidence=args.confidence,
            stop_loss=args.stop_loss,
            take_profit=args.take_profit,
            reason=args.reason,
            source=args.source
        )
    
    elif args.command == "get":
        signals = client.get_signals(args.pair)
        print(json.dumps(signals, indent=2, ensure_ascii=False))
    
    elif args.command == "clear":
        client.clear_signals(args.pair)
    
    elif args.command == "buy":
        stop_loss = None
        take_profit = None
        
        if args.price:
            stop_loss = args.price * (1 - args.sl_percent / 100)
            take_profit = args.price * (1 + args.tp_percent / 100)
        
        client.send_signal(
            pair=args.pair,
            action="buy",
            confidence=0.8,
            stop_loss=stop_loss,
            take_profit=take_profit,
            reason=f"快速买入信号 (止损:{args.sl_percent}%, 止盈:{args.tp_percent}%)",
            source="quick_buy"
        )
    
    elif args.command == "sell":
        stop_loss = None
        take_profit = None
        
        if args.price:
            stop_loss = args.price * (1 + args.sl_percent / 100)
            take_profit = args.price * (1 - args.tp_percent / 100)
        
        client.send_signal(
            pair=args.pair,
            action="sell",
            confidence=0.8,
            stop_loss=stop_loss,
            take_profit=take_profit,
            reason=f"快速卖出信号 (止损:{args.sl_percent}%, 止盈:{args.tp_percent}%)",
            source="quick_sell"
        )

if __name__ == "__main__":
    main()