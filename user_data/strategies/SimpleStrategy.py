import talib.abstract as ta
from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame
import freqtrade.vendor.qtpylib.indicators as qtpylib

class SimpleStrategy(IStrategy):
    """
    简单双均线策略示例
    """
    INTERFACE_VERSION = 3

    # 策略参数
    minimal_roi = {
        "60": 0.01,   # 60分钟后至少1%利润
        "30": 0.02,   # 30分钟后至少2%利润
        "0": 0.04     # 立即至少4%利润
    }

    stoploss = -0.10  # 止损10%

    # 时间框架
    timeframe = '5m'

    # 启动时需要的历史数据数量
    startup_candle_count: int = 30

    # 订单类型
    order_types = {
        'entry': 'limit',
        'exit': 'limit',
        'stoploss': 'market',
        'stoploss_on_exchange': False
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        添加技术指标到dataframe
        """
        # 简单移动平均线
        dataframe['sma_fast'] = ta.SMA(dataframe, timeperiod=10)
        dataframe['sma_slow'] = ta.SMA(dataframe, timeperiod=30)
        
        # RSI
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        
        # MACD
        macd = ta.MACD(dataframe)
        dataframe['macd'] = macd['macd']
        dataframe['macdsignal'] = macd['macdsignal']
        dataframe['macdhist'] = macd['macdhist']
        
        # 成交量移动平均
        dataframe['volume_mean'] = dataframe['volume'].rolling(10).mean()

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        买入信号逻辑
        """
        dataframe.loc[
            (
                # 快速均线上穿慢速均线
                (qtpylib.crossed_above(dataframe['sma_fast'], dataframe['sma_slow'])) &
                # RSI不超买
                (dataframe['rsi'] < 70) &
                # MACD金叉
                (dataframe['macd'] > dataframe['macdsignal']) &
                # 成交量高于平均
                (dataframe['volume'] > dataframe['volume_mean']) &
                # 确保有足够的成交量
                (dataframe['volume'] > 0)
            ),
            'enter_long'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        卖出信号逻辑
        """
        dataframe.loc[
            (
                # 快速均线下穿慢速均线
                (qtpylib.crossed_below(dataframe['sma_fast'], dataframe['sma_slow'])) |
                # RSI超买
                (dataframe['rsi'] > 80) |
                # MACD死叉
                (dataframe['macd'] < dataframe['macdsignal'])
            ),
            'exit_long'] = 1

        return dataframe