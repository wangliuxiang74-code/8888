# XAUUSD 顶级波动率因子库
> 版本: v2.0 | 更新: 2026-03-16

---

## 核心理念

**波动率是黄金的血压**，不是用来预测方向的，而是用来**定价风险**和**识别流动性事件**的。

---

## 因子1: 波动率期限结构 (Volatility Term Structure)

### 逻辑
机构通过波动率期货/期权定价未来风险，**期限结构**揭示市场预期。

### 关键指标
| 指标 | 计算 | 信号 |
|------|------|------|
| 3M/1M期限价差 | (黄金3月IV - 1月IV) | > 2% = Contango = 机构预期风险上升 |
| 6M/3M期限价差 | (黄金6月IV - 3月IV) | > 3% = 远期风险溢价高 |
| 期限结构斜率 | 线性回归斜率 | > 0.5 = 上涨趋势 |

### 量化表达
```python
def vol_term_structure(gvz_curve):
    """
    GVZ = CBOE黄金波动率指数
    """
    # 前端波动率
    front_vol = gvz_curve['1M']
    # 远期波动率  
    deferred_vol = gvz_curve['3M']
    
    term_spread = deferred_vol - front_vol
    
    if term_spread > 2:
        return 'CONTANGO', term_spread  # 机构预期风险上升
    elif term_spread < -1:
        return 'BACKWARDATION', term_spread  # 风险偏好回升
    else:
        return 'FLAT', term_spread
```

---

## 因子2: IV-HV价差 (Implied vs Historical)

### 逻辑
**隐含波动率(IV)** 是市场定价，**历史波动率(HV)** 是实际发生。IV > HV = 波动率溢价 = 保险费贵 = 机构避险。

### 阈值
| IV - HV | 市场定价 | 建议 |
|---------|----------|------|
| > +5% | 波动率溢价高 | 买入黄金作为保险 |
| -5% ~ +5% | 合理 | 中性 |
| < -5% | 波动率折价 | 黄金避险需求弱 |

### 量化表达
```python
def iv_hv_spread(gold_iv, gold_hv):
    spread = gold_iv - gold_hv
    
    if spread > 5:
        return 'VOLATILITY_PREMIUM', 'BUY_GOLD'  # 波动率溢价高
    elif spread < -5:
        return 'VOLATILITY_DISCOUNT', 'NEUTRAL'  # 折价
    else:
        return 'FAIR', 'NEUTRAL'
```

---

## 因子3: 黄金VIX (GVZ) 与 VIX 联动

### 逻辑
**GVZ** = 黄金波动率指数，**VIX** = 美股恐慌指数。两者相关性揭示资金流向。

### 关系
| 关系 | 含义 | 信号 |
|------|------|------|
| GVZ > VIX | 黄金风险溢价 > 美股 | 🟢 黄金避险需求强 |
| GVZ < VIX | 黄金风险溢价 < 美股 | 🔴 资金流向美股 |
| GVZ突然飙升+VIX平稳 | 黄金特有风险 | 🟡 地缘/央行事件 |

### 量化表达
```python
def gvz_vix_regime(gvz, vix):
    ratio = gvz / vix
    
    if ratio > 1.2:
        return 'GOLD_RISK_PREMIUM', 1  # 黄金避险强
    elif ratio < 0.8:
        return 'EQUITY_RISK_PREMIUM', -1  # 美股避险强
    else:
        return 'BALANCED', 0
```

---

## 因子4: 波动率微笑 (Vol Smile)

### 逻辑
期权市场的**波动率微笑**揭示尾部风险定价。虚值期权(OTM)波动率陡峭 = 市场害怕黑天鹅。

### 指标
| 形态 | 含义 | 信号 |
|------|------|------|
| 左偏(put skew) | 下跌风险溢价高 | 🟢 黄金看涨 |
| 右偏(call skew) | 上涨风险溢价高 | 🔴 黄金看跌 |
| 对称 | 市场中性 | 🟡 |

