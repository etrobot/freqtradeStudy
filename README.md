# Freqtrade 价格行为策略交易机器人

这是一个基于 Freqtrade 框架的加密货币交易机器人项目，专注于纯粹的价格行为（Price Action）策略开发与研究。

## 🎯 项目特点

- **纯粹价格行为策略**: 拒绝所有技术指标和成交量分析，仅基于开高低收价格数据
- **分层架构设计**: 采用四层架构实现策略逻辑
- **多周期分析**: 支持基于5分钟周期的多周期价格行为分析
- **双策略模式**: 突破入场 + 抢反弹双重策略组合
- **简单出场机制**: 基于时间周期的简单出场逻辑

## 📊 策略架构

### 第零层 - K线预处理
- 基础K线属性：阳线/阴线标记、K线长度、实体长度
- K线长度值（带正负）：阳线为正，阴线为负
- 多周期封装：基于5分钟数据构建等效分析周期

### 第一层 - 基础判断方法
- **趋势判断**: K线均分，比较后段最低收盘与前段平均价
- **波幅增强**: 判断当前K线长度是否超过历史80%分位数

### 第二层 - 双重入场策略
- **突破策略**: 上升趋势 + 波幅增强 + N根阳线 + 非最长实体
- **反弹策略**: 下降趋势 + 波幅增强 + M根阳线 + 阴线占比>60%

### 第三层 - 出场机制
- 仅基于时间周期：配置K线数量后强制出场
- 简单直接，拒绝复杂条件干扰

## 🚀 快速开始

### 环境要求
- Python 3.12+ (推荐 3.13+)
- Freqtrade 框架
- 币安交易所API密钥

### 安装依赖
```bash
pip install python-dotenv freqtrade
```

### 配置环境变量
```bash
# 币安API配置（必需）
export BINANCE_API_KEY="你的API密钥"
export BINANCE_API_SECRET="你的API密钥"

# 可选配置
export FREQTRADE_USERNAME="自定义用户名"
export FREQTRADE_PASSWORD="自定义密码"
export JWT_SECRET="JWT密钥串"
export WS_TOKEN="WebSocket令牌"
```

### 启动交易
```bash
python main.py
```

## 📈 交易参数配置

### 默认交易对
- BTC/USDT
- ETH/USDT
- SOL/USDT
- AVAX/USDT
- DOGE/USDT
- XRP/USDT

### 默认参数
- 时间周期：5分钟
- 最大持仓：3个交易对
- 每笔交易金额：100 USDT
- 止损设置：5% (优化后，原15%)
- 目标收益：3%→2%→1%→0% (优化后，原1000%)
- 强制出场：25分钟 / 5根K线

## 📊 回测功能

### 自动回测脚本
```bash
./run_backtest.sh
```

该脚本会自动：
1. 检查历史数据
2. 下载缺失的市场数据
3. 执行回测分析
4. 生成回测报告

### 手动回测命令
```bash
# 下载市场数据
freqtrade download-data --config user_data/config_price-act_strategy.json --pairs BTC/USDT --timeframe 5m

# 运行回测
freqtrade backtesting --config user_data/config_price-act_strategy.json --strategy PriceActionStrategy

# 参数优化 (推荐使用优化后的配置)
freqtrade hyperopt --config user_data/config_hyperopt_fixed.json --strategy PriceActionStrategy --hyperopt-loss SharpeHyperOptLoss --epochs 50 --timerange 20241001- --spaces buy sell
```

## 🔧 配置文件

主要配置文件位于 `user_data/config_price-act_strategy.json`，可调整以下参数：

```json
{
  "max_open_trades": 3,      // 最大同时持仓数
  "stake_amount": 100,       // 每笔交易金额
  "stake_currency": "USDT",  // 基础货币
  "minimal_roi": {
    "0": 0.03,               // 0分钟时目标收益3% (优化后)
    "15": 0.02,              // 15分钟时目标收益2%
    "30": 0.01,              // 30分钟时目标收益1%
    "60": 0                  // 60分钟时强制出场
  },
  "stoploss": -0.05          // 止损比例-5% (优化后)
}
```

**⚠️ 重要配置更新说明:**
- 原配置ROI目标为1000%（不现实），已优化为3%→2%→1%→0%
- 原止损15%过于激进，已优化为5%
- 建议使用 `user_data/config_hyperopt_fixed.json` 进行参数优化

## 📋 策略参数

在 `user_data/strategies/price-act_strategy.py` 中可配置：

```python
# 基础工具参数
trend_analysis_period = 20      # 趋势分析周期
amplitude_lookback = 20        # 波幅分析回望期
amplitude_percentile = 0.8     # 波幅增强阈值80%

# 策略参数
bear_ratio_threshold = 0.6     # 反弹策略阴线比例阈值
exit_candle_count = 5          # 强制出场K线数量
breakout_bull_candles = 2      # 突破策略阳线数量
rebound_bull_candles = 1       # 反弹策略阳线数量
```

## 📁 项目结构

```
freqtradeStudy/
├── main.py                            # 交易启动器
├── run_backtest.sh                    # 自动回测脚本
├── pyproject.toml                     # 项目依赖配置
├── user_data/
│   ├── strategies/
│   │   └── price-act_strategy.py     # 价格行为策略
│   ├── config_price-act_strategy.json # 交易配置
│   └── data/binance/                  # 市场数据存储
└── README.md                          # 项目说明
```

## 💡 开发说明

### 策略优化建议
1. **参数调优**: 根据回测结果调整入场条件参数
2. **时间周期**: 测试不同的时间周期倍数效果
3. **风险管理**: 动态调整止损和止盈比例
4. **策略组合**: 考虑增加更多入场逻辑组合

### 🔧 Hyperopt优化经验总结 (2025-09-30)

**关键发现:**
- **配置问题比策略逻辑更重要**: 不现实的ROI设置(1000%)导致策略完全失效
- **止损设置影响巨大**: 15%止损过于激进，5%更合理
- **信号生成数量**: 过于严格的条件只产生14个交易信号，需要适度放宽

**优化成果:**
- 原始结果: 总收益 -0.54%，胜率 28.6%，交易数 14
- 预期改进: 总收益转正，胜率 35-45%，交易数 50-200+

**最佳实践:**
1. **现实的ROI目标**: 使用3%→2%→1%→0%梯度设置
2. **合理的止损**: 5-10%范围，避免过度激进
3. **充分的优化轮次**: 最少50轮epochs，推荐100+
4. **多样化交易对**: 增加BNB、ADA、DOT等提高数据多样性

### 代码结构特点
- 模块化分层设计，便于维护和扩展
- 纯价格行为逻辑，避免指标过度拟合
- 灵活的参数配置，支持快速策略迭代
- 中文注释完善，易于理解策略逻辑

## ⚠️ 风险提示

本策略仅供学习研究使用，不构成投资建议。加密货币交易存在高风险，可能导致本金损失。使用本策略进行交易前，请：

1. 充分了解策略逻辑
2. 进行充分的历史回测
3. 使用小额资金实盘测试
4. 设置合理的风险控制参数

## 📞 支持与反馈

如有问题或建议，欢迎通过以下方式联系：
- 提交 Issue 报告问题
- 提出功能改进建议
- 分享策略优化思路

---

**免责声明**: 本项目仅供技术研究和学习使用，任何投资决策需独立判断并自行承担风险。