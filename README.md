# AIcoin - Bitcoin Price Prediction Platform

🚀 比特币价格预测平台 - **Python 量化后端 + 前端可视化**，提供专业的时间序列 / 机器学习预测与技术分析。

> ⚠️ 仅供学习和研究目的，预测结果不构成任何投资建议。加密货币市场波动剧烈，请谨慎投资。

---

## ✨ 功能特性

- 📊 **专业 K 线图表**：OHLCV 蜡烛图 + 成交量
- 🔮 **量化预测**：ARIMA / Prophet / LSTM / XGBoost / 集成(Ensemble)，预测线**带真实波动**，并输出 **80% / 95% 置信区间扇形**
- 📈 **10+ 技术指标**：MA / EMA / MACD / KDJ / RSI / BOLL / ATR / OBV / VWAP / 量比，全部在后端计算
- 🎯 **交易信号**：金叉 / 死叉 / 超买 / 超卖，自动在 K 线上标注买卖箭头
- 🧪 **回测评估**：MSE / MAE / RMSE / MAPE / 方向准确率
- 📐 **统计指标**：Sharpe 比率 / 最大回撤 / 胜率 / 年化波动
- 🌓 **深色/浅色主题**，后端离线时自动回退到本地 JS 预测引擎

---

## 🏗️ 架构

```
┌─────────────────┐         ┌──────────────────────┐
│  前端 (HTML/JS) │ ──API──▶│  Python 后端 (FastAPI)│
│  K线 + 预测扇形 │ ◀──────│  量化分析 + ML 预测   │
└─────────────────┘  JSON   └──────────────────────┘
                                      │
                                      ▼
                             ┌──────────────────┐
                             │ CoinGecko 数据    │
                             │  + SQLite 本地缓存│
                             └──────────────────┘
```

## 📦 项目结构

```
AIcoin/
├── index.html              # 前端主页面
├── css/style.css           # 样式
├── js/
│   ├── api.js              # CoinGecko 直连(前端回退用)
│   ├── backend.js          # Python 后端 API 客户端
│   ├── prediction.js       # 本地 JS 预测引擎(后端离线回退)
│   ├── chart.js            # K线 / 预测扇形 / 信号渲染
│   └── app.js              # 主应用逻辑
├── backend/                # ⭐ Python 量化后端
│   ├── main.py             # FastAPI 入口
│   ├── requirements.txt
│   ├── api/                # 路由 + Pydantic 模型
│   ├── data/               # 数据获取 / SQLite 缓存 / 清洗
│   ├── indicators/         # MA/EMA/MACD/KDJ/RSI/BOLL/ATR/OBV/VWAP + 信号
│   ├── models/             # ARIMA / Prophet / LSTM / XGBoost / Ensemble
│   ├── backtest/           # 回测 + 评估指标
│   └── tests/              # pytest
├── Dockerfile
├── docker-compose.yml
└── .github/workflows/ci.yml
```

---

## 🚀 快速开始

### 方式一：Docker Compose（推荐，一键启动后端 + 前端）

```bash
docker-compose up --build
```

- 后端 API: <http://localhost:8000>（交互式文档 <http://localhost:8000/docs>）
- 前端页面: <http://localhost:8080>

### 方式二：本地运行后端 + 前端

```bash
# 1. 启动后端
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000

# 2. 另开一个终端，启动前端静态服务器
python -m http.server 8080
# 浏览器访问 http://localhost:8080
```

前端默认连接 `http://localhost:8000`。可在页面顶部 **量化后端** 输入框中填写其它地址，
也可用查询参数覆盖：`http://localhost:8080/?backend=https://your-host`。
若后端不可用，前端会自动回退到内置的本地 JS 预测引擎。

### 可选：启用重量级模型

`prophet` / `xgboost` / `torch` 为可选依赖。未安装时对应模型会优雅降级（API 仍可用，
`/api/models` 会标记其 `available=false`）。安装即可启用完整模型：

```bash
pip install prophet xgboost torch
```

---

## 🔌 REST API

| Method | Path | 功能 |
|--------|------|------|
| GET | `/api/klines?days=365&interval=1d` | 历史 K 线 OHLCV |
| GET | `/api/indicators?type=macd,kdj,rsi&days=365` | 技术指标计算 |
| GET | `/api/predict?model=ensemble&horizon=180&days=365` | 价格预测（默认 6 个月，含置信区间） |
| GET | `/api/backtest?model=lstm&period=90` | 回测结果 |
| GET | `/api/signals?days=365` | 交易信号（金叉死叉 / 超买超卖） |
| GET | `/api/stats?days=365` | 统计指标（Sharpe / 最大回撤 / 胜率） |
| GET | `/api/models` | 可用模型及其后端可用性 |

预测响应示例：

```json
{
  "model": "ensemble",
  "horizon_days": 180,
  "available": true,
  "note": "Weighted ensemble of: arima, xgboost",
  "predictions": [
    { "date": "2026-06-18", "price": 67234.5,
      "lower_80": 64100, "upper_80": 70500,
      "lower_95": 61200, "upper_95": 73800 }
  ],
  "metrics": { "mae": 1234.5, "rmse": 1890.2, "mape": 2.34, "directional_accuracy": 0.68 }
}
```

---

## 🧪 测试

```bash
pip install -r backend/requirements.txt pytest httpx
AICOIN_DISABLE_NETWORK=1 python -m pytest backend/tests/ -q
```

`AICOIN_DISABLE_NETWORK=1` 使用确定性合成数据，避免测试依赖外部网络。

---

## ☁️ 部署

- **后端**：使用仓库根目录的 `Dockerfile` 可部署到 Railway / Fly.io / Render 等（免费层）。
  通过环境变量配置：
  - `CORS_ORIGINS`（逗号分隔，默认 `*`）
  - `CACHE_TTL_SECONDS`（缓存有效期，默认 3600）
- **前端**：继续托管在 GitHub Pages，通过 `?backend=` 或页面输入框指向已部署的后端（CORS 已开启）。
- **CI**：`.github/workflows/ci.yml` 在 push / PR 时运行 pytest 并构建 Docker 镜像。

---

## 🛠️ 技术栈

- **后端**: FastAPI · pandas · numpy · statsmodels · scikit-learn ·（可选 prophet / xgboost / torch）
- **前端**: HTML5 + CSS3 + Vanilla JS · [Lightweight Charts](https://github.com/tradingview/lightweight-charts)
- **数据源**: CoinGecko API + SQLite 本地缓存
- **部署**: Docker / GitHub Actions / GitHub Pages

## License

MIT License
