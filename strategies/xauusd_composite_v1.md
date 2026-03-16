# XAUUSD 综合因子策略 v1.0

> 创建: 2026-03-16
> 作者: A (量化交易员)

---

## 策略逻辑

### 因子权重

| 因子 | 权重 | 方向 |
|------|------|------|
| 机构订单 (Delta/CumDelta) | 25% | 正相关 |
| 波动率 (ATR收窄突破) | 20% | 正相关 |
| 宏观 (DXY↓ + VIX↑) | 25% | 正相关 |
| 机器学习 (LSTM预测) | 30% | 正相关 |

---

## 入场条件

### 多头信号 (满足≥3个)

```
1. 订单流: Cumulative Delta > 0 且 创新高
2. 波动率: 布林带收窄后放量突破上轨
3. 宏观: DXY日线下跌 + VIX > 15
4. ML: LSTM预测概率 > 0.6
```

### 空头信号 (满足≥3个)

```
1. 订单流: Cumulative Delta < 0 且 创新低
2. 波动率: 布林带收窄后放量突破下轨
3. 宏观: DXY日线上涨 + VIX < 20
4. ML: LSTM预测概率 < 0.4
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

---

## 时间过滤

| 时段 | 交易 | 原因 |
|------|------|------|
| 13:00-17:00 UTC | ✅ | 伦敦+纽约流动性最好 |
| 21:30-23:30 UTC | ✅ | 美国数据发布后 |
| 00:00-07:00 UTC | ❌ | 亚洲盘流动性差 |
| 数据发布前30分钟 | ❌ | 不确定 |

---

## 禁止条件 (任一触发则不开仓)

- [ ] 点差 > 30点
- [ ] VIX > 35 (恐慌过度)
- [ ] 布林带收窄 < 20% (等待突破)
- [ ] 连续亏损3单
- [ ] 非农/CPI/FOMC当天

---

## Python实现框架

```python
class XAUUSD_Strategy:
    def __init__(self):
        self.order_flow_weight = 0.25
        self.volatility_weight = 0.20
        self.macro_weight = 0.25
        self.ml_weight = 0.30
        
    def get_order_flow_signal(self, df):
        """机构订单因子"""
        delta = df['ask_vol'] - df['bid_vol']
        cum_delta = delta.rolling(20).sum()
        
        if cum_delta.iloc[-1] > 0 and cum_delta.iloc[-1] > cum_delta.iloc[-5]:
            return 1
        elif cum_delta.iloc[-1] < 0 and cum_delta.iloc[-1] < cum_delta.iloc[-5]:
            return -1
        return 0
    
    def get_volatility_signal(self, df):
        """波动率因子"""
        bb_upper, bb_mid, bb_lower = bollinger_bands(df['close'])
        bb_width = (bb_upper - bb_lower) / bb_mid
        
        # 收窄判断
        squeeze = bb_width.iloc[-1] < bb_width.rolling(20).mean().iloc[-1] * 0.8
        
        # 突破判断
        if squeeze:
            if df['close'].iloc[-1] > bb_upper.iloc[-1]:
                return 1  # 多
            elif df['close'].iloc[-1] < bb_lower.iloc[-1]:
                return -1 # 空
        return 0
    
    def get_macro_signal(self, dxy, vix):
        """宏观因子"""
        dxy_change = dxy.pct_change().iloc[-1]
        signal = 0
        
        if dxy_change < -0.002 and vix.iloc[-1] > 15:
            signal += 1  # 多: 美元跌 + 恐慌
        elif dxy_change > 0.002 and vix.iloc[-1] < 20:
            signal -= 1  # 空: 美元涨 + 乐观
            
        return signal
    
    def get_ml_signal(self, model, features):
        """机器学习因子"""
        pred = model.predict(features)
        
        if pred > 0.6:
            return 1
        elif pred < 0.4:
            return -1
        return 0
    
    def should_entry(self, df, dxy, vix, ml_model):
        """综合信号"""
        of_sig = self.get_order_flow_signal(df)
        vol_sig = self.get_volatility_signal(df)
        macro_sig = self.get_macro_signal(dxy, vix)
        ml_sig = self.get_ml_signal(ml_model, df)
        
        # 权重计算
        score = (
            of_sig * self.order_flow_weight +
            vol_sig * self.volatility_weight +
            macro_sig * self.macro_weight +
            ml_sig * self.ml_weight
        )
        
        # 入场
        if score >= 0.6:
            return 'LONG'
        elif score <= -0.6:
            return 'SHORT'
        return 'WAIT'
```

---

## 下一步

1. **回测验证** → 用历史数据跑
2. **实盘模拟** → MT5模拟账户
3. **实盘** → 逐步上仓位

---

*策略框架完成 - 2026-03-16*
