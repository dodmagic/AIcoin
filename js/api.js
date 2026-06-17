/**
 * api.js - CoinGecko API 数据获取
 */
const API = {
    BASE_URL: 'https://api.coingecko.com/api/v3',

    /**
     * 获取比特币历史OHLC数据(K线)
     * @param {number} days - 天数
     * @returns {Promise<Array>} OHLC数据 [[timestamp, open, high, low, close], ...]
     */
    async getOHLC(days = 365) {
        const url = `${this.BASE_URL}/coins/bitcoin/ohlc?vs_currency=usd&days=${days}`;
        try {
            const res = await fetch(url);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return await res.json();
        } catch (err) {
            console.error('获取OHLC数据失败:', err);
            return this._generateFallbackOHLC(days);
        }
    },

    /**
     * 获取比特币历史市场数据(含成交量)
     * @param {number} days - 天数
     * @returns {Promise<Object>} { prices, total_volumes }
     */
    async getMarketChart(days = 365) {
        const url = `${this.BASE_URL}/coins/bitcoin/market_chart?vs_currency=usd&days=${days}`;
        try {
            const res = await fetch(url);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return await res.json();
        } catch (err) {
            console.error('获取市场数据失败:', err);
            return this._generateFallbackMarket(days);
        }
    },

    /**
     * 获取比特币当前价格
     * @returns {Promise<Object>} { usd, usd_24h_change }
     */
    async getCurrentPrice() {
        const url = `${this.BASE_URL}/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true`;
        try {
            const res = await fetch(url);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            return {
                price: data.bitcoin.usd,
                change24h: data.bitcoin.usd_24h_change
            };
        } catch (err) {
            console.error('获取当前价格失败:', err);
            return { price: null, change24h: null };
        }
    },

    /**
     * 备用数据生成 - OHLC (当API不可用时)
     */
    _generateFallbackOHLC(days) {
        const data = [];
        const now = Date.now();
        let price = 60000 + Math.random() * 30000;
        const interval = days <= 30 ? 4 * 3600000 : 24 * 3600000;
        const count = days <= 30 ? days * 6 : days;

        for (let i = count; i >= 0; i--) {
            const time = now - i * interval;
            const change = (Math.random() - 0.48) * price * 0.03;
            const open = price;
            price += change;
            const close = price;
            const high = Math.max(open, close) * (1 + Math.random() * 0.015);
            const low = Math.min(open, close) * (1 - Math.random() * 0.015);
            data.push([time, open, high, low, close]);
        }
        return data;
    },

    /**
     * 备用数据生成 - 市场数据
     */
    _generateFallbackMarket(days) {
        const prices = [];
        const volumes = [];
        const now = Date.now();
        let price = 60000 + Math.random() * 30000;
        const interval = 24 * 3600000;

        for (let i = days; i >= 0; i--) {
            const time = now - i * interval;
            const change = (Math.random() - 0.48) * price * 0.03;
            price += change;
            prices.push([time, price]);
            volumes.push([time, Math.random() * 50000000000 + 10000000000]);
        }
        return { prices, total_volumes: volumes };
    }
};
