# XAUUSD 顶级宏观因子库
> 版本: v2.0 | 更新: 2026-03-16

---

## 核心理念

**黄金是宏观定价的终极资产**，不是技术分析能解释的。顶级玩家只看央行资产负债表和信用体系。

---

## 因子1: 实际利率 (Real Yield)

### 逻辑
**黄金的机会成本 = 实际利率**。当实际利率为负，黄金是零成本资产。

### 公式
```
Real Yield = 名义利率 - 通胀预期
           = TIPS Yield (抗通胀债券收益率)
```

### 信号
| 实际利率 | 黄金表现 | 信号 |
|----------|----------|------|
| < -2% | 史上最强牛市 | 🟢🟢 爆赚 |
| -2% ~ 0% | 强势上涨 | 🟢 |
| 0% ~ 2% | 震荡 | 🟡 |
| > 2% | 弱势 | 🔴 |

### 量化表达
```python
def real_yield_signal(tips_yield, inflation_breakeven):
    real_yield = tips_yield  # TIPS收益率已经是实际利率
    
    if real_yield < -2:
        return 'DEEP_NEGATIVE', 3  # 黄金超级牛市
    elif real_yield < 0:
        return 'NEGATIVE', 2
    elif real_yield < 2:
        return 'POSITIVE', 0
    else:
        return 'HIGH_POSITIVE', -2
```

---

## 因子2: 美元信用体系 (USD Credit)

### 逻辑
黄金是**美元信用体系**的镜像。当美元信用扩张，黄金涨；信用收缩，黄金跌。

### 核心指标
| 指标 | 含义 | 信号 |
|------|------|------|
| 美联储资产负债表 | 美元流动性 | > 8万亿 = 黄金利好 |
| 逆回购规模 | 过剩流动性 | > 2万亿 = 流动性泛滥 = 黄金利好 |
| 银行准备金 | 贷出能力 | 上升 = 信用扩张 = 黄金利好 |
| M2货币供应 | 广义货币 | YOY > 10% = 货币超发 = 黄金利好 |

### 量化表达
```python
def usd_credit_signal(fed_balance_sheet, reverse_repo, m2_yoy):
    score = 0
    
    # 美联储资产负债表
    if fed_balance_sheet > 8_500_000_000_000:  # 8.5万亿
        score += 2
    elif fed_balance_sheet > 8_000_000_000_000:
        score += 1
    
    # 逆回购 (流动性过剩)
    if reverse_repo > 2_000_000_000_000:  # 2万亿
        score += 2
    elif reverse_repo > 1_500_000_000_000:
        score += 1
    
    # M2增速
    if m2_yoy > 10:
        score += 2
    elif m2_yoy > 5:
        score += 1
    
    return score
```

---

## 因子3: 美元指数权重货币 (DXY Weights)

### 逻辑
DXY = 57.6%欧元 + 13.6%日元 + ... 

**欧元/日元走势** = 美元50%以上命运。

### 货币联动
| 货币 | DXY权重 | 信号 |
|------|---------|------|
| EUR/USD | 57.6% | EUR涨 = DXY跌 = 黄金涨 🟢 |
| USD/JPY | 13.6% | JPY跌 = 黄金跌 🔴 |
| GBP/USD | 11.9% | 关联性中等 |
| USD/CAD | 9.1% | 油价关联 |

### 量化表达
```python
def dxy_weighted_signal(eurusd, usdjpy, gbpusd):
    # 欧元权重最高
    eur_signal = -1 if eurusd > eurusd.shift(20) else 1
    
    # 日元避险属性
    jpy_signal = 1 if usdjpy > 150 else 0  # JPY暴跌时黄金涨
    
    weighted = eur_signal * 0.576 + jpy_signal * 0.136
    
    if weighted < -0.3:
        return 'USD_WEAK', 2  # 黄金利好
    elif weighted > 0.3:
        return 'USD_STRONG', -2  # 黄金利空
    else:
        return 'NEUTRAL', 0
```

---

## 因子4: 全球央行购金 (Central Bank Gold)

### 逻辑
**央行是黄金最大单一买家**，2022年起全球央行净购金创历史新高。

### 监控
| 指标 | 阈值 | 信号 |
|------|------|------|
| 央行净购金 | > 50吨/月 | 🟢 多头 |
| 央行净售金 | > 20吨/月 | 🔴 空头 |
| 中国央行 | 连续3月增持 | 🟢🟢 强买 |
| 新兴市场央行 | 净购金增加 | 🟢 去美元化 |

### 数据源
- IMF IFS (国际收支)
- 世界黄金协会 (WGC)
- 中国外管局 (SAFE)
- 俄罗斯央行

