# XAUUSD 001号因子 - 新闻趋势因子
> 版本: v1.0 | 更新: 2026-03-16
> 状态: 🟢 活跃

---

## 因子定位

**001号因子** = 主流外媒黄金新闻情绪指数

不是简单的正能量/负能量，而是**机构级新闻定价**。

---

## 数据源 (权重)

| 来源 | 权重 | 优先级 |
|------|------|--------|
| Reuters 黄金/大宗商品 | 30% | P0 |
| Bloomberg 黄金市场 | 30% | P0 |
| CNBC 大宗商品 | 15% | P1 |
| Financial Times 市场 | 10% | P1 |
| WSJ 市场新闻 | 10% | P2 |
| 金十数据/华尔街见闻 | 5% | P2 |

---

## 抓取模块

```python
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json

class GoldNewsFetcher:
    """主流外媒黄金新闻抓取器"""
    
    SOURCES = {
        'reuters': {
            'url': 'https://www.reuters.com/markets/commodities/gold/',
            'selector': 'article',
            'weight': 0.30
        },
        'bloomberg': {
            'url': 'https://www.bloomberg.com/markets/commodities/gold',
            'selector': 'article',
            'weight': 0.30
        },
        'cnbc': {
            'url': 'https://www.cnbc.com/investing/commodities/gold/',
            'selector': 'article',
            'weight': 0.15
        },
        'ft': {
            'url': 'https://www.ft.com/markets/commodities',
            'selector': 'article',
            'weight': 0.10
        },
        'wsj': {
            'url': 'https://www.wsj.com/news/markets/gold',
            'selector': 'article',
            'weight': 0.10
        }
    }
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.session = requests.Session()
    
    def fetch_all(self, hours=24):
        """抓取过去N小时的新闻"""
        all_news = []
        
        for source, config in self.SOURCES.items():
            try:
                news = self._fetch_source(source, config, hours)
                all_news.extend(news)
            except Exception as e:
                print(f"[{source}] 抓取失败: {e}")
        
        # 按时间排序
        all_news.sort(key=lambda x: x['publish_time'], reverse=True)
        
        return all_news
    
    def _fetch_source(self, source, config, hours):
        """抓取单个来源"""
        response = self.session.get(
            config['url'], 
            headers=self.headers,
            timeout=10
        )
        
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.select(config['selector'])
        
        news_list = []
        cutoff = datetime.now() - timedelta(hours=hours)
        
        for article in articles[:20]:  # 取最新20条
            try:
                title = article.get_text(strip=True)[:200]
                link = article.find('a')
                url = link.get('href') if link else ''
                
                # 过滤黄金相关
                if not self._is_gold_related(title):
                    continue
                
                news_list.append({
                    'source': source,
                    'title': title,
                    'url': url,
                    'publish_time': datetime.now(),  # 简化处理
                    'weight': config['weight']
                })
            except:
                continue
        
        return news_list
    
    def _is_gold_related(self, title):
        """过滤黄金相关标题"""
        gold_keywords = [
            'gold', 'goldman', 'gold:', 'xauusd', 'xau',
            'bullion', 'precious metal', 'fed', 'fomc',
            'inflation', 'real yield', 'tips', 'dxy',
            'dollar', 'usd', 'central bank', 'powell'
        ]
        
        title_lower = title.lower()
        return any(kw in title_lower for kw in gold_keywords)
```

---

## 情绪分析模块

```python
from transformers import pipeline
import torch

class GoldSentimentAnalyzer:
    """黄金专用情绪分析"""
    
    def __init__(self):
        # 使用金融领域模型
        self.sentiment = pipeline(
            "sentiment-analysis",
            model="ProsusAI/finbert",
            device=-1  # CPU
        )
        
        # 黄金相关关键词权重
        self.bullish_keywords = [
            'bullish', 'rise', 'rally', 'surge', 'gain',
            'higher', 'strong', 'buy', 'upgrade', 'outperform',
            'safe haven', 'hedge', 'inflation hedge', 'uncertainty',
            'geopolitical', 'tension', 'conflict', 'war'
        ]
        
        self.bearish_keywords = [
            'bearish', 'fall', 'drop', 'decline', 'sell',
            'lower', 'weak', 'downgrade', 'underperform',
            'profit taking', 'pullback', 'correction',
            'fed hawkish', 'rate hike', 'dollar strength'
        ]
    
    def analyze(self, news_list):
        """分析新闻情绪"""
        results = []
        
        for news in news_list:
            title = news['title']
            
            # 1. FinBERT分析
            bert_result = self.sentiment(title[:512])[0]
            
            # 2. 关键词增强
            keyword_score = self._keyword_score(title)
            
            # 3. 加权得分
            final_score = 0.7 * self._label_to_score(bert_result) + 0.3 * keyword_score
            
            results.append({
                'source': news['source'],
                'title': title,
                'bert_score': bert_result['score'],
                'bert_label': bert_result['label'],
                'keyword_score': keyword_score,
                'final_score': final_score,
                'weight': news['weight']
            })
        
        return results
    
    def _label_to_score(self, result):
        """转换标签到分数"""
        if result['label'] == 'positive':
            return result['score']
        elif result['label'] == 'negative':
            return -result['score']
        return 0
    
    def _keyword_score(self, title):
        """关键词打分"""
        title_lower = title.lower()
        
        bullish_count = sum(1 for kw in self.bullish_keywords if kw in title_lower)
        bearish_count = sum(1 for kw in self.bearish_keywords if kw in title_lower)
        
        total = bullish_count + bearish_count
        if total == 0:
            return 0
        
        return (bullish_count - bearish_count) / total
```

