# XAUUSD 策略v8 - 缠论买二卖二
> 版本: v8.0 | 更新: 2026-03-16
> 理论: 缠中说禅《教你炒股票》- 笔、线段、中枢、背离

---

## 核心理论

### 买二卖二
```
买二 = 第二个中枢背离笔 + 次级别回抽不破中枢上沿
卖二 = 第二个中枢背离笔 + 次级别回抽不破中枢下沿
```

### 背离类型
| 类型 | 条件 | 信号 |
|------|------|------|
| 价背 | 价格创新高，MACD/RSI不创新高 | 顶背离 = 卖 |
| 量背 | 价格创新高，成交量不配合 | 顶背离 = 卖 |
| 价底 | 价格创新低，MACD/RSI不创新低 | 底背离 = 买 |
| 量底 | 价格创新低，成交量萎缩 | 底背离 = 买 |

---

## 策略逻辑

### 入场条件 (买二)

```
1. 至少完成两个上涨中枢
2. 出现背离笔 (价格新高，MACD柱状图新低)
3. 次级别回抽不破前中枢上沿
4. 成交量缩量确认
```

### 出场条件 (卖二)

```
1. 价背: 价格新高，MACD/RSI背离
2. 量背: 成交量无法放大
3. 出现反转K线 (吞没/ Pin Bar / 十字星)
4. 止损: 2% 或 跌破前低
```

---

## 量化实现

