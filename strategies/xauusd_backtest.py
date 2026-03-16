#!/usr/bin/env python3
"""
XAUUSD 策略回测 + 实时信号生成
运行: python xauusd_backtest.py
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

# ==================== 配置 ====================
CONFIG = {
    'symbol': 'XAUUSD',
    'initial_balance': 100000,
    'risk_per_trade': 0.01,
    'max_daily_risk': 0.03,
    'stop_loss_pct': 0.02,
    'take_profit_pct': 0.04,
    'max_positions': 2,
}

# ==================== 因子权重 ====================
WEIGHTS = {
    'news': 0.25,
    'order_flow': 0.25,
    'volatility': 0.20,
    'macro': 0.20,
    'ml': 0.10
}

# ==================== 模拟数据生成 ====================
def generate_mock_data(days=365):
    """生成模拟黄金数据"""
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    # 模拟黄金趋势 (缓慢上涨)
    np.random.seed(42)
    returns = np.random.normal(0.0003, 0.008, days)
    
    # 添加趋势
    trend = np.linspace(0, 0.15, days)
    prices = 5000 * (1 + trend + np.cumsum(returns))
    
    df = pd.DataFrame({
        'date': dates,
        'open': prices * (1 + np.random.uniform(-0.005, 0.005, days)),
        'high': prices * (1 + np.random.uniform(0, 0.02, days)),
        'low': prices * (1 - np.random.uniform(0, 0.02, days)),
        'close': prices,
        'volume': np.random.randint(10000, 50000, days)
    })
    
    df.set_index('date', inplace=True)
    return df

# ==================== 因子计算 ====================
def calculate_news_factor():
    """001新闻因子 - 使用刚才抓取的结果"""
    # 基于刚才Kitco新闻分析: 10看多, 4看空
    # 因子值 = (10-4)/(10+4) = 0.43
    return 0.43

def calculate_order_flow_factor(df):
    """002机构订单因子"""
    if len(df) < 20:
        return 0
    
    volume_ma = df['volume'].rolling(20).mean()
    volume_ratio = df['volume'].iloc[-1] / volume_ma.iloc[-1] if volume_ma.iloc[-1] > 0 else 1
    
    momentum = (df['close'].iloc[-1] - df['close'].iloc[-20]) / df['close'].iloc[-20]
    
    if volume_ratio > 1.3 and momentum > 0.01:
        return 0.5
    elif volume_ratio > 1.3 and momentum < -0.01:
        return -0.5
    return momentum * 10  # 归一化到 -0.5 ~ 0.5

def calculate_volatility_factor(df):
    """003波动率因子"""
    if len(df) < 20:
        return 0
    
    # ATR
    high_low = df['high'] - df['low']
    atr = high_low.rolling(14).mean().iloc[-1]
    
    # 布林带
    sma = df['close'].rolling(20).mean().iloc[-1]
    std = df['close'].rolling(20).std().iloc[-1]
    upper = sma + 2 * std
    lower = sma - 2 * std
    
    current_price = df['close'].iloc[-1]
    
    if current_price > upper:
        return 0.5
    elif current_price < lower:
        return -0.5
    
    # 中性区域
    position = (current_price - sma) / (std * 2) if std > 0 else 0
    return np.clip(position * 0.3, -0.3, 0.3)

def calculate_macro_factor():
    """004宏观因子"""
    # 基于刚才DXY分析: DXY=100.383 跌0.11%
    score = 0
    
    # DXY: 下跌 = 黄金利好
    dxy_change = -0.0011  # -0.11%
    if dxy_change < 0:
        score += 0.3
    
    # 实际利率 (假设)
    real_yield = -0.5  # 负利率 = 黄金利好
    if real_yield < 0:
        score += 0.5
    
    return np.clip(score, -0.5, 0.5)

def calculate_ml_factor():
    """005 ML因子 (预留)"""
    return 0

# ==================== 综合信号 ====================
def calculate_signals(df):
    """计算所有因子和综合信号"""
    news = calculate_news_factor()
    order_flow = calculate_order_flow_factor(df)
    volatility = calculate_volatility_factor(df)
    macro = calculate_macro_factor()
    ml = calculate_ml_factor()
    
    factors = {
        'news': news,
        'order_flow': order_flow,
        'volatility': volatility,
        'macro': macro,
        'ml': ml
    }
    
    # 加权分数
    score = sum(factors[k] * WEIGHTS[k] for k in WEIGHTS)
    
    return factors, score

# ==================== 回测 ====================
def backtest(df, initial_balance=100000):
    """简单回测"""
    balance = initial_balance
    trades = []
    position = None
    
    for i in range(60, len(df)):  # 从第60天开始
        window = df.iloc[:i+1]
        
        factors, score = calculate_signals(window)
        
        current_price = df['close'].iloc[i]
        
        if position is None:
            if score >= 0.25:  # 做多
                entry = current_price
                stop = entry * (1 - CONFIG['stop_loss_pct'])
                position = {
                    'type': 'LONG',
                    'entry': entry,
                    'stop': stop,
                    'entry_date': df.index[i]
                }
            elif score <= -0.25:  # 做空
                entry = current_price
                stop = entry * (1 + CONFIG['stop_loss_pct'])
                position = {
                    'type': 'SHORT',
                    'entry': entry,
                    'stop': stop,
                    'entry_date': df.index[i]
                }
        else:
            # 检查止损
            if position['type'] == 'LONG':
                if current_price <= position['stop']:
                    pnl = (current_price - position['entry']) / position['entry']
                    balance *= (1 + pnl)
                    trades.append({
                        'entry': position['entry'],
                        'exit': current_price,
                        'pnl': pnl,
                        'type': 'LONG'
                    })
                    position = None
            else:
                if current_price >= position['stop']:
                    pnl = (position['entry'] - current_price) / position['entry']
                    balance *= (1 + pnl)
                    trades.append({
                        'entry': position['entry'],
                        'exit': current_price,
                        'pnl': pnl,
                        'type': 'SHORT'
                    })
                    position = None
    
    return balance, trades

# ==================== 主程序 ====================
def main():
    print("=" * 60)
    print("XAUUSD 量化策略 v3.0 回测系统")
    print("=" * 60)
    
    # 生成模拟数据
    print("\n[1] 生成历史数据...")
    df = generate_mock_data(days=365)
    print(f"    数据范围: {df.index[0].date()} ~ {df.index[-1].date()}")
    print(f"    数据点数: {len(df)}")
    
    # 实时信号
    print("\n[2] 计算实时信号...")
    factors, score = calculate_signals(df)
    
    print(f"    001 新闻因子:     {factors['news']:+.2f}")
    print(f"    002 机构订单:    {factors['order_flow']:+.2f}")
    print(f"    003 波动率:      {factors['volatility']:+.2f}")
    print(f"    004 宏观:        {factors['macro']:+.2f}")
    print(f"    005 ML:          {factors['ml']:+.2f}")
    print(f"    ─────────────────")
    print(f"    综合分数:        {score:+.2f}")
    
    # 信号
    if score >= 0.25:
        signal = "BUY"
    elif score <= -0.25:
        signal = "SELL"
    else:
        signal = "WAIT"
    
    print(f"\n[3] 实时信号: {signal}")
    print(f"    当前价格: ${df['close'].iloc[-1]:.2f}")
    
    # 回测
    print("\n[4] 回测 (最近60天)...")
    final_balance, trades = backtest(df)
    
    if trades:
        wins = [t for t in trades if t['pnl'] > 0]
        losses = [t for t in trades if t['pnl'] <= 0]
        win_rate = len(wins) / len(trades) * 100 if trades else 0
        avg_win = np.mean([t['pnl'] for t in wins]) * 100 if wins else 0
        avg_loss = np.mean([t['pnl'] for t in losses]) * 100 if losses else 0
        
        print(f"    总交易:    {len(trades)} 笔")
        print(f"    胜率:      {win_rate:.1f}%")
        print(f"    平均盈利:  {avg_win:.2f}%")
        print(f"    平均亏损:  {avg_loss:.2f}%")
        print(f"    最终余额:  ${final_balance:,.2f}")
        print(f"    收益率:    {(final_balance - CONFIG['initial_balance']) / CONFIG['initial_balance'] * 100:.2f}%")
    else:
        print("    无交易")
    
    # 输出JSON
    result = {
        'timestamp': datetime.now().isoformat(),
        'signal': signal,
        'score': round(score, 3),
        'factors': {k: round(v, 3) for k, v in factors.items()},
        'current_price': round(df['close'].iloc[-1], 2),
        'backtest': {
            'final_balance': round(final_balance, 2),
            'return_pct': round((final_balance - CONFIG['initial_balance']) / CONFIG['initial_balance'] * 100, 2),
            'total_trades': len(trades)
        }
    }
    
    print("\n" + "=" * 60)
    print("JSON Output:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    return result

if __name__ == "__main__":
    main()
