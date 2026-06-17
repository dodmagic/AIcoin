# AIcoin - Bitcoin Price Prediction Platform

[![CI](https://github.com/dodmagic/AIcoin/actions/workflows/ci.yml/badge.svg)](https://github.com/dodmagic/AIcoin/actions/workflows/ci.yml)
[![Docker Build & Push](https://github.com/dodmagic/AIcoin/actions/workflows/docker-build.yml/badge.svg)](https://github.com/dodmagic/AIcoin/actions/workflows/docker-build.yml)
[![Deploy & Integration Test](https://github.com/dodmagic/AIcoin/actions/workflows/deploy.yml/badge.svg)](https://github.com/dodmagic/AIcoin/actions/workflows/deploy.yml)
[![backend image](https://img.shields.io/badge/ghcr.io-aicoin--backend-blue?logo=docker)](https://github.com/dodmagic/AIcoin/pkgs/container/aicoin-backend)
[![frontend image](https://img.shields.io/badge/ghcr.io-aicoin--frontend-blue?logo=docker)](https://github.com/dodmagic/AIcoin/pkgs/container/aicoin-frontend)

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
├── backend/Dockerfile      # 后端镜像 (python:3.11-slim, 多阶段, 非 root)
├── frontend/               # 前端容器化 (Nginx)
│   ├── Dockerfile          # nginx:alpine 静态站点镜像
│   └── nginx.conf          # /api 反向代理到 backend:8000
├── docker-compose.yml      # 一键启动整个栈 (GHCR 镜像)
├── docker-compose.test.yml # 容器化集成测试栈
└── .github/workflows/
    ├── ci.yml              # CI: ruff lint + pytest + 前端 lint
    ├── docker-build.yml    # 构建并推送多架构镜像到 GHCR (+ Trivy + cosign + SBOM)
    └── deploy.yml          # 拉取镜像 + 集成测试 + 失败自动告警
```

---

## 🚀 快速开始

### 方式一：Docker Compose（推荐，一键启动后端 + 前端）

直接拉取已发布到 GHCR 的镜像启动（**无需本地构建**）：

```bash
# 拉取 docker-compose.yml 并启动
curl -O https://raw.githubusercontent.com/dodmagic/AIcoin/main/docker-compose.yml
docker compose pull
docker compose up -d

# 访问前端
open http://localhost:8080
```

或在本地源码目录中构建并启动：

```bash
docker compose up --build -d
```

- 后端 API: <http://localhost:8000>（交互式文档 <http://localhost:8000/docs>）
- 前端页面: <http://localhost:8080>（Nginx 将 `/api/*` 反向代理到后端）

镜像地址（multi-arch: amd64 + arm64）：

- `ghcr.io/dodmagic/aicoin-backend:latest`
- `ghcr.io/dodmagic/aicoin-frontend:latest`

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

## ☁️ 部署 & CI/CD

整个构建、测试、推送、集成测试流程**完全在 GitHub Actions 云端完成**，无需本地 Docker 环境。

```
开发者 push → GitHub
                 │
                 ▼
        ┌─────────────────────┐
        │ ci.yml              │
        │  • ruff lint        │
        │  • pytest           │
        │  • 前端 JS lint     │
        └────────┬────────────┘
                 │ 通过 (push 到 main / 打 tag v*)
                 ▼
        ┌─────────────────────┐
        │ docker-build.yml    │
        │  • build backend    │
        │  • build frontend   │
        │  • multi-arch       │
        │    (amd64 + arm64)  │
        │  • push to ghcr.io  │
        │  • Trivy 漏洞扫描   │
        │  • cosign 签名      │
        │  • SBOM 生成        │
        └────────┬────────────┘
                 │ 构建成功后自动触发
                 ▼
        ┌─────────────────────┐
        │ deploy.yml          │
        │  • pull from ghcr   │
        │  • compose up       │
        │  • 集成测试         │
        │  • 日志 artifact    │
        │  • 失败自动开 issue │
        └─────────────────────┘
                 │
                 ▼
              ✅ Done
```

**镜像标签策略：** `latest`（main 分支）/ `v1.2.3`（语义化 tag）/ `sha-abc123`（commit SHA）三种并存。

**首次配置（仓库 Settings）：**

- Settings → Actions → General → Workflow permissions 勾选 **Read and write permissions**（允许推送 packages）。
- 首次推送后，在仓库 **Packages** 页面把 `aicoin-backend` / `aicoin-frontend` 镜像设为 **public** 以便公开部署。

**单镜像部署（仅后端）：** 使用 `backend/Dockerfile` 可部署到 Railway / Fly.io / Render 等。
通过环境变量配置：

- `CORS_ORIGINS`（逗号分隔，默认 `*`）
- `CACHE_TTL_SECONDS`（缓存有效期，默认 3600）

**前端**：也可继续托管在 GitHub Pages，通过 `?backend=` 或页面输入框指向已部署的后端（CORS 已开启）。

---

## 🛠️ 技术栈

- **后端**: FastAPI · pandas · numpy · statsmodels · scikit-learn ·（可选 prophet / xgboost / torch）
- **前端**: HTML5 + CSS3 + Vanilla JS · [Lightweight Charts](https://github.com/tradingview/lightweight-charts)
- **数据源**: CoinGecko API + SQLite 本地缓存
- **部署**: Docker / GitHub Actions / GitHub Pages

## License

MIT License
