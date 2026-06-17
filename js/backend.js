/**
 * backend.js - Python 量化后端 (FastAPI) 客户端
 *
 * 后端地址可通过以下方式配置(优先级从高到低):
 *   1. localStorage 中的 `aicoin_backend_url`
 *   2. URL 查询参数 ?backend=https://your-host
 *   3. 默认 http://localhost:8000
 * 若后端不可用, 前端会自动回退到本地 JS 预测引擎 (prediction.js)。
 */
const Backend = {
    _available: null,

    baseUrl() {
        const fromStorage = localStorage.getItem('aicoin_backend_url');
        if (fromStorage) return fromStorage.replace(/\/$/, '');
        const params = new URLSearchParams(location.search);
        const fromQuery = params.get('backend');
        if (fromQuery) return fromQuery.replace(/\/$/, '');
        return 'http://localhost:8000';
    },

    setBaseUrl(url) {
        if (url) {
            localStorage.setItem('aicoin_backend_url', url.replace(/\/$/, ''));
        } else {
            localStorage.removeItem('aicoin_backend_url');
        }
        this._available = null;
    },

    async _get(path) {
        const res = await fetch(`${this.baseUrl()}${path}`, {
            headers: { 'Accept': 'application/json' }
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
    },

    /**
     * 检测后端是否在线 (带缓存)
     */
    async isAvailable() {
        if (this._available !== null) return this._available;
        try {
            const ctrl = new AbortController();
            const timer = setTimeout(() => ctrl.abort(), 2500);
            const res = await fetch(`${this.baseUrl()}/health`, { signal: ctrl.signal });
            clearTimeout(timer);
            this._available = res.ok;
        } catch (e) {
            this._available = false;
        }
        return this._available;
    },

    /**
     * 价格预测
     * @returns {Object} { model, horizon_days, predictions:[{time,price,lower_80,...}], metrics }
     */
    async predict(model = 'ensemble', horizon = 180, days = 365) {
        return this._get(`/api/predict?model=${encodeURIComponent(model)}&horizon=${horizon}&days=${days}`);
    },

    /**
     * 交易信号 (金叉/死叉/超买/超卖)
     */
    async signals(days = 365) {
        return this._get(`/api/signals?days=${days}`);
    },

    /**
     * 统计指标 (Sharpe / 最大回撤 / 胜率)
     */
    async stats(days = 365) {
        return this._get(`/api/stats?days=${days}`);
    },

    /**
     * 回测结果
     */
    async backtest(model = 'ensemble', period = 90, days = 365) {
        return this._get(`/api/backtest?model=${encodeURIComponent(model)}&period=${period}&days=${days}`);
    },

    /**
     * 可用模型列表及其后端可用性
     */
    async models() {
        return this._get('/api/models');
    }
};
