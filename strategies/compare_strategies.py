#!/usr/bin/env python3
"""
XAUUSD 策略对比回测: v3 (综合因子) vs v8 (缠论买二卖二)
运行: python compare_strategies.py
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json

# ==================== 数据生成 ====================
def generate_data(seed=42, days=180):
    np.random.seed(seed)
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    # 模拟黄金走势 (趋势 + 震荡)
    trend = np.linspace(0, 0.25, days)
    cycle = np.sin(np.linspace(0, 6, days)) * 0.1
    noise = np.cumsum(np.random.normal(0, 0.008, days))
    prices = 4900 * (1 + trend + cycle + noise * 0.15)
    
    df = pd.DataFrame({
        'date': dates,
        'open': prices * (1 + np.random.uniform(-0.003, 0.003, days)),
        'high': prices * (1 + np.random.uniform(0, 0.015, days)),
        'low': prices * (1 - np.random.uniform(0, 0.015, days)),
        'close': prices,
        'volume': np.random.randint(10000, 50000, days)
    })
    df.set_index('date', inplace=True)
    return df

# ==================== 策略v3: 综合因子 ====================
class StrategyV3:
    """综合因子策略"""
    
    def __init__(self):
        self.name = "v3_综合因子"
        self.threshold = 0.25
        
    def calculate_factors(self, df, news=0.43):
        """计算因子"""
        # 简化因子计算
        momentum = (df['close'].iloc[-1] - df['close'].iloc[-20]) / df['close'].iloc[-20] if len(df) >= 20 else 0
        
        # 波动率因子
        sma = df['close'].rolling(20).mean().iloc[-1]
        std = df['close'].rolling(20).std().iloc[-1]
        upper = sma + 2 * std
        vol_signal = 0.3 if df['close'].iloc[-1] > upper else 0.1
        
        # 宏观 (固定)
        macro = 0.5
        
        # 综合分数
        score = news * 0.25 + momentum * 5 + vol_signal * 0.2 + macro * 0.2
        
        return score
    
    def signal(self, df, news=0.43):
        score = self.calculate_factors(df, news)
        
        if score > self.threshold:
            return 'LONG', score
        elif score < -self.threshold:
            return 'SHORT', score
        return 'WAIT', score

# ==================== 策略v8: 缠论 ====================
class StrategyV8:
    """缠论买二卖二策略"""
    
    def __init__(self):
        self.name = "v8_缠论"
        self.threshold = 0.25
        
    def calculate_macd(self, df):
        """计算MACD"""
        ema_fast = df['close'].ewm(span=12, adjust=False).mean()
        ema_slow = df['close'].ewm(span=26, adjust=False).mean()
        
        macd = ema_fast - ema_slow
        signal = macd.ewm(span=9, adjust=False).mean()
        hist = macd - signal
        
        return hist
    
    def detect_divergence(self, df):
        """检测背离"""
        if len(df) < 30:
            return None
        
        hist = self.calculate_macd(df)
        price = df['close'].values
        
        # 检测顶背离
        price_high = price[-20:].max()
        hist_high = hist.iloc[-20:].max()
        
        # 价格新高，MACD不新高 = 顶背离
        recent_price_high = price[-5:].max()
        recent_hist_high = hist.iloc[-5:].max()
        
        if recent_price_high > price_high * 1.01 and recent_hist_high < hist_high * 0.9:
            return 'top_divergence'
        
        # 底背离
        price_low = price[-20:].min()
        hist_low = hist.iloc[-20:].min()
        
        recent_price_low = price[-5:].min()
        recent_hist_low = hist.iloc[-5:].min()
        
        if recent_price_low < price_low * 0.99 and recent_hist_low > hist_low * 1.1:
            return 'bottom_divergence'
        
        return None
    
    def signal(self, df):
        """缠论信号"""
        div = self.detect_divergence(df)
        
        # 简化: 背离+趋势
        if div == 'bottom_divergence':
            return 'LONG', 0.5
        elif div == 'top_divergence':
            return 'SHORT', 0.5
        
        # 无背离时看趋势
        ema20 = df['close'].rolling(20).mean().iloc[-1]
        if df['close'].iloc[-1] > ema20:
            return 'LONG', 0.2
        
        return 'WAIT', 0

# ==================== 回测引擎 ====================
def backtest(strategy, df, initial_balance=100000, stop_loss=0.02, take_profit=0.04):
    balance = initial_balance
    position = None
    trades = []
    
    for i in range(50, len(df)):
        window = df.iloc[:i+1]
        signal, score = strategy.signal(window)
        price = df['close'].iloc[i]
        
        if position is None:
            if signal == 'LONG':
                position = {
                    'type': 'LONG',
                    'entry': price,
                    'stop': price * (1 - stop_loss),
                    'target': price * (1 + take_profit),
                    'entry_date': df.index[i]
                }
            elif signal == 'SHORT':
                position = {
                    'type': 'SHORT',
                    'entry': price,
                    'stop': price * (1 + stop_loss),
                    'target': price * (1 - take_profit),
                    'entry_date': df.index[i]
                }
        else:
            closed = False
            pnl = 0
            
            if position['type'] == 'LONG':
                if price <= position['stop']:
                    pnl = (price - position['entry']) / position['entry']
                    closed = True
                elif price >= position['target']:
                    pnl = (price - position['entry']) / position['entry']
                    closed = True
            else:
                if price >= position['stop']:
                    pnl = (position['entry'] - price) / position['entry']
                    closed = True
                elif price <= position['target']:
                    pnl = (position['entry'] - price) / position['entry']
                    closed = True
            
            if closed:
                balance *= (1 + pnl)
                trades.append({
                    'entry': position['entry'],
                    'exit': price,
                    'pnl': pnl,
                    'type': position['type']
                })
                position = None
    
    return balance, trades

# ==================== 主程序 ====================
def main():
    print("=" * 70)
    print("XAUUSD 策略对比回测: v3 (综合因子) vs v8 (缠论买二卖二)")
    print("=" * 70)
    
    # 生成数据
    print("\n[1] 生成测试数据...")
    df = generate_data()
    print(f"    数据范围: {df.index[0].date()} ~ {df.index[-1].date()}")
    print(f"    数据点数: {len(df)}")
    print(f"    价格范围: ${df['close'].min():.2f} ~ ${df['close'].max():.2f}")
    
    # 实时信号
    print("\n[2] 实时信号...")
    
    v3 = StrategyV3()
    v8 = StrategyV8()
    
    v3_signal, v3_score = v3.signal(df)
    v8_signal, v8_score = v8.signal(df)
    
    print(f"    v3 (综合因子): {v3_signal} (score: {v3_score:.3f})")
    print(f"    v8 (缠论):     {v8_signal} (score: {v8_score:.3f})")
    
    # 回测v3
    print("\n[3] 回测 v3 (综合因子)...")
    v3_balance, v3_trades = backtest(v3, df)
    v3_return = (v3_balance - 100000) / 100000 * 100
    v3_win_rate = len([t for t in v3_trades if t['pnl'] > 0]) / len(v3_trades) * 100 if v3_trades else 0
    
    print(f"    最终余额: ${v3_balance:,.2f}")
    print(f"    收益率:   {v3_return:.2f}%")
    print(f"    交易次数: {len(v3_trades)}")
    print(f"    胜率:     {v3_win_rate:.1f}%")
    
    # 回测v8
    print("\n[4] 回测 v8 (缠论买二卖二)...")
    v8_balance, v8_trades = backtest(v8, df)
    v8_return = (v8_balance - 100000) / 100000 * 100
    v8_win_rate = len([t for t in v8_trades if t['pnl'] > 0]) / len(v8_trades) * 100 if v8_trades else 0
    
    print(f"    最终余额: ${v8_balance:,.2f}")
    print(f"    收益率:   {v8_return:.2f}%")
    print(f"    交易次数: {len(v8_trades)}")
    print(f"    胜率:     {v8_win_rate:.1f}%")
    
    # 对比
    print("\n" + "=" * 70)
    print("对比结果")
    print("=" * 70)
    print(f"{'指标':<15} {'v3 (综合因子)':<20} {'v8 (缠论)':<20}")
    print("-" * 70)
    print(f"{'实时信号':<15} {v3_signal:<20} {v8_signal:<20}")
    print(f"{'分数':<15} {v3_score:<20.3f} {v8_score:<20.3f}")
    print(f"{'最终余额':<15} ${v3_balance:<18,.0f} ${v8_balance:<18,.0f}")
    print(f"{'收益率':<15} {v3_return:<19.2f}% {v8_return:<19.2f}%")
    print(f"{'交易次数':<15} {len(v3_trades):<20} {len(v8_trades):<20}")
    print(f"{'胜率':<15} {v3_win_rate:<19.1f}% {v8_win_rate:<19.1f}%")
    
    # 结论
    winner = "v3" if v3_return > v8_return else "v8"
    print(f"\n[5] 结论: {winner} 策略表现更好!")
    
    # 输出JSON
    result = {
        'timestamp': datetime.now().isoformat(),
        'v3': {
            'signal': v3_signal,
            'score': round(v3_score, 3),
            'final_balance': round(v3_balance, 2),
            'return_pct': round(v3_return, 2),
            'trades': len(v3_trades),
            'win_rate': round(v3_win_rate, 1)
        },
        'v8': {
            'signal': v8_signal,
            'score': round(v8_score, 3),
            'final_balance': round(v8_balance, 2),
            'return_pct': round(v8_return, 2),
            'trades': len(v8_trades),
            'win_rate': round(v8_win_rate, 1)
        },
        'winner': winner
    }
    
    print("\nJSON Output:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    return result

if __name__ == "__main__":
    main()
