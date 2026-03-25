# SKILL.md - 跨境电商选品调研

## Description
帮助跨境电商卖家进行童装/玩具类目的选品调研，包括竞品分析、利润测算、趋势判断。

## When to Use
- 用户想选品、找爆款
- 分析竞品数据
- 计算产品利润
- 判断市场趋势

## Prerequisites
- 有具体想做的类目（童装/玩具/母婴）
- 已确定目标平台（Amazon/Shopee/Temu）
- 了解基础成本（工厂价、物流费）

## Workflow

### 1. 市场调研
使用 `web_search` 搜索目标类目的市场趋势：
- "{类目} 2024 2025 trending products"
- "{类目} best sellers Amazon"
- "{类目} 热销 趋势"

### 2. 竞品分析
- 抓取竞品Listing页面
- 分析价格、评价、卖点
- 统计差评痛点

### 3. 利润测算
计算公式：
```
利润 = 售价 - 工厂成本 - 物流 - 平台佣金 - 广告费 - 退货率
利润率 = 利润 / 售价
```

### 4. 输出报告
整理成表格：
| 产品 | 竞品价 | 预估成本 | 毛利 | 评分 | 竞争度 | 建议 |

## Example Usage

**用户**: "帮我调研下女童连衣裙"

**Agent**:
1. 搜索 "girls dress trending 2024 Amazon"
2. 抓取Top 10 Listing分析
3. 算利润（假设工厂价¥30，卖$19.99）
4. 输出报告

## Limitations
- 需要用户已知工厂成本
- 竞品数据是公开的，不保证实时
- 不提供具体供应商联系方式

## Files
- `references/product-research-template.md` - 选品报告模板

## Notes
- 童装注意：尺码、安全认证（CPC/CE）
- 玩具注意：年龄分级、材质安全
- 利润建议：毛利>30%才值得做