### 量化表达
```python
def vol_smile_skew(otm_put_iv, otm_call_iv, atm_iv):
    """
    ATM = At The Money
    OTM = Out of The Money
    """
    put_skew = atm_iv - otm_put_iv  # 虚值看跌期权IV
    call_skew = atm_iv - otm_call_iv  # 虚值看涨期权IV
    
    if put_skew > call_skew + 2:
        return 'LEFT_SKEW', 'BEARISH_PROTECTION'  # 防跌
    elif call_skew > put_skew + 2:
        return 'RIGHT_SKEW', 'BULLISH_PROTECTION'  # 防涨
    else:
        return 'SYMMETRIC', 'NEUTRAL'
```

---

## 因子5: 流动性事件预警 (Liquidity Event)

### 逻辑
黄金在**流动性事件**(央行决议、地缘冲突)前后波动率特征不同。

### 事件日历
| 事件 | 预期波动率 | 最佳策略 |
|------|------------|----------|
| FOMC会议 | IV急升 | 买入跨式期权(Straddle) |
| 非农数据 | HV急升 | 事件前做多波动率 |
| 地缘冲突 | GVZ飙升 | 买入黄金 |
| 央行降息 | IV-HV扩大 | 黄金多头 |

### 量化表达
```python
def liquidity_event_signal(hist_vol, event_calendar):
    days_to_event = min([(event - today).days for event in event_calendar])
    
    if days_to_event <= 3:
        # 事件临近，波动率预期上升
        return 'EVENT_WINDOW', hist_vol * 1.5
    elif days_to_event <= 7:
        return 'PRE_EVENT', hist_vol * 1.2
    else:
        return 'NORMAL', hist_vol
```

---

## 因子6: 波动率突破 (Volatility Breakout)

### 逻辑
波动率从**低位突破**往往预示大行情。

### 识别条件
```
1. 波动率处于20日低位 (< 20日均值 - 1.5标准差)
2. 3日内波动率上升 > 30%
3. 伴随价格突破关键位
4. 成交量配合
```

### 量化表达
```python
def vol_breakout(gvz, threshold=1.5):
    mv = gvz.rolling(20).mean()
    std = ggv.rolling(20).std()
    
    # 低位突破信号
    if gvz < mv - threshold * std:
        # 3日涨幅
        vol_change = (gvz - gvz.shift(3)) / gvz.shift(3)
        
        if vol_change > 0.3:
            return 'VOLATILITY_BREAKOUT', 'BULLISH'
        elif vol_change > 0.15:
            return 'VOLATILITY_BREAKOUT', 'NEUTRAL'
    
    return 'NORMAL', 'NEUTRAL'
```

---

## 综合信号

```python
def volatility_composite_score(gvz_curve, gold_iv, gold_hv, gvz, vix, event_calendar):
    score = 0
    
    # 期限结构
    term_regime, term_val = vol_term_structure(gvz_curve)
    if term_regime == 'CONTANGO':
        score += 2
    elif term_regime == 'BACKWARDATION':
        score -= 1
    
    # IV-HV价差
    premium_regime, _ = iv_hv_spread(gold_iv, gold_hv)
    if premium_regime == 'VOLATILITY_PREMIUM':
        score += 2
    
    # GVZ/VIX联动
    risk_regime, risk_val = gvz_vix_regime(gvz, vix)
    score += risk_val
    
    # 事件预警
    event_regime, vol_mult = liquidity_event_signal(gold_hv, event_calendar)
    if event_regime in ['EVENT_WINDOW', 'PRE_EVENT']:
        score += 1
    
    return score
```

---

## 信号阈值

| 综合分数 | 交易建议 |
|----------|----------|
| >= 4 | 强买黄金 (波动率定价过高) |
| 2-3 | 轻仓买 |
| -1 to 1 | 观望 |
| -2 to -3 | 回避黄金 |
| <= -4 | 做空黄金 |

---

*顶级波动率因子完成 - 2026-03-16*
