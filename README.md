# AIcoin - Bitcoin Price Prediction Platform

🚀 比特币价格预测平台 - 历史K线图表 & 未来6个月走势预测，用于量化分析

## 功能特性

- 📊 **历史K线图表**: 展示比特币历史价格的专业K线图（开盘价、收盘价、最高价、最低价）
- 🔮 **未来走势预测**: 基于多种算法预测未来6个月的价格走势
- 📈 **技术指标**: MA(移动平均线)、EMA、BOLL(布林带)等常用量化指标
- 🎯 **量化分析面板**: 提供关键预测数据、置信区间和风险评估
- 🌓 **深色/浅色主题**: 支持主题切换，适应不同使用场景

## 预测算法

1. **线性回归预测** - 基于历史趋势的线性外推
2. **移动平均预测** - 基于加权移动平均的趋势延伸
3. **综合预测** - 结合多种模型的加权平均预测

## 技术栈

- **前端**: HTML5 + CSS3 + Vanilla JavaScript
- **图表库**: [Lightweight Charts](https://github.com/nickvdyck/nickvdyck.github.io) by TradingView
- **数据源**: CoinGecko API (免费公开API)
- **部署**: GitHub Pages (静态站点)

## 快速开始

### 方式一：GitHub Pages 部署
1. Fork 本仓库
2. 进入仓库 Settings → Pages
3. Source 选择 `main` 分支，目录选择 `/ (root)`
4. 保存后等待部署完成，访问 `https://<username>.github.io/AIcoin`

### 方式二：本地运行
```bash
git clone https://github.com/dodmagic/AIcoin.git
cd AIcoin
# 使用任意静态服务器，例如：
npx serve .
# 或
python -m http.server 8080
```

## 项目结构

```
AIcoin/
├── index.html          # 主页面
├── css/
│   └── style.css       # 样式文件
├── js/
│   ├── app.js          # 主应用逻辑
│   ├── chart.js        # K线图表渲染
│   ├── prediction.js   # 预测算法引擎
│   └── api.js          # 数据获取接口
├── assets/             # 静态资源
└── README.md
```

## ⚠️ 免责声明

本项目仅供学习和研究目的，预测结果不构成任何投资建议。加密货币市场波动剧烈，请谨慎投资。

## License

MIT License
