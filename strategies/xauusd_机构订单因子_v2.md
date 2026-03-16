# XAUUSD 顶级机构订单因子库
> 版本: v2.0 | 更新: 2026-03-16

---

## 核心理念

**不做烂大街的成交量/持仓量**，只追踪**真实主力行为信号**。

---

## 因子1: 流动性耗尽 (Liquidity Sweep)

### 逻辑
机构从不直接追涨杀跌，而是**先扫掉散户流动性**，然后反转。

### 识别条件
```
1. 快速突破近期高低点 (15分钟内 > 30点)
2. 伴随成交量放大 (> 均量3倍)
3. 突破后30分钟内反转 > 50%
4. 形成订单块 (Order Block) 在突破点下方
```

### 量化表达
```python
def liquidity_sweep(df, lookback=20):
    high = df['high'].rolling(lookback).max()
    low = df['low'].rolling(lookback).min()
    
    # 向上 sweep
    sweep_up = (df['close'] > high.shift(1)) & (df['close'].shift(-1) < high)
    
    # 向下 sweep  
    sweep_down = (df['close'] < low.shift(1)) & (df['close'].shift(-1) > low)
    
    # 成交量确认
    vol_spike = df['volume'] > df['volume'].rolling(20).mean() * 3
    
    return sweep_up & vol_spike, sweep_down & vol_spike
```

---

## 因子2: 暗池流动性分布 (Dark Pool Liquidity)

### 逻辑
CME期货80%交易发生在电子交易平台外，这些**暗池订单**是真正支撑位/阻力位。

### 数据源
- CME Fixing (上午/下午定盘价)
- COMEX黄金期货未平仓合约分布 (OCR)
- LBMA黄金定盘价 (上午/下午)

### 识别条件
```
1. 价格接近暗池买单密集区 (支撑)
2. 价格接近暗池卖单密集区 (阻力)
3. 暗池流动性被"吃掉"后快速反弹
```

### 量化表达
```python
def dark_pool_zones(cme_levels, premium_levels):
    """计算暗池支撑/阻力区"""
    support_zones = cme_levels[cme_levels['type'] == 'bid']['price'].quantile([0.7, 0.9])
    resistance_zones = cme_levels[cme_levels['type'] == 'ask']['price'].quantile([0.1, 0.3])
    
    return support_zones, resistance_zones
```

---

## 因子3: 订单块确认 (Order Block)

### 逻辑
机构建仓后，会在特定区域形成**订单块**，价格回到该区域时会获得支撑/阻力。

### 识别条件
```
1. 连续3根K线同一方向 (机构建仓)
2. 随后出现至少5根K线回调
3. 价格回到建仓区域 > 70%回撤
4. 出现Pin Bar /吞没形态确认
```

### 量化表达
```python
def find_order_blocks(df, min_consecutive=3, min_retrace=5):
    blocks = []
    consecutive = 0
    start_idx = 0
    
    for i in range(len(df)):
        # 连续同方向K线
        if df['close'].iloc[i] > df['open'].iloc[i]:
            if consecutive == 0:
                start_idx = i
            consecutive += 1
        else:
            if consecutive >= min_consecutive:
                blocks.append({
                    'start': start_idx,
                    'end': i-1,
                    'type': 'bullish',
                    'zone': df.loc[start_idx:i-1, 'low'].min()
                })
            consecutive = 0
    
    return blocks
```

---

## 因子4: ETF持仓突变 (SLV/GLD Flow)

### 逻辑
黄金ETF是**散户+机构最大持仓载体**，单日净申购/赎回 > 5亿美元 = 重大信号。

### 监控
| 指标 | 阈值 | 信号 |
|------|------|------|
| GLD净流入 | > +5亿美元/日 | 🟢 强势看涨 |
| GLD净流出 | > -5亿美元/日 | 🔴 强势看跌 |
| SLV/GLD比率 | > 2周均值+10% | 🟡 银强金弱 |
| 持仓集中度 | > 70%在前10大持仓 | 🟡 机构控盘 |

### 数据源
- iShares GLD 持仓变化
- iShares SLV 持仓变化
- 黄金ETF溢价/折价

---

## 因子5: COT持仓报告 (Commitments of Traders)

### 逻辑
CFTC每周发布的COT报告披露**大型投机商**和**商业套保商**净头寸。

### 核心指标
| 指标 | 含义 | 信号 |
|------|------|------|
| Large Speculators净多头 | 对冲基金/大户 | > 200,000手 = 超买 |
| Commercials净空头 | 黄金生产商 | 极端空头 = 底部信号 |
| Commercials净多头 | 黄金消费商 | 极端多头 = 顶部信号 |
| 净头寸变化 | 每周变化 | 连续3周同向 = 趋势形成 |

### 量化表达
```python
def cot_signal(cot_data):
    spec_net = cot_data['large_speculators_net']
    comm_net = cot_data['commercials_net']
    
    # 商业机构极端信号
    if comm_net < -300000:  # 生产商大量套保空头
        return 'BULLISH_REVERSAL'  # 可能见底
    elif comm_net > 100000:  # 消费商大量采购
        return 'BEARISH_REVERSAL'  # 可能见顶
    
    # 投机商信号
    if spec_net > 250000:
        return 'OVERBOUGHT'
    elif spec_net < -100000:
        return 'OVERSOLD'
    
    return 'NEUTRAL'
```

---

## 因子6: 波动率指纹 (Volatility Fingerprint)

### 逻辑
黄金期货和现货的**波动率差异**揭示机构行为。

### 指标
| 指标 | 计算 | 信号 |
|------|------|------|
| COMEX期现价差 | 期货价格 - 现货价格 | > $50 = 期货溢价(Contango) = 机构看涨 |
| GVZ vs VIX | 黄金波动率/美股波动率 | GVZ > VIX = 黄金风险溢价高 |
| 期限结构 | 3月期货 / 1月期货 | Contango > 2% = 机构看涨 |

---

## 综合信号

```python
def institutional_score(df, cot_data, etf_flow, cme_levels):
    score = 0
    
    # 流动性耗尽
    sweep_up, sweep_down = liquidity_sweep(df)
    if sweep_up: score += 2
    if sweep_down: score -= 2
    
    # 订单块
    blocks = find_order_blocks(df)
    if in_order_block(df['close'].iloc[-1], blocks):
        if blocks[-1]['type'] == 'bullish':
            score += 1
        else:
            score -= 1
    
    # ETF流向
    if etf_flow > 500_000_000:
        score += 2
    elif etf_flow < -500_000_000:
        score -= 2
    
    # COT
    cot = cot_signal(cot_data)
    if cot == 'BULLISH_REVERSAL': score += 3
    elif cot == 'OVERBOUGHT': score -= 2
    
    return score
```

---

## 信号阈值

| 综合分数 | 交易建议 |
|----------|----------|
| >= 4 | 强买 |
| 2-3 | 轻仓买 |
| -1 to 1 | 观望 |
| -2 to -3 | 轻仓卖 |
| <= -4 | 强卖 |

---

*顶级机构订单因子完成 - 2026-03-16*
