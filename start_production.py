#!/usr/bin/env python3
"""
生产环境启动脚本
"""

import uvicorn
import os
from signal_server import app

if __name__ == "__main__":
    # 生产环境配置
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    workers = int(os.getenv("WORKERS", 1))
    
    print(f"🚀 启动生产环境信号服务器...")
    print(f"📡 监听地址: {host}:{port}")
    print(f"👥 工作进程: {workers}")
    print(f"📁 信号文件: user_data/external_signals.json")
    
    uvicorn.run(
        "signal_server:app",
        host=host,
        port=port,
        workers=workers,
        reload=False,
        access_log=True,
        log_level="info"
    )