# XAUUSD 综合策略 v3.0 - 001因子融合版
> 版本: v3.0 | 更新: 2026-03-16
> 状态: 🟢 活跃

---

## 策略概述

融合4大顶级因子 + 001号新闻因子，实现**机构级黄金量化交易**。

---

## 因子权重

| 因子 | 名称 | 权重 |
|------|------|------|
| 001 | 新闻趋势因子 | 25% |
| 002 | 机构订单因子 | 25% |
| 003 | 波动率因子 | 20% |
| 004 | 宏观因子 | 20% |
| 005 | ML预测因子 | 10% |

---

## 入场条件

### 多头信号 (总分 >= 0.6)

```
001. 新闻因子 >= 0.3 OR
002. 机构订单: 订单块确认 + COT多头 OR
003. 波动率: IV-HV正价差 + Contango OR
004. 宏观: 实际利率 < 0% + 央行购金
```

### 空头信号 (总分 <= -0.6)

```
001. 新闻因子 <= -0.3 OR
002. 机构订单: 流动性耗尽 + COT空头 OR
003. 波动率: IV-HV负价差 + Backwardation OR
004. 宏观: 实际利率 > 2% + 央行售金
```

---

## 风控规则

| 规则 | 参数 |
|------|------|
| 单笔风险 | 1% |
| 单日风险 | 3% |
| 止损 | 2% 或 2倍ATR |
| 止盈 | 4% 或 3倍ATR |
| 持仓上限 | 2单 |
| 最大回撤 | 10% |

---

## 时间过滤

| 时段 | 交易 | 原因 |
|------|------|------|
| 13:00-17:00 UTC | ✅ | 伦敦+纽约流动性最好 |
| 21:30-23:30 UTC | ✅ | 美国数据发布后 |
| 00:00-07:00 UTC | ❌ | 亚洲盘流动性差 |
| 数据发布前30分钟 | ❌ | 不确定 |
| 周五下午 | ❌ | 周末风险 |

---

## 禁止条件

- [ ] 点差 > 30点
- [ ] VIX > 35 (恐慌过度)
- [ ] 连续亏损3单
- [ ] 非农/CPI/FOMC当天
- [ ] 001号因子 |因子值| < 0.2 (新闻不明朗)

---

## Python实现

