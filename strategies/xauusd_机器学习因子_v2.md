# XAUUSD 顶级机器学习因子库
> 版本: v2.0 | 更新: 2026-03-16

---

## 核心理念

**不用LSTM/Transformer做价格预测**——那是玄学。用ML做**风险定价**和**特征提取**。

---

## 因子1: 波动率预测 (Volatility Forecasting)

### 逻辑
用ML预测**未来波动率**，然后用波动率曲线定价期权/期货。

### 模型
```python
# GARCH + LSTM 混合模型
class VolatilityModel:
    def __init__(self):
        self.garch = arch.arch_model(returns, vol='Garch', p=1, q=1)
        self.lstm = tf.keras.Sequential([
            LSTM(64, return_sequences=True, input_shape=(20, 10)),
            LSTM(32),
            Dense(1, activation='relu')
        ])
    
    def predict(self, features):
        # GARCH 条件波动率
        garch_vol = self.garch.fit().conditional_volatility
        
        # LSTM 预测偏差
        lstm_pred = self.lstm.predict(features)
        
        # 融合
        final_vol = 0.7 * garch_vol + 0.3 * lstm_pred
        
        return final_vol
```

### 信号
| 预测波动率 | 实际波动率 | 信号 |
|------------|-------------|------|
| 低估 | 高于预测 | 🟡 波动率骤增预警 |
| 高估 | 低于预测 | 🟡 波动率收窄 |

---

## 因子2: 资金流预测 (Money Flow Prediction)

### 逻辑
用**资金流特征**预测价格短期方向。不是预测价格，而是预测**订单簿失衡**。

### 特征工程
```python
def extract_money_flow_features(df):
    features = {
        # 成交量分布
        'volume_mean': df['volume'].rolling(20).mean(),
        'volume_std': df['volume'].rolling(20).std(),
        'volume_skew': df['volume'].rolling(20).skew(),
        
        # 价量相关性
        'price_volume_corr': df['close'].rolling(20).corr(df['volume']),
        
        # 资金流方向
        'money_flow': (df['close'] - df['open']) * df['volume'],
        'money_flow_ma': df['money_flow'].rolling(10).mean(),
        
        # 订单簿压力
        'bid_ask_spread': df['ask'] - df['bid'],
        'order_imbalance': (df['bid_volume'] - df['ask_volume']) / 
                          (df['bid_volume'] + df['ask_volume'])
    }
    return pd.DataFrame(features)
```

### 模型训练
```python
# XGBoost 分类器
model = xgb.XGBClassifier(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,
    objective='binary:logistic'
)

# 标签：未来1小时涨跌
y = (df['close'].shift(-1) > df['close']).astype(int)
```

---

## 因子3: 文本情绪因子 (NLP Sentiment)

### 逻辑
用NLP从**新闻/社交媒体**提取黄金情绪。不是烂大街的VADER，而是**领域预训练模型**。

### 数据源
| 来源 | 权重 | 更新频率 |
|------|------|----------|
| Reuters黄金新闻 | 30% | 实时 |
| Bloomberg黄金新闻 | 30% | 实时 |
| Twitter/X $GOLD | 20% | 实时 |
| Reddit r/wallstreetbets | 10% | 日更 |
| 央行声明 | 10% | 事件驱动 |

### 模型
```python
# FinBERT 金融领域预训练模型
from transformers import BertTokenizer, BertForSequenceClassification

class GoldSentimentModel:
    def __init__(self):
        self.tokenizer = BertTokenizer.from_pretrained('ProsusAI/finbert')
        self.model = BertForSequenceClassification.from_pretrained(
            'ProsusAI/finbert',
            num_labels=3
        )
    
    def predict(self, text):
        inputs = self.tokenizer(text, return_tensors='pt', truncation=True, max_length=512)
        outputs = self.model(**inputs)
        probs = torch.softmax(outputs.logits, dim=1)
        
        return {
            'bullish': probs[0][0].item(),
            'neutral': probs[0][1].item(),
            'bearish': probs[0][2].item()
        }
```

### 信号
| 情绪 | 分数 | 信号 |
|------|------|------|
| Bullish | > 0.65 | 🟢 买 |
| Bearish | > 0.65 | 🔴 卖 |
| Neutral | 其他 | 🟡 观望 |

---

## 因子4: SHAP特征重要性 (Explainable ML)

### 逻辑
用**SHAP**解释模型决策，找出真正影响黄金价格的**因子贡献**。

### 代码
```python
import shap

# 训练好的XGBoost模型
model = xgb.XGBClassifier()
model.fit(X_train, y_train)

# SHAP解释器
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test)

# 绘制特征重要性
shap.summary_plot(shap_values, X_test, feature_names=feature_names)
```

### 典型因子重要性排序
```
1. 实际利率 (TIPS Yield)        ████████████████████ 35%
2. 美元指数 (DXY)               ███████████████ 25%
3. 波动率 (GVZ)                 ██████████ 15%
4. 央行购金                     ███████ 10%
5. 风险偏好 (HYG-LQD)           █████ 8%
6. 技术形态                     ███ 5%
7. 季节性                       █ 2%
```

