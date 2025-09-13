# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401

import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from pandas import DataFrame
from typing import Optional, Union
import json
import requests
from pathlib import Path

from freqtrade.strategy import (
    IStrategy,
    Trade,
    Order,
    informative,
    merge_informative_pair,
    stoploss_from_absolute,
)

# 添加技术指标库
import talib.abstract as ta

class ExternalSignalStrategy(IStrategy):
    """
    外部信号驱动策略
    通过读取外部信号文件或API来决定买卖操作
    """
    
    # 策略基本设置
    INTERFACE_VERSION = 3
    timeframe = '5m'
    process_only_new_candles = False  # 允许在当前K线内根据外部信号立即入场
    can_short = False
    
    # ROI设置 - 由于依赖外部信号，设置较高的ROI避免过早退出
    minimal_roi = {
        "0": 0.50,   # 50% ROI
        "40": 0.25,  # 25% ROI after 40 minutes
        "120": 0.10, # 10% ROI after 2 hours
        "720": 0.05  # 5% ROI after 12 hours
    }
    
    # 止损设置
    stoploss = -0.10  # 10% 止损
    
    # 信号相关设置
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = True
    
    # 外部信号配置
    signal_file_path = "user_data/external_signals.json"
    signal_api_url = "http://localhost:8000"  # 可选：从API获取信号
    signal_check_interval = 5  # 检查信号的间隔（秒）
    
    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self.last_signal_check = 0
        self.current_signals = {}
        
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        添加基本指标，主要用于信号验证
        """
        # 基本价格指标
        dataframe['hl2'] = (dataframe['high'] + dataframe['low']) / 2
        dataframe['hlc3'] = (dataframe['high'] + dataframe['low'] + dataframe['close']) / 3
        
        # 成交量指标
        dataframe['volume_sma'] = dataframe['volume'].rolling(window=20).mean()
        
        # RSI - 用于信号过滤
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        
        # 移动平均线 - 用于趋势确认
        dataframe['sma_20'] = ta.SMA(dataframe, timeperiod=20)
        dataframe['sma_50'] = ta.SMA(dataframe, timeperiod=50)
        
        return dataframe
    
    def check_external_signals(self, pair: str) -> dict:
        """
        检查外部信号
        返回格式: {
            'action': 'buy'/'sell'/'hold',
            'timestamp': unix_timestamp,
            'confidence': 0.0-1.0,
            'stop_loss': price,
            'take_profit': price
        }
        """
        current_time = datetime.now().timestamp()
        
        # 避免频繁检查
        if current_time - self.last_signal_check < self.signal_check_interval:
            return self.current_signals.get(pair, {})
        
        self.last_signal_check = current_time
        
        # 方法1：从文件读取信号
        signal = self.read_signal_from_file(pair)
        
        # 方法2：从API获取信号（如果配置了API URL）
        if not signal and self.signal_api_url:
            signal = self.read_signal_from_api(pair)
        
        if signal:
            self.current_signals[pair] = signal
            
        return signal or {}
    
    def read_signal_from_file(self, pair: str) -> dict:
        """
        从JSON文件读取信号
        """
        try:
            signal_file = Path(self.signal_file_path)
            if signal_file.exists():
                with open(signal_file, 'r') as f:
                    signals = json.load(f)
                    
                # 查找该交易对的最新信号
                pair_signals = signals.get(pair, [])
                if pair_signals:
                    # 返回最新的信号
                    latest_signal = max(pair_signals, key=lambda x: x.get('timestamp', 0))
                    
                    # 检查信号是否还有效（例如：5分钟内的信号）
                    signal_age = datetime.now().timestamp() - latest_signal.get('timestamp', 0)
                    if signal_age < 300:  # 5分钟内有效
                        return latest_signal
                        
        except Exception as e:
            self.logger.error(f"读取信号文件失败: {e}")
            
        return {}
    
    def read_signal_from_api(self, pair: str) -> dict:
        """
        从API获取信号
        """
        try:
            response = requests.get(
                f"{self.signal_api_url}/signals/{pair}",
                timeout=5
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self.logger.error(f"从API获取信号失败: {e}")
            
        return {}
    
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        基于外部信号生成入场信号
        """
        pair = metadata['pair']
        
        # 初始化信号列
        dataframe['enter_long'] = 0
        dataframe['enter_short'] = 0
        
        # 获取外部信号
        signal = self.check_external_signals(pair)
        
        if signal and signal.get('action') == 'buy':
            # 添加一些基本的过滤条件
            entry_conditions = (
                (dataframe['volume'] > dataframe['volume_sma'] * 0.5) &  # 成交量过滤
                (dataframe['rsi'] < 80)  # RSI过滤，避免超买
            )
            
            # 设置最后一根K线的买入信号
            dataframe.loc[dataframe.index[-1:], 'enter_long'] = np.where(
                entry_conditions.iloc[-1:], 1, 0
            )
            
        elif signal and signal.get('action') == 'sell':
            # 做空信号
            entry_conditions = (
                (dataframe['volume'] > dataframe['volume_sma'] * 0.5) &  # 成交量过滤
                (dataframe['rsi'] > 20)  # RSI过滤，避免超卖
            )
            
            dataframe.loc[dataframe.index[-1:], 'enter_short'] = np.where(
                entry_conditions.iloc[-1:], 1, 0
            )
        
        return dataframe
    
    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        基于外部信号生成出场信号
        """
        pair = metadata['pair']
        
        # 初始化信号列
        dataframe['exit_long'] = 0
        dataframe['exit_short'] = 0
        
        # 获取外部信号
        signal = self.check_external_signals(pair)
        
        if signal and signal.get('action') == 'sell':
            # 平多仓信号
            dataframe.loc[dataframe.index[-1:], 'exit_long'] = 1
            
        elif signal and signal.get('action') == 'buy':
            # 平空仓信号
            dataframe.loc[dataframe.index[-1:], 'exit_short'] = 1
            
        return dataframe
    
    def custom_stoploss(self, pair: str, trade: Trade, current_time: datetime,
                       current_rate: float, current_profit: float, **kwargs) -> float:
        """
        动态止损，可以基于外部信号调整
        """
        signal = self.check_external_signals(pair)
        
        # 如果外部信号提供了止损价格
        if signal and 'stop_loss' in signal:
            if trade.is_short:
                # 做空时，止损价格应该高于入场价格
                sl_price = signal['stop_loss']
                if sl_price > trade.open_rate:
                    return stoploss_from_absolute(sl_price, current_rate, is_short=True)
            else:
                # 做多时，止损价格应该低于入场价格
                sl_price = signal['stop_loss']
                if sl_price < trade.open_rate:
                    return stoploss_from_absolute(sl_price, current_rate, is_short=False)
        
        # 使用默认止损
        return self.stoploss
    
    def custom_exit(self, pair: str, trade: Trade, current_time: datetime, current_rate: float,
                   current_profit: float, **kwargs) -> Optional[Union[str, bool]]:
        """
        自定义退出逻辑
        """
        signal = self.check_external_signals(pair)
        
        # 如果外部信号要求退出
        if signal and signal.get('action') == 'exit':
            return 'external_exit_signal'
        
        # 如果外部信号提供了止盈价格
        if signal and 'take_profit' in signal:
            tp_price = signal['take_profit']
            
            if trade.is_short:
                if current_rate <= tp_price:
                    return 'take_profit_reached'
            else:
                if current_rate >= tp_price:
                    return 'take_profit_reached'
        
        return None