### 量化表达
```python
def central_bank_signal(monthly_gold_buying, china_consecutive_months):
    score = 0
    
    if monthly_gold_buying > 500:  # 50吨
        score += 3
    elif monthly_gold_buying > 200:  # 20吨
        score += 1
    
    if china_consecutive_months >= 3:
        score += 2
    
    return score
```

---

## 因子5: 信用利差 (Credit Spread)

### 逻辑
**高收益债利差** = 市场风险偏好。利差扩大 = 风险厌恶 = 黄金涨。

### 指标
| 利差 | 含义 | 信号 |
|------|------|------|
| HYG (高收益债) - LQD (投资级债) | 信用风险溢价 | > 4% = 恐慌 = 黄金涨 🟢 |
| BBB级债 vs AAA级债 | 信用质量 | 扩大 = 经济担忧 = 黄金涨 |

### 量化表达
```python
def credit_spread_signal(hyg_lqd_spread, bbb_aaa_spread):
    # HYG-LQD 利差
    if hyg_lqd_spread > 4:
        risk_off = 3
    elif hyg_lqd_spread > 3:
        risk_off = 1
    elif hyg_lqd_spread > 2:
        risk_off = 0
    else:
        risk_off = -1
    
    # BBB-AAA 利差
    if bbb_aaa_spread > 1.5:
        credit_concern = 2
    elif bbb_aaa_spread > 1:
        credit_concern = 1
    else:
        credit_concern = 0
    
    return risk_off + credit_concern
```

---

## 因子6: 地缘Risk Premium (Geopolitical Risk)

### 逻辑
黄金是**终极避险资产**，地缘事件直接触发Risk Premium。

### 事件类型
| 事件 | 黄金反应 | 持续时间 |
|------|----------|----------|
| 中东战争 | 🟢🟢 +5-10% | 1-2周 |
| 朝鲜导弹 | 🟢 +2-3% | 2-3天 |
| 金融危机 | 🟢🟢 +20%+ | 几个月 |
| 贸易战 | 🟡 不确定 | 反复 |

### 量化表达
```python
def geopolitical_risk_signal(event_type, event_intensity):
    events = {
        'WAR': 3,           # 战争
        'CRISIS': 3,        # 金融危机
        'SANCTION': 2,      # 制裁
        'ELECTION': 1,       # 选举
        'TRADE_WAR': 1,     # 贸易战
        'NATURAL_DISASTER': 2  # 自然灾害
    }
    
    base = events.get(event_type, 0)
    intensity_mult = event_intensity / 10  # 1-10 scale
    
    return base * intensity_mult
```

---

## 因子7: 黄金/白银比率 (Gold/Silver Ratio)

### 逻辑
**金银比**是宏观情绪放大器。极端值揭示转折点。

### 信号
| 金银比 | 含义 | 信号 |
|--------|------|------|
| > 90 | 银被低估到极致 | 🟢 银将补涨 |
| < 65 | 金被低估 | 🔴 金将补涨 |
| 突破历史均值 | 趋势形成 | 顺势 |

### 量化表达
```python
def gold_silver_ratio_signal(ratio, historical_mean=70):
    z_score = (ratio - historical_mean) / ratio.rolling(20).std()
    
    if z_score > 2:  # 比历史均值高2个标准差
        return 'EXTREME_HIGH', 'SILVER_OUTPERFORM'  # 银将补涨
    elif z_score < -2:
        return 'EXTREME_LOW', 'GOLD_OUTPERFORM'  # 金将补涨
    else:
        return 'NORMAL', 'NEUTRAL'
```

---

## 综合信号

```python
def macro_composite_score(tips_yield, fed_bal, reverse_repo, m2_yoy, 
                          monthly_cb_buying, hyg_lqd_spread, gsr):
    score = 0
    
    # 实际利率
    ry = real_yield_signal(tips_yield)
    score += ry[1]
    
    # 美元信用
    credit = usd_credit_signal(fed_bal, reverse_repo, m2_yoy)
    score += credit
    
    # 央行购金
    cb = central_bank_signal(monthly_cb_buying)
    score += cb
    
    # 信用利差
    spread = credit_spread_signal(hyg_lqd_spread, 0)
    score += spread
    
    # 金银比
    gsr_sig = gold_silver_ratio_signal(gsr)
    if gsr_sig[1] == 'SILVER_OUTPERFORM':
        score += 1  # 银强时金银齐涨
    
    return score
```

---

## 信号阈值

| 综合分数 | 交易建议 |
|----------|----------|
| >= 6 | 强买 (宏观共振) |
| 3-5 | 轻仓买 |
| 0-2 | 观望 |
| -1 to -3 | 轻仓卖 |
| <= -4 | 强卖 |

---

*顶级宏观因子完成 - 2026-03-16*