---

## 因子5: 异常检测 (Anomaly Detection)

### 逻辑
用**Isolation Forest**检测异常事件(央行干预、地缘冲突)，这些事件后黄金往往大涨。

### 代码
```python
from sklearn.ensemble import IsolationForest

# 特征
features = ['returns', 'volume', 'volatility', ' turnover']
X = df[features]

# 异常检测模型
iso_forest = IsolationForest(
    contamination=0.02,  # 2%异常
    n_estimators=200
)

df['anomaly'] = iso_forest.fit_predict(X)
anomalies = df[df['anomaly'] == -1]

# 异常事件后黄金表现
print("异常事件后平均收益:", anomalies['close'].pct_change().mean())
```

### 信号
| 异常类型 | 黄金反应 | 信号 |
|----------|----------|------|
| 波动率异常 | 🟢 上涨 | 买 |
| 成交量异常 | 🟡 不确定 | 观察 |
| 价量背离 | 🔴 可能反转 | 卖 |

---

## 因子6: 强化学习做市 (RL Market Making)

### 逻辑
用**Q-Learning**训练黄金做市策略，学习最佳报价。

### 框架
```python
class GoldMarketMaker:
    def __init__(self):
        self.q_table = {}
        self.gamma = 0.9  # 折扣因子
        self.alpha = 0.1  # 学习率
        self.epsilon = 0.1  # 探索率
    
    def get_action(self, state):
        if random.random() < self.epsilon:
            return random.choice(['bid', 'ask', 'hold'])
        return max(self.q_table.get(state, {}).items(), 
                  key=lambda x: x[1])[0]
    
    def update(self, state, action, reward, next_state):
        old_q = self.q_table.get(state, {}).get(action, 0)
        max_next_q = max(self.q_table.get(next_state, {}).values(), default=0)
        
        new_q = old_q + self.alpha * (reward + self.gamma * max_next_q - old_q)
        
        if state not in self.q_table:
            self.q_table[state] = {}
        self.q_table[state][action] = new_q
```

### 状态空间
- 订单簿深度
- 当前波动率
- 库存风险
- 市场情绪

---

## 因子7: 跨界特征迁移 (Cross-Asset Transfer Learning)

### 逻辑
用**其他资产**训练的特征迁移到黄金。

### 迁移资产
| 源资产 | 特征 | 迁移效果 |
|--------|------|----------|
| 原油 | 通胀预期 | 🟢🟢 强 |
| 美债 | 流动性 | 🟢 强 |
| 比特币 | 风险偏好 | 🟡 中 |
| 欧元 | 美元 | 🟢 强 |

### 代码
```python
# 用原油数据预训练
oil_model = train_model(oil_features, oil_returns)

# 迁移到黄金
gold_features_adapted = adapt_features(gold_features, oil_features)
gold_model = transfer_learning(oil_model, gold_features_adapted)
```

---

## 因子8: 组合预测 (Ensemble Prediction)

### 逻辑
不依赖单一模型，用**多模型投票**。

### 组合
```python
class GoldEnsemble:
    def __init__(self):
        self.models = {
            'xgboost': XGBClassifier(),
            'lstm': LSTMModel(),
            'transformer': TransformerModel(),
            'random_forest': RandomForestClassifier()
        }
        self.weights = [0.35, 0.25, 0.25, 0.15]
    
    def predict(self, X):
        preds = []
        for name, model in self.models.items():
            pred = model.predict_proba(X)[:, 1]
            preds.append(pred)
        
        # 加权平均
        weighted_pred = np.average(preds, weights=self.weights, axis=0)
        
        return weighted_pred
```

---

## 综合信号

```python
def ml_composite_score(vol_pred, money_flow_pred, sentiment_score, 
                       anomaly_detected, ensemble_pred):
    score = 0
    
    # 波动率预测
    if vol_pred > 1.5 * historical_vol:
        score += 2  # 波动率骤增
    
    # 资金流
    if money_flow_pred > 0.6:
        score += 2
    elif money_flow_pred < 0.4:
        score -= 2
    
    # 情绪
    if sentiment_score > 0.65:
        score += 1
    elif sentiment_score < 0.35:
        score -= 1
    
    # 异常检测
    if anomaly_detected:
        score += 2
    
    # 集成预测
    if ensemble_pred > 0.6:
        score += 2
    elif ensemble_pred < 0.4:
        score -= 2
    
    return score
```

---

## 信号阈值

| 综合分数 | 交易建议 |
|----------|----------|
| >= 5 | 强买 |
| 2-4 | 轻仓买 |
| -1 to 1 | 观望 |
| -2 to -4 | 轻仓卖 |
| <= -5 | 强卖 |

---

## 数据源

| 数据 | 来源 | 频率 |
|------|------|------|
| 价格/成交量 | CME/Bloomberg | 毫秒 |
| 订单簿 | L2报价 | 毫秒 |
| 新闻 | Reuters/Bloomberg | 实时 |
| 社交媒体 | Twitter/X API | 实时 |
| 央行数据 | IMF/SAFE | 月度 |

---

*顶级机器学习因子完成 - 2026-03-16*