---

## 趋势因子计算

```python
class GoldTrendFactor:
    """001号因子 - 新闻趋势因子"""
    
    def __init__(self):
        self.fetcher = GoldNewsFetcher()
        self.analyzer = GoldSentimentAnalyzer()
        
        # 因子参数
        self.lookback_hours = 24  # 抓取过去24小时
        self.min_news_count = 5   # 最小新闻数
        
        # 阈值
        self.bullish_threshold = 0.3   # 看多阈值
        self.bearish_threshold = -0.3  # 看空阈值
    
    def calculate(self):
        """计算001号因子"""
        # 1. 抓取新闻
        news = self.fetcher.fetch_all(hours=self.lookback_hours)
        
        if len(news) < self.min_news_count:
            return {
                'status': 'insufficient_data',
                'news_count': len(news),
                'factor_value': 0,
                'signal': 'NEUTRAL'
            }
        
        # 2. 情绪分析
        sentiments = self.analyzer.analyze(news)
        
        # 3. 计算加权得分
        total_weight = sum(s['weight'] for s in sentiments)
        weighted_score = sum(s['final_score'] * s['weight'] for s in sentiments) / total_weight
        
        # 4. 时间衰减
        recency_score = self._recency_decay(sentiments)
        
        # 5. 综合因子
        factor_value = 0.6 * weighted_score + 0.4 * recency_score
        
        # 6. 信号
        signal = self._get_signal(factor_value)
        
        return {
            'status': 'ok',
            'factor_value': round(factor_value, 4),
            'signal': signal,
            'news_count': len(news),
            'weighted_sentiment': round(weighted_score, 4),
            'recency_score': round(recency_score, 4),
            'sources': list(set(s['source'] for s in sentiments)),
            'top_headlines': [s['title'][:80] for s in sentiments[:5]]
        }
    
    def _recency_decay(self, sentiments):
        """时间衰减加权"""
        decay_factor = 0.9  # 每条新闻衰减10%
        
        scores = []
        for i, s in enumerate(sentiments):
            decay = decay_factor ** i
            scores.append(s['final_score'] * decay)
        
        return sum(scores) / len(scores) if scores else 0
    
    def _get_signal(self, factor_value):
        """生成交易信号"""
        if factor_value >= self.bullish_threshold:
            return 'STRONG_BUY' if factor_value >= 0.5 else 'BUY'
        elif factor_value <= self.bearish_threshold:
            return 'STRONG_SELL' if factor_value <= -0.5 else 'SELL'
        return 'NEUTRAL'
```

---

## 因子输出示例

```json
{
  "factor_id": "001",
  "factor_name": "新闻趋势因子",
  "timestamp": "2026-03-16T16:00:00Z",
  "factor_value": 0.4235,
  "signal": "BUY",
  "confidence": 0.72,
  "details": {
    "news_count": 28,
    "weighted_sentiment": 0.38,
    "recency_score": 0.51,
    "sources": ["reuters", "bloomberg", "cnbc"],
    "top_headlines": [
      "Gold rallies to new high as inflation fears mount",
      "Fed signals pause on rate hikes, gold surges",
      "Central banks accelerate gold purchases",
      "Geopolitical tensions boost safe-haven demand",
      "Goldman upgrades gold to overweight"
    ]
  }
}
```

---

## 信号定义

| 因子值 | 信号 | 含义 |
|--------|------|------|
| >= 0.5 | 🟢🟢 STRONG_BUY | 机构强烈看多 |
| 0.3 ~ 0.5 | 🟢 BUY | 看多 |
| -0.3 ~ 0.3 | 🟡 NEUTRAL | 中性 |
| -0.5 ~ -0.3 | 🔴 SELL | 看空 |
| <= -0.5 | 🔴🔴 STRONG_SELL | 机构强烈看空 |

---

## 今日因子值 (2026-03-16)

> 需要运行脚本获取实时值

```bash
python gold_news_factor.py
```

---

## 后续优化

- [ ] 接入Bloomberg Terminal API
- [ ] 接入Reuters Data API
- [ ] 添加新闻影响持续时间模型
- [ ] 添加反向新闻信号检测
- [ ] 与COT报告持仓对比验证

---

*001号因子完成 - 2026-03-16*
