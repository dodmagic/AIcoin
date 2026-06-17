/**
 * app.js - 主应用逻辑
 */
(async function () {
    // ===== State =====
    let currentRange = 365;
    let currentModel = 'ensemble';
    let currentIndicator = 'ma';
    let pricesCache = [];

    // 后端缺少方向准确率时的默认置信度 (%)
    const DEFAULT_CONFIDENCE = 60;

    // ===== Init =====
    async function init() {
        showLoading(true);

        try {
            ChartManager.init();
            await loadData();
            setupEventListeners();
            await updateCurrentPrice();
        } catch (err) {
            console.error('初始化失败:', err);
        }

        showLoading(false);
    }

    // ===== Data Loading =====
    async function loadData() {
        showLoading(true);

        try {
            const [ohlc, market] = await Promise.all([
                API.getOHLC(currentRange),
                API.getMarketChart(currentRange)
            ]);

            // 渲染K线
            const candles = ChartManager.setCandles(ohlc);

            // 渲染成交量
            if (market.total_volumes) {
                ChartManager.setVolume(market.total_volumes, ohlc);
            }

            // 构建价格序列(用于预测)
            pricesCache = candles.map(c => ({
                time: c.time,
                value: c.close
            }));

            // 添加技术指标
            ChartManager.addIndicator(currentIndicator, pricesCache);

            // 运行预测
            await runPrediction();

            // 滚动到最新
            ChartManager.scrollToEnd();
        } catch (err) {
            console.error('加载数据失败:', err);
        }

        showLoading(false);
    }

    // ===== Prediction =====
    async function runPrediction() {
        // 优先使用 Python 后端 (真实波动 + 80/95 置信区间扇形)
        if (await Backend.isAvailable()) {
            try {
                const horizon = 180;
                const res = await Backend.predict(currentModel, horizon, currentRange);
                if (res.predictions && res.predictions.length > 0) {
                    ChartManager.setPredictionFan(res.predictions);
                    updateStatsFromBackend(res);
                    setBackendStatus(true, res);
                    await loadSignals();
                    ChartManager.scrollToEnd();
                    return;
                }
            } catch (err) {
                console.warn('后端预测失败, 回退本地引擎:', err);
            }
        }
        setBackendStatus(false);

        // 回退: 本地 JS 预测引擎
        const result = Prediction.predict(pricesCache, mapLocalModel(currentModel), 180);
        if (result.predictions.length > 0) {
            ChartManager.setPrediction(
                result.predictions,
                result.upperBand,
                result.lowerBand
            );
        }
        updateStats(result.stats);
    }

    // 后端模型名 -> 本地引擎可用模型名
    function mapLocalModel(model) {
        if (model === 'linear') return 'linear';
        if (model === 'ma') return 'ma';
        return 'combined';
    }

    async function loadSignals() {
        try {
            const res = await Backend.signals(currentRange);
            ChartManager.setSignals(res.signals || []);
        } catch (err) {
            console.warn('加载信号失败:', err);
        }
    }

    function setBackendStatus(online, res) {
        const el = document.getElementById('backendStatus');
        if (!el) return;
        if (online) {
            const note = res && res.note ? ` · ${res.note}` : '';
            el.textContent = `🟢 量化后端在线${note}`;
            el.className = 'backend-status online';
        } else {
            el.textContent = '🟡 后端离线 · 使用本地引擎';
            el.className = 'backend-status offline';
        }
    }

    function updateStatsFromBackend(res) {
        const preds = res.predictions;
        const fmt = (v) => v ? `$${Number(v).toLocaleString('en-US', { maximumFractionDigits: 0 })}` : '--';
        const at = (i) => preds[Math.min(i, preds.length - 1)]?.price;
        const current = pricesCache.length ? pricesCache[pricesCache.length - 1].value : at(0);

        const pctChange = (future) => {
            if (!future || !current) return null;
            const pct = ((future - current) / current * 100).toFixed(1);
            return { text: `${pct >= 0 ? '+' : ''}${pct}%`, isUp: pct >= 0 };
        };

        document.getElementById('statCurrentPrice').textContent = fmt(current);
        document.getElementById('statPrice1m').textContent = fmt(at(29));
        setChange('statChange1m', pctChange(at(29)));
        document.getElementById('statPrice3m').textContent = fmt(at(89));
        setChange('statChange3m', pctChange(at(89)));
        document.getElementById('statPrice6m').textContent = fmt(at(preds.length - 1));
        setChange('statChange6m', pctChange(at(preds.length - 1)));

        const last = at(preds.length - 1);
        document.getElementById('statTrend').textContent =
            last > current ? '📈 看涨' : (last < current ? '📉 看跌' : '➡️ 横盘');

        // 用回测方向准确率作为置信度
        const m = res.metrics || {};
        const conf = m.directional_accuracy != null ? Math.round(m.directional_accuracy * 100) : DEFAULT_CONFIDENCE;
        document.getElementById('statConfidence').textContent = `${conf}%`;
        document.getElementById('confidenceFill').style.width = `${conf}%`;

        // 用预测区间宽度估算波动率
        const p = preds[preds.length - 1];
        const vol = p && p.price ? ((p.upper_80 - p.lower_80) / 2 / p.price * 100).toFixed(1) : '--';
        document.getElementById('statVolatility').textContent = `${vol}%`;

        if (m.mape != null) {
            document.getElementById('statRSI').textContent = `MAPE ${m.mape.toFixed(1)}%`;
        }

        // 更新统计面板 (Sharpe / 最大回撤)
        updateBackendStats();
    }

    async function updateBackendStats() {
        try {
            const res = await Backend.stats(currentRange);
            const el = document.getElementById('backendStats');
            if (el && res.stats) {
                const s = res.stats;
                el.innerHTML =
                    `Sharpe ${s.sharpe} · 最大回撤 ${(s.max_drawdown * 100).toFixed(1)}% · ` +
                    `胜率 ${(s.win_rate * 100).toFixed(1)}% · 年化波动 ${(s.annual_volatility * 100).toFixed(1)}%`;
            }
        } catch (err) {
            /* optional */
        }
    }

    // ===== UI Updates =====
    async function updateCurrentPrice() {
        const { price, change24h } = await API.getCurrentPrice();
        const priceEl = document.getElementById('currentPrice');
        const changeEl = document.getElementById('priceChange');

        if (price) {
            priceEl.textContent = `$${price.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
            if (change24h !== null) {
                const sign = change24h >= 0 ? '+' : '';
                changeEl.textContent = `${sign}${change24h.toFixed(2)}%`;
                changeEl.className = `price-change ${change24h >= 0 ? 'up' : 'down'}`;
            }
        }
    }

    function updateStats(stats) {
        if (!stats || !stats.currentPrice) return;

        const fmt = (v) => v ? `$${v.toLocaleString('en-US', { maximumFractionDigits: 0 })}` : '--';
        const pctChange = (future, current) => {
            if (!future || !current) return '';
            const pct = ((future - current) / current * 100).toFixed(1);
            const sign = pct >= 0 ? '+' : '';
            return { text: `${sign}${pct}%`, isUp: pct >= 0 };
        };

        document.getElementById('statCurrentPrice').textContent = fmt(stats.currentPrice);

        // 1个月预测
        document.getElementById('statPrice1m').textContent = fmt(stats.price1m);
        const c1 = pctChange(stats.price1m, stats.currentPrice);
        setChange('statChange1m', c1);

        // 3个月预测
        document.getElementById('statPrice3m').textContent = fmt(stats.price3m);
        const c3 = pctChange(stats.price3m, stats.currentPrice);
        setChange('statChange3m', c3);

        // 6个月预测
        document.getElementById('statPrice6m').textContent = fmt(stats.price6m);
        const c6 = pctChange(stats.price6m, stats.currentPrice);
        setChange('statChange6m', c6);

        // 趋势
        document.getElementById('statTrend').textContent = stats.trend || '--';

        // 置信度
        const confPct = Math.round((stats.confidence || 0) * 100);
        document.getElementById('statConfidence').textContent = `${confPct}%`;
        document.getElementById('confidenceFill').style.width = `${confPct}%`;

        // 波动率
        const volPct = ((stats.volatility || 0) * 100).toFixed(1);
        document.getElementById('statVolatility').textContent = `${volPct}%`;

        // RSI
        document.getElementById('statRSI').textContent = (stats.rsi || 0).toFixed(1);
    }

    function setChange(id, change) {
        const el = document.getElementById(id);
        if (change && change.text) {
            el.textContent = change.text;
            el.className = `stat-change ${change.isUp ? 'up' : 'down'}`;
        }
    }

    function showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        if (show) overlay.classList.remove('hidden');
        else overlay.classList.add('hidden');
    }

    // ===== Event Listeners =====
    function setupEventListeners() {
        // 时间范围
        document.getElementById('timeRange').addEventListener('click', (e) => {
            const btn = e.target.closest('[data-range]');
            if (!btn) return;

            document.querySelectorAll('#timeRange .btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentRange = parseInt(btn.dataset.range);
            loadData();
        });

        // 技术指标
        document.getElementById('indicators').addEventListener('click', (e) => {
            const btn = e.target.closest('[data-indicator]');
            if (!btn) return;

            document.querySelectorAll('#indicators .btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentIndicator = btn.dataset.indicator;

            if (pricesCache.length > 0) {
                ChartManager.addIndicator(currentIndicator, pricesCache);
            }
        });

        // 预测模型
        document.getElementById('predictionModel').addEventListener('change', (e) => {
            currentModel = e.target.value;
            if (pricesCache.length > 0) runPrediction();
        });

        // 后端地址配置
        const backendInput = document.getElementById('backendUrl');
        if (backendInput) {
            const stored = localStorage.getItem('aicoin_backend_url');
            if (stored) backendInput.value = stored;
            backendInput.addEventListener('change', (e) => {
                Backend.setBaseUrl(e.target.value.trim());
                loadData();
            });
        }

        // 刷新按钮
        document.getElementById('refreshBtn').addEventListener('click', () => {
            loadData();
            updateCurrentPrice();
        });

        // 主题切换
        document.getElementById('themeToggle').addEventListener('click', () => {
            const isDark = document.body.classList.toggle('dark-theme');
            document.body.classList.toggle('light-theme', !isDark);
            ChartManager.updateTheme(isDark);
        });
    }

    // ===== Start =====
    init();
})();