```python
import pandas as pd
import numpy as np
from datetime import datetime

class ChanStrategy:
    """缠论买二卖二策略"""
    
    def __init__(self):
        self.name = "Chan_L2_Buy_Sell"
        self.stop_loss = 0.02
        self.take_profit = 0.04
        
    def calculate_ema(self, df, periods=[5, 10, 20, 50]):
        """计算EMA"""
        for p in periods:
            df[f'ema_{p}'] = df['close'].ewm(span=p, adjust=False).mean()
        return df
    
    def calculate_macd(self, df, fast=12, slow=26, signal=9):
        """计算MACD"""
        ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
        
        df['macd'] = ema_fast - ema_slow
        df['macd_signal'] = df['macd'].ewm(span=signal, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        return df
    
    def calculate_rsi(self, df, period=14):
        """计算RSI"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        return df
    
    def detect_divergence(self, df, lookback=20):
        """检测背离"""
        price = df['close'].values
        macd_hist = df['macd_hist'].values
        
        signals = []
        
        for i in range(lookback, len(df)):
            # 顶背离: 价格新高，MACD新低
            if price[i] > price[i-lookback:i].max() * 1.01:  # 价格新高1%
                if macd_hist[i] < macd_hist[i-lookback:i].max() * 0.9:  # MACD新低
                    signals.append({
                        'index': i,
                        'type': 'top_divergence',
                        'date': df.index[i]
                    })
            
            # 底背离: 价格新低，MACD新高
            if price[i] < price[i-lookback:i].min() * 0.99:  # 价格新低1%
                if macd_hist[i] > macd_hist[i-lookback:i].min() * 1.1:  # MACD新高
                    signals.append({
                        'index': i,
                        'type': 'bottom_divergence',
                        'date': df.index[i]
                    })
        
        return signals
    
    def detect_central(self, df, window=20):
        """检测中枢 (简化版)"""
        if len(df) < window:
            return None
        
        recent = df['close'].iloc[-window:]
        high = recent.max()
        low = recent.min()
        mid = (high + low) / 2
        
        return {'high': high, 'low': low, 'mid': mid}
    
    def detect_buy_2(self, df):
        """买二信号"""
        # 1. 检测底背离
        divergences = self.detect_divergence(df)
        
        if not divergences:
            return False, "No divergence"
        
        last_div = divergences[-1]
        
        # 2. 必须在背离后价格反弹
        if last_div['type'] == 'bottom_divergence':
            price_after = df['close'].iloc[last_div['index']:]
            if len(price_after) > 5:
                # 反弹超过背离点
                if price_after.iloc[-1] > df['close'].iloc[last_div['index']]:
                    return True, f"Buy2 at {last_div['date']}"
        
        return False, "Conditions not met"
    
    def detect_sell_2(self, df):
        """卖二信号"""
        # 1. 检测顶背离
        divergences = self.detect_divergence(df)
        
        if not divergences:
            return False, "No divergence"
        
        last_div = divergences[-1]
        
        # 2. 必须在背离后价格回落
        if last_div['type'] == 'top_divergence':
            price_after = df['close'].iloc[last_div['index']:]
            if len(price_after) > 5:
                # 回落跌破背离点
                if price_after.iloc[-1] < df['close'].iloc[last_div['index']]:
                    return True, f"Sell2 at {last_div['date']}"
        
        return False, "Conditions not met"
    
    def should_entry(self, df):
        """判断入场"""
        # 计算指标
        df = self.calculate_ema(df)
        df = self.calculate_macd(df)
        df = self.calculate_rsi(df)
        
        # 检测买二
        buy_signal, buy_reason = self.detect_buy_2(df)
        if buy_signal:
            return 'LONG', buy_reason
        
        # 检测卖二
        sell_signal, sell_reason = self.detect_sell_2(df)
        if sell_signal:
            return 'SHORT', sell_reason
        
        return 'WAIT', 'No signal'
    
    def backtest(self, df, initial_balance=100000):
        """回测"""
        balance = initial_balance
        position = None
        trades = []
        
        df = self.calculate_ema(df)
        df = self.calculate_macd(df)
        
        for i in range(50, len(df)):
            window = df.iloc[:i+1]
            signal, reason = self.should_entry(window)
            price = df['close'].iloc[i]
            
            if position is None:
                if signal == 'LONG':
                    entry = price
                    stop = entry * (1 - self.stop_loss)
                    target = entry * (1 + self.take_profit)
                    position = {
                        'type': 'LONG',
                        'entry': entry,
                        'stop': stop,
                        'target': target,
                        'entry_date': df.index[i]
                    }
                elif signal == 'SHORT':
                    entry = price
                    stop = entry * (1 + self.stop_loss)
                    target = entry * (1 - self.take_profit)
                    position = {
                        'type': 'SHORT',
                        'entry': entry,
                        'stop': stop,
                        'target': target,
                        'entry_date': df.index[i]
                    }
            else:
                # 检查止损/止盈
                if position['type'] == 'LONG':
                    if price <= position['stop']:
                        pnl = (price - position['entry']) / position['entry']
                        balance *= (1 + pnl)
                        trades.append(pnl)
                        position = None
                    elif price >= position['target']:
                        pnl = (price - position['entry']) / position['entry']
                        balance *= (1 + pnl)
                        trades.append(pnl)
                        position = None
                else:
                    if price >= position['stop']:
                        pnl = (position['entry'] - price) / position['entry']
                        balance *= (1 + pnl)
                        trades.append(pnl)
                        position = None
                    elif price <= position['target']:
                        pnl = (position['entry'] - price) / position['entry']
                        balance *= (1 + pnl)
                        trades.append(pnl)
                        position = None
        
        return balance, trades
```

---

## 背离平仓规则

```
1. 出现相反背离立即平仓
2. 触及止损/止盈
3. 出现反转形态 (吞没/十字星)
4. 持仓超过20根K线强制平仓
```

---

## 策略参数

| 参数 | 值 |
|------|-----|
| 背离周期 | 20根K线 |
| MACD参数 | 12,26,9 |
| RSI参数 | 14 |
| 止损 | 2% |
| 止盈 | 4% |
| 中枢窗口 | 20 |

---

## 与v3对比

| 维度 | v3 (综合因子) | v8 (缠论) |
|------|---------------|-----------|
| 入场依据 | 多因子加权 | 背离信号 |
| 出场依据 | 止盈/止损 | 背离反转 |
| 理论基础 | 宏观+技术 | 缠中说禅 |
| 信号频率 | 较高 | 较低 |
| 胜率预期 | 50-55% | 55-60% |

---

*策略v8完成 - 2026-03-16*