```python
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class XAUUSD_Strategy_v3:
    def __init__(self):
        self.name = "XAUUSD_Strategy_v3"
        self.risk_per_trade = 0.01
        self.max_daily_risk = 0.03
        self.stop_loss_pct = 0.02
        self.take_profit_pct = 0.04
        
        # 因子权重
        self.weights = {
            'news': 0.25,
            'order_flow': 0.25,
            'volatility': 0.20,
            'macro': 0.20,
            'ml': 0.10
        }
    
    def calculate_factors(self, df, news_factor, cot_data, macro_data):
        """计算所有因子"""
        factors = {}
        
        # 001 新闻因子
        factors['news'] = news_factor
        
        # 002 机构订单因子
        factors['order_flow'] = self.order_flow_factor(df)
        
        # 003 波动率因子
        factors['volatility'] = self.volatility_factor(df)
        
        # 004 宏观因子
        factors['macro'] = self.macro_factor(macro_data)
        
        # 005 ML因子 (预留)
        factors['ml'] = 0
        
        return factors
    
    def order_flow_factor(self, df):
        """机构订单因子"""
        # 简化: 使用成交量和价格动量
        volume_ma = df['volume'].rolling(20).mean()
        volume_ratio = df['volume'] / volume_ma
        
        # 价格动量
        momentum = df['close'].pct_change(20)
        
        # 订单块信号
        if volume_ratio > 1.5 and momentum > 0:
            return 0.5
        elif volume_ratio > 1.5 and momentum < 0:
            return -0.5
        return 0
    
    def volatility_factor(self, df):
        """波动率因子"""
        # ATR
        high_low = df['high'] - df['low']
        atr = high_low.rolling(14).mean()
        
        # 布林带
        sma = df['close'].rolling(20).mean()
        std = df['close'].rolling(20).std()
        upper = sma + 2 * std
        lower = sma - 2 * std
        
        # 突破信号
        if df['close'].iloc[-1] > upper.iloc[-1]:
            return 0.5  # 突破上轨，多
        elif df['close'].iloc[-1] < lower.iloc[-1]:
            return -0.5  # 突破下轨，空
        
        # 震荡
        return 0
    
    def macro_factor(self, macro_data):
        """宏观因子"""
        score = 0
        
        # 实际利率
        if 'real_yield' in macro_data:
            ry = macro_data['real_yield']
            if ry < 0:
                score += 0.5
            elif ry > 2:
                score -= 0.5
        
        # 央行购金
        if 'cb_gold' in macro_data:
            if macro_data['cb_gold'] > 50:  # 50吨/月
                score += 0.3
        
        # DXY
        if 'dxy_change' in macro_data:
            if macro_data['dxy_change'] < -0.002:
                score += 0.3
            elif macro_data['dxy_change'] > 0.002:
                score -= 0.3
        
        return score
    
    def calculate_score(self, factors):
        """计算综合分数"""
        score = 0
        for factor_name, weight in self.weights.items():
            score += factors.get(factor_name, 0) * weight
        return score
    
    def should_entry(self, df, news_factor, cot_data, macro_data):
        """判断是否入场"""
        factors = self.calculate_factors(df, news_factor, cot_data, macro_data)
        score = self.calculate_score(factors)
        
        # 新闻过滤
        if abs(news_factor) < 0.2:
            return 'WAIT', factors, score, 'News unclear'
        
        # 入场信号
        if score >= 0.6:
            return 'LONG', factors, score, 'Bullish signal'
        elif score <= -0.6:
            return 'SHORT', factors, score, 'Bearish signal'
        
        return 'WAIT', factors, score, 'No clear signal'
    
    def calculate_position_size(self, account_balance, entry_price, stop_loss):
        """计算仓位"""
        risk_amount = account_balance * self.risk_per_trade
        price_risk = entry_price - stop_loss
        
        if price_risk <= 0:
            return 0
        
        position_size = risk_amount / price_risk
        return position_size
    
    def backtest(self, df, news_series, start_date, end_date):
        """回测"""
        results = []
        balance = 100000
        position = None
        
        for date in pd.date_range(start_date, end_date):
            if date not in df.index:
                continue
            
            row = df.loc[date]
            news = news_series.get(date, 0)
            
            signal, factors, score, reason = self.should_entry(
                row.to_frame().T, news, None, {}
            )
            
            if signal == 'LONG' and position is None:
                # 开多仓
                entry = row['close']
                stop = entry * (1 - self.stop_loss_pct)
                target = entry * (1 + self.take_profit_pct)
                position = {
                    'type': 'LONG',
                    'entry': entry,
                    'stop': stop,
                    'target': target,
                    'date': date
                }
            
            elif signal == 'SHORT' and position is None:
                # 开空仓
                entry = row['close']
                stop = entry * (1 + self.stop_loss_pct)
                target = entry * (1 - self.take_profit_pct)
                position = {
                    'type': 'SHORT',
                    'entry': entry,
                    'stop': stop,
                    'target': target,
                    'date': date
                }
            
            elif position is not None:
                # 检查止损/止盈
                if position['type'] == 'LONG':
                    if row['close'] <= position['stop']:
                        balance *= (1 - self.risk_per_trade)
                        position = None
                    elif row['close'] >= position['target']:
                        balance *= (1 + self.take_profit_pct)
                        position = None
                else:
                    if row['close'] >= position['stop']:
                        balance *= (1 - self.risk_per_trade)
                        position = None
                    elif row['close'] <= position['target']:
                        balance *= (1 + self.take_profit_pct)
                        position = None
            
            results.append({
                'date': date,
                'balance': balance,
                'signal': signal,
                'score': score
            })
        
        return pd.DataFrame(results)
```

---

## 绩效指标

| 指标 | 目标值 |
|------|--------|
| 年化收益 | > 30% |
| 夏普比率 | > 1.5 |
| 最大回撤 | < 10% |
| 胜率 | > 55% |
| 盈亏比 | > 1.5 |

---

*策略 v3.0 完成 - 2026-03-16*
