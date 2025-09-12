#!/usr/bin/env python3
"""
外部信号服务器
提供REST API接口接收和管理交易信号
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
import json
import uvicorn
from datetime import datetime
from pathlib import Path

app = FastAPI(title="Trading Signal Server", version="1.0.0")

# 信号数据模型
class TradingSignal(BaseModel):
    pair: str
    action: str  # buy, sell, hold, exit
    confidence: float  # 0.0 - 1.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    reason: Optional[str] = None
    source: Optional[str] = None
    timestamp: Optional[float] = None

class SignalResponse(BaseModel):
    success: bool
    message: str
    signal_id: Optional[str] = None

# 信号存储
SIGNALS_FILE = "user_data/external_signals.json"

def load_signals() -> Dict:
    """加载信号文件"""
    try:
        if Path(SIGNALS_FILE).exists():
            with open(SIGNALS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"加载信号文件失败: {e}")
    return {}

def save_signals(signals: Dict) -> bool:
    """保存信号到文件"""
    try:
        # 确保目录存在
        Path(SIGNALS_FILE).parent.mkdir(parents=True, exist_ok=True)
        
        with open(SIGNALS_FILE, 'w') as f:
            json.dump(signals, f, indent=2)
        return True
    except Exception as e:
        print(f"保存信号文件失败: {e}")
        return False

@app.get("/")
async def root():
    return {"message": "Trading Signal Server", "version": "1.0.0"}

@app.get("/signals")
async def get_all_signals():
    """获取所有信号"""
    signals = load_signals()
    return {"signals": signals}

@app.get("/signals/{pair}")
async def get_pair_signals(pair: str):
    """获取特定交易对的信号"""
    signals = load_signals()
    pair_signals = signals.get(pair, [])
    
    if not pair_signals:
        raise HTTPException(status_code=404, detail=f"No signals found for {pair}")
    
    # 返回最新的信号
    latest_signal = max(pair_signals, key=lambda x: x.get('timestamp', 0))
    return latest_signal

@app.post("/signals", response_model=SignalResponse)
async def add_signal(signal: TradingSignal):
    """添加新的交易信号"""
    try:
        # 设置时间戳
        if signal.timestamp is None:
            signal.timestamp = datetime.now().timestamp()
        
        # 验证信号
        if signal.action not in ['buy', 'sell', 'hold', 'exit']:
            raise HTTPException(status_code=400, detail="Invalid action. Must be: buy, sell, hold, exit")
        
        if not (0.0 <= signal.confidence <= 1.0):
            raise HTTPException(status_code=400, detail="Confidence must be between 0.0 and 1.0")
        
        # 加载现有信号
        signals = load_signals()
        
        # 添加新信号
        if signal.pair not in signals:
            signals[signal.pair] = []
        
        signals[signal.pair].append(signal.dict())
        
        # 保持每个交易对最多10个信号
        signals[signal.pair] = signals[signal.pair][-10:]
        
        # 保存信号
        if save_signals(signals):
            signal_id = f"{signal.pair}_{int(signal.timestamp)}"
            return SignalResponse(
                success=True,
                message=f"Signal added successfully for {signal.pair}",
                signal_id=signal_id
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to save signal")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/signals/{pair}")
async def clear_pair_signals(pair: str):
    """清除特定交易对的所有信号"""
    signals = load_signals()
    
    if pair in signals:
        del signals[pair]
        if save_signals(signals):
            return {"success": True, "message": f"Cleared all signals for {pair}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save changes")
    else:
        raise HTTPException(status_code=404, detail=f"No signals found for {pair}")

@app.post("/signals/webhook")
async def webhook_signal(data: dict):
    """
    Webhook接口，接收来自TradingView等平台的信号
    
    预期格式:
    {
        "symbol": "BTCUSDT",
        "action": "buy",
        "price": 45000,
        "stop_loss": 42000,
        "take_profit": 48000,
        "message": "突破关键阻力位"
    }
    """
    try:
        # 转换symbol格式 (BTCUSDT -> BTC/USDT)
        symbol = data.get('symbol', '').upper()
        if 'USDT' in symbol:
            pair = symbol.replace('USDT', '/USDT')
        elif 'USD' in symbol:
            pair = symbol.replace('USD', '/USD')
        else:
            pair = symbol
        
        # 创建信号对象
        signal = TradingSignal(
            pair=pair,
            action=data.get('action', 'hold').lower(),
            confidence=data.get('confidence', 0.8),
            stop_loss=data.get('stop_loss'),
            take_profit=data.get('take_profit'),
            reason=data.get('message', 'Webhook signal'),
            source='webhook',
            timestamp=datetime.now().timestamp()
        )
        
        # 使用现有的添加信号逻辑
        return await add_signal(signal)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid webhook data: {str(e)}")

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    print("启动交易信号服务器...")
    print("API文档: http://localhost:6677/docs")
    print("信号文件: user_data/external_signals.json")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=6677
    )