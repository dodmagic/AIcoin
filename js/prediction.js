/**
 * prediction.js - 比特币价格预测算法引擎
 */
const Prediction = {

    /**
     * 综合预测入口
     * @param {Array} prices - 历史价格 [{time, value}, ...]
     * @param {string} model - 预测模型 'linear' | 'ma' | 'combined'
     * @param {number} futureDays - 预测天数 (默认180天=6个月)
     * @returns {Object} { predictions, confidence, stats }
     */
    predict(prices, model = 'combined', futureDays = 180) {
        if (!prices || prices.length < 30) {
            return { predictions: [], upperBand: [], lowerBand: [], confidence: 0, stats: {} };
        }

        const values = prices.map(p => p.value);
        let predictions;

        switch (model) {
            case 'linear':
                predictions = this._linearRegression(values, futureDays);
                break;
            case 'ma':
                predictions = this._movingAverageForecast(values, futureDays);
                break;
            case 'combined':
            default:
                predictions = this._combinedForecast(values, futureDays);
                break;
        }

        const lastTime = prices[prices.length - 1].time;
        const dayInSec = 86400;
        const volatility = this._calculateVolatility(values);
        const confidence = this._calculateConfidence(values, model);

        // 构建预测点(含时间戳)
        const predictionPoints = predictions.map((val, i) => ({
            time: lastTime + (i + 1) * dayInSec,
            value: Math.max(val, 0)
        }));

        // 置信区间
        const { upper, lower } = this._confidenceBands(predictionPoints, volatility);

        // 统计信息
        const currentPrice = values[values.length - 1];
        const stats = {
            currentPrice,
            price1m: predictionPoints[Math.min(29, predictionPoints.length - 1)]?.value,
            price3m: predictionPoints[Math.min(89, predictionPoints.length - 1)]?.value,
            price6m: predictionPoints[predictionPoints.length - 1]?.value,
            trend: this._determineTrend(predictionPoints, currentPrice),
            confidence,
            volatility,
            rsi: this._calculateRSI(values)
        };

        return {
            predictions: predictionPoints,
            upperBand: upper,
            lowerBand: lower,
            confidence,
            stats
        };
    },

    /**
     * 线性回归预测
     */
    _linearRegression(values, futureDays) {
        const n = values.length;
        // 使用最近90天数据做回归
        const window = Math.min(90, n);
        const recent = values.slice(-window);

        let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;
        for (let i = 0; i < recent.length; i++) {
            sumX += i;
            sumY += recent[i];
            sumXY += i * recent[i];
            sumX2 += i * i;
        }

        const slope = (recent.length * sumXY - sumX * sumY) / (recent.length * sumX2 - sumX * sumX);
        const intercept = (sumY - slope * sumX) / recent.length;

        const predictions = [];
        for (let i = 1; i <= futureDays; i++) {
            const x = recent.length + i - 1;
            // 加入衰减因子，距离越远斜率影响越小
            const decay = Math.exp(-i * 0.003);
            const trend = slope * decay * i;
            predictions.push(intercept + slope * (recent.length - 1) + trend);
        }

        return predictions;
    },

    /**
     * 加权移动平均预测
     */
    _movingAverageForecast(values, futureDays) {
        const windowSize = Math.min(30, Math.floor(values.length / 3));
        const predictions = [];
        let buffer = values.slice(-windowSize);

        for (let i = 0; i < futureDays; i++) {
            // 指数加权
            let weightedSum = 0, weightTotal = 0;
            for (let j = 0; j < buffer.length; j++) {
                const w = Math.exp(j * 0.05);
                weightedSum += buffer[j] * w;
                weightTotal += w;
            }
            const predicted = weightedSum / weightTotal;

            // 添加均值回归和随机波动
            const meanReversion = (values[values.length - 1] - predicted) * 0.01;
            const noise = (Math.random() - 0.5) * predicted * 0.005;
            const final = predicted + meanReversion + noise;

            predictions.push(final);
            buffer.push(final);
            buffer.shift();
        }

        return predictions;
    },

    /**
     * 综合预测 - 融合多种模型
     */
    _combinedForecast(values, futureDays) {
        const linear = this._linearRegression(values, futureDays);
        const ma = this._movingAverageForecast(values, futureDays);

        return linear.map((val, i) => {
            // 短期更信任MA，长期更信任线性回归
            const maWeight = Math.exp(-i * 0.01);
            const linearWeight = 1 - maWeight;
            return val * linearWeight + ma[i] * maWeight;
        });
    },

    /**
     * 计算置信区间带
     */
    _confidenceBands(predictions, volatility) {
        const upper = predictions.map((p, i) => ({
            time: p.time,
            value: p.value * (1 + volatility * Math.sqrt((i + 1) / 30) * 1.5)
        }));

        const lower = predictions.map((p, i) => ({
            time: p.time,
            value: Math.max(p.value * (1 - volatility * Math.sqrt((i + 1) / 30) * 1.5), 0)
        }));

        return { upper, lower };
    },

    /**
     * 计算年化波动率
     */
    _calculateVolatility(values) {
        if (values.length < 2) return 0;
        const returns = [];
        for (let i = 1; i < values.length; i++) {
            returns.push(Math.log(values[i] / values[i - 1]));
        }
        const mean = returns.reduce((a, b) => a + b, 0) / returns.length;
        const variance = returns.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / returns.length;
        return Math.sqrt(variance * 365); // 年化
    },

    /**
     * 计算RSI (相对强弱指标)
     */
    _calculateRSI(values, period = 14) {
        if (values.length < period + 1) return 50;
        const recent = values.slice(-(period + 1));
        let gains = 0, losses = 0;

        for (let i = 1; i < recent.length; i++) {
            const diff = recent[i] - recent[i - 1];
            if (diff > 0) gains += diff;
            else losses -= diff;
        }

        const avgGain = gains / period;
        const avgLoss = losses / period;
        if (avgLoss === 0) return 100;
        const rs = avgGain / avgLoss;
        return 100 - 100 / (1 + rs);
    },

    /**
     * 判断趋势
     */
    _determineTrend(predictions, currentPrice) {
        if (predictions.length === 0) return '未知';
        const finalPrice = predictions[predictions.length - 1].value;
        const change = (finalPrice - currentPrice) / currentPrice;

        if (change > 0.2) return '🟢 强烈看涨';
        if (change > 0.05) return '🟢 看涨';
        if (change > -0.05) return '🟡 震荡';
        if (change > -0.2) return '🔴 看跌';
        return '🔴 强烈看跌';
    },

    /**
     * 计算预测置信度
     */
    _calculateConfidence(values, model) {
        const volatility = this._calculateVolatility(values);
        // 波动率越低置信度越高，数据量越多置信度越高
        let base = Math.max(0.3, 1 - volatility);
        base *= Math.min(1, values.length / 365);

        if (model === 'combined') base *= 1.1;
        return Math.min(0.85, Math.max(0.2, base));
    },

    /**
     * 计算移动平均线
     */
    calculateMA(prices, period) {
        const result = [];
        for (let i = period - 1; i < prices.length; i++) {
            let sum = 0;
            for (let j = 0; j < period; j++) {
                sum += prices[i - j].value;
            }
            result.push({ time: prices[i].time, value: sum / period });
        }
        return result;
    },

    /**
     * 计算指数移动平均线
     */
    calculateEMA(prices, period) {
        const result = [];
        const k = 2 / (period + 1);
        let ema = prices[0].value;

        for (let i = 0; i < prices.length; i++) {
            ema = prices[i].value * k + ema * (1 - k);
            if (i >= period - 1) {
                result.push({ time: prices[i].time, value: ema });
            }
        }
        return result;
    },

    /**
     * 计算布林带
     */
    calculateBOLL(prices, period = 20, multiplier = 2) {
        const upper = [], middle = [], lower = [];

        for (let i = period - 1; i < prices.length; i++) {
            let sum = 0;
            for (let j = 0; j < period; j++) sum += prices[i - j].value;
            const ma = sum / period;

            let variance = 0;
            for (let j = 0; j < period; j++) variance += Math.pow(prices[i - j].value - ma, 2);
            const std = Math.sqrt(variance / period);

            const time = prices[i].time;
            upper.push({ time, value: ma + multiplier * std });
            middle.push({ time, value: ma });
            lower.push({ time, value: ma - multiplier * std });
        }

        return { upper, middle, lower };
    }
};
