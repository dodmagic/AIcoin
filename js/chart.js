/**
 * chart.js - K线图表渲染引擎 (基于Lightweight Charts)
 */
const ChartManager = {
    mainChart: null,
    candleSeries: null,
    predictionSeries: null,
    upperBandSeries: null,
    lowerBandSeries: null,
    upper95BandSeries: null,
    lower95BandSeries: null,
    indicatorSeries: [],
    volumeChart: null,
    volumeSeries: null,

    /**
     * 初始化图表
     */
    init() {
        const isDark = document.body.classList.contains('dark-theme');
        const chartOptions = this._getChartOptions(isDark);

        // 主图表
        const mainContainer = document.getElementById('mainChart');
        this.mainChart = LightweightCharts.createChart(mainContainer, {
            ...chartOptions,
            height: 480
        });

        // K线序列
        this.candleSeries = this.mainChart.addCandlestickSeries({
            upColor: '#26a69a',
            downColor: '#ef5350',
            borderUpColor: '#26a69a',
            borderDownColor: '#ef5350',
            wickUpColor: '#26a69a',
            wickDownColor: '#ef5350'
        });

        // 预测折线
        this.predictionSeries = this.mainChart.addLineSeries({
            color: '#ff9800',
            lineWidth: 2,
            lineStyle: LightweightCharts.LineStyle.Dashed,
            title: '预测'
        });

        // 置信区间上轨 (80%)
        this.upperBandSeries = this.mainChart.addLineSeries({
            color: 'rgba(255, 152, 0, 0.35)',
            lineWidth: 1,
            lineStyle: LightweightCharts.LineStyle.Dotted,
            crosshairMarkerVisible: false,
        });

        // 置信区间下轨 (80%)
        this.lowerBandSeries = this.mainChart.addLineSeries({
            color: 'rgba(255, 152, 0, 0.35)',
            lineWidth: 1,
            lineStyle: LightweightCharts.LineStyle.Dotted,
            crosshairMarkerVisible: false,
        });

        // 置信区间上轨 (95%)
        this.upper95BandSeries = this.mainChart.addLineSeries({
            color: 'rgba(255, 152, 0, 0.18)',
            lineWidth: 1,
            lineStyle: LightweightCharts.LineStyle.Dotted,
            crosshairMarkerVisible: false,
        });

        // 置信区间下轨 (95%)
        this.lower95BandSeries = this.mainChart.addLineSeries({
            color: 'rgba(255, 152, 0, 0.18)',
            lineWidth: 1,
            lineStyle: LightweightCharts.LineStyle.Dotted,
            crosshairMarkerVisible: false,
        });

        // 成交量图表
        const volContainer = document.getElementById('volumeChart');
        this.volumeChart = LightweightCharts.createChart(volContainer, {
            ...chartOptions,
            height: 100
        });

        this.volumeSeries = this.volumeChart.addHistogramSeries({
            color: '#26a69a',
            priceFormat: { type: 'volume' },
            priceScaleId: ''
        });

        // 同步缩放
        this.mainChart.timeScale().subscribeVisibleTimeRangeChange(() => {
            const range = this.mainChart.timeScale().getVisibleRange();
            if (range) this.volumeChart.timeScale().setVisibleRange(range);
        });

        // 响应式
        this._setupResize(mainContainer, this.mainChart, 480);
        this._setupResize(volContainer, this.volumeChart, 100);
    },

    /**
     * 更新K线数据
     */
    setCandles(ohlcData) {
        const candles = ohlcData.map(d => ({
            time: Math.floor(d[0] / 1000),
            open: d[1],
            high: d[2],
            low: d[3],
            close: d[4]
        }));

        // 去重并按时间排序
        const unique = this._dedup(candles);
        this.candleSeries.setData(unique);
        return unique;
    },

    /**
     * 更新成交量
     */
    setVolume(volumeData, ohlcData) {
        const closeMap = {};
        if (ohlcData) {
            ohlcData.forEach(d => {
                closeMap[Math.floor(d[0] / 1000)] = { open: d[1], close: d[4] };
            });
        }

        const volumes = volumeData.map(d => {
            const time = Math.floor(d[0] / 1000);
            const info = closeMap[time];
            return {
                time,
                value: d[1],
                color: info && info.close >= info.open
                    ? 'rgba(38, 166, 154, 0.5)'
                    : 'rgba(239, 83, 80, 0.5)'
            };
        });

        this.volumeSeries.setData(this._dedup(volumes));
    },

    /**
     * 更新预测线和置信区间 (本地引擎: 单一区间)
     */
    setPrediction(predictions, upperBand, lowerBand) {
        this.predictionSeries.setData(predictions);
        this.upperBandSeries.setData(upperBand);
        this.lowerBandSeries.setData(lowerBand);
        if (this.upper95BandSeries) this.upper95BandSeries.setData([]);
        if (this.lower95BandSeries) this.lower95BandSeries.setData([]);
    },

    /**
     * 更新预测扇形图 (后端: 80% + 95% 置信区间)
     * @param {Array} points - [{time, price, lower_80, upper_80, lower_95, upper_95}]
     */
    setPredictionFan(points) {
        const line = points.map(p => ({ time: p.time, value: p.price }));
        const u80 = points.map(p => ({ time: p.time, value: p.upper_80 }));
        const l80 = points.map(p => ({ time: p.time, value: p.lower_80 }));
        const u95 = points.map(p => ({ time: p.time, value: p.upper_95 }));
        const l95 = points.map(p => ({ time: p.time, value: p.lower_95 }));

        this.predictionSeries.setData(this._dedup(line));
        this.upperBandSeries.setData(this._dedup(u80));
        this.lowerBandSeries.setData(this._dedup(l80));
        this.upper95BandSeries.setData(this._dedup(u95));
        this.lower95BandSeries.setData(this._dedup(l95));
    },

    /**
     * 在K线上叠加买入/卖出信号箭头
     * @param {Array} signals - [{time, type:'buy'|'sell', reason}]
     */
    setSignals(signals) {
        if (!this.candleSeries) return;
        const markers = (signals || []).map(s => ({
            time: s.time,
            position: s.type === 'buy' ? 'belowBar' : 'aboveBar',
            color: s.type === 'buy' ? '#26a69a' : '#ef5350',
            shape: s.type === 'buy' ? 'arrowUp' : 'arrowDown',
            text: s.type === 'buy' ? '买' : '卖'
        }));
        const unique = this._dedup(markers);
        try { this.candleSeries.setMarkers(unique); } catch (e) { /* ignore */ }
    },

    /**
     * 添加技术指标
     */
    addIndicator(type, prices) {
        // 清除旧指标
        this.clearIndicators();

        switch (type) {
            case 'ma': {
                const ma7 = Prediction.calculateMA(prices, 7);
                const ma25 = Prediction.calculateMA(prices, 25);
                const ma99 = Prediction.calculateMA(prices, 99);

                this.indicatorSeries.push(
                    this._addLine(ma7, '#f44336', 'MA7'),
                    this._addLine(ma25, '#2196f3', 'MA25'),
                    this._addLine(ma99, '#9c27b0', 'MA99')
                );
                break;
            }
            case 'ema': {
                const ema12 = Prediction.calculateEMA(prices, 12);
                const ema26 = Prediction.calculateEMA(prices, 26);

                this.indicatorSeries.push(
                    this._addLine(ema12, '#ff5722', 'EMA12'),
                    this._addLine(ema26, '#00bcd4', 'EMA26')
                );
                break;
            }
            case 'boll': {
                const boll = Prediction.calculateBOLL(prices);
                this.indicatorSeries.push(
                    this._addLine(boll.upper, '#e91e63', 'BOLL↑'),
                    this._addLine(boll.middle, '#ff9800', 'BOLL'),
                    this._addLine(boll.lower, '#4caf50', 'BOLL↓')
                );
                break;
            }
        }
    },

    /**
     * 清除技术指标
     */
    clearIndicators() {
        this.indicatorSeries.forEach(s => {
            try { this.mainChart.removeSeries(s); } catch (e) { /* ignore */ }
        });
        this.indicatorSeries = [];
    },

    /**
     * 滚动到最新数据
     */
    scrollToEnd() {
        this.mainChart.timeScale().scrollToRealTime();
    },

    /**
     * 切换主题
     */
    updateTheme(isDark) {
        const opts = this._getChartOptions(isDark);
        this.mainChart.applyOptions(opts);
        this.volumeChart.applyOptions(opts);
    },

    // ===== Private Methods =====

    _addLine(data, color, title) {
        const series = this.mainChart.addLineSeries({
            color,
            lineWidth: 1,
            title,
            crosshairMarkerVisible: false
        });
        series.setData(data);
        return series;
    },

    _dedup(arr) {
        const seen = new Set();
        return arr
            .sort((a, b) => a.time - b.time)
            .filter(item => {
                if (seen.has(item.time)) return false;
                seen.add(item.time);
                return true;
            });
    },

    _getChartOptions(isDark) {
        return {
            layout: {
                background: { type: LightweightCharts.ColorType.Solid, color: isDark ? '#16213e' : '#ffffff' },
                textColor: isDark ? '#d1d4dc' : '#333333'
            },
            grid: {
                vertLines: { color: isDark ? 'rgba(42, 46, 57, 0.5)' : 'rgba(0,0,0,0.06)' },
                horzLines: { color: isDark ? 'rgba(42, 46, 57, 0.5)' : 'rgba(0,0,0,0.06)' }
            },
            crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
            rightPriceScale: { borderColor: isDark ? 'rgba(42, 46, 57, 0.8)' : '#e0e0e0' },
            timeScale: {
                borderColor: isDark ? 'rgba(42, 46, 57, 0.8)' : '#e0e0e0',
                timeVisible: true
            },
            handleScroll: true,
            handleScale: true
        };
    },

    _setupResize(container, chart, baseHeight) {
        const observer = new ResizeObserver(entries => {
            const { width } = entries[0].contentRect;
            chart.applyOptions({ width });
        });
        observer.observe(container);
    }
};
