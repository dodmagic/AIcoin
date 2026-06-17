/**
 * app.js - 主应用逻辑
 */
(async function () {
    // ===== State =====
    let currentRange = 365;
    let currentModel = 'combined';
    let currentIndicator = 'ma';
    let pricesCache = [];

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
            runPrediction();

            // 滚动到最新
            ChartManager.scrollToEnd();
        } catch (err) {
            console.error('加载数据失败:', err);
        }

        showLoading(false);
    }

    // ===== Prediction =====
    function runPrediction() {
        const result = Prediction.predict(pricesCache, currentModel, 180);

        if (result.predictions.length > 0) {
            ChartManager.setPrediction(
                result.predictions,
                result.upperBand,
                result.lowerBand
            );
        }

        updateStats(result.stats);
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
