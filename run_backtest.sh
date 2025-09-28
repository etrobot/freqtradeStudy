#!/bin/bash

# 配置参数
CONFIG_FILE="user_data/config_price-act_strategy.json"
STRATEGY="PriceActionStrategy"
TIMERANGE="20240101-"
PAIRS=("BTC/USDT" "ETH/USDT" "SOL/USDT" "AVAX/USDT" "DOGE/USDT" "XRP/USDT")
TIMEFRAME="5m"
DATA_DIR="user_data/data/binance"

# 检查数据目录是否存在，不存在则创建
mkdir -p "$DATA_DIR"

# 检查数据是否存在的函数
check_data_exists() {
    local pair=$1
    # 将交易对中的/替换为_，因为这是freqtrade保存数据的格式
    local pair_dir=$(echo "$pair" | tr '/' '_')
    # 检查数据文件是否存在
    if [ -f "$DATA_DIR/${pair_dir}-${TIMEFRAME}.feather" ]; then
        return 0  # 文件存在，返回成功
    else
        return 1  # 文件不存在，返回失败
    fi
}

# 下载数据的函数
download_data() {
    local pair=$1
    echo "下载数据: $pair $TIMEFRAME"
    freqtrade download-data --config "$CONFIG_FILE" --pairs "$pair" --timeframe "$TIMEFRAME" --timerange "$TIMERANGE"
    
    # 检查下载是否成功
    if [ $? -ne 0 ]; then
        echo "下载 $pair 数据失败"
        exit 1
    fi
}

# 主程序
echo "开始检查数据..."

NEED_DOWNLOAD=false

# 检查所有交易对的数据是否存在
for pair in "${PAIRS[@]}"; do
    if ! check_data_exists "$pair"; then
        echo "未找到 $pair 的历史数据"
        NEED_DOWNLOAD=true
    else
        echo "$pair 的数据已存在"
    fi
done

# 如果需要下载数据
if [ "$NEED_DOWNLOAD" = true ]; then
    echo "开始下载缺失的数据..."
    for pair in "${PAIRS[@]}"; do
        download_data "$pair"
    done
    echo "数据下载完成!"
else
    echo "所有数据已存在，跳过下载步骤"
fi

# 运行回测
echo "开始回测..."
freqtrade backtesting --config "$CONFIG_FILE" --strategy "$STRATEGY" --timerange "$TIMERANGE"

# 检查回测是否成功
if [ $? -eq 0 ]; then
    echo "回测完成!"
else
    echo "回测过程中出现错误"
    exit 1
fi
