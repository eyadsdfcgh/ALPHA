/**
 * Alpha Platform - TradingView Lightweight Charts Integration
 */

let chart, candleSeries;
let wave1Series, wave2Series, wave3Series, wave4Series, wave200Series;
let smmaSeries;
let areaSeriesInner, areaSeriesOuter;
let tpLines = [];
let srBoxes = []; // We will use custom primitive or just lines for SR boxes for simplicity in v4, or we can use rectangles if supported. Lightweight Charts v4 doesn't have native "Boxes". We can simulate with AreaSeries or horizontal lines. For now we will just draw horizontal lines for Support and Resistance.

let rawCandles = [];
const worker = new Worker('/static/js/tradingWorker.js');

function initChart() {
    const container = document.getElementById('tv_chart_container');
    container.innerHTML = '';
    
    chart = LightweightCharts.createChart(container, {
        layout: {
            background: { type: LightweightCharts.ColorType.Solid, color: '#0B0E14' },
            textColor: '#94a3b8',
        },
        grid: {
            vertLines: { color: 'rgba(255, 255, 255, 0.03)' },
            horzLines: { color: 'rgba(255, 255, 255, 0.03)' },
        },
        crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal,
        },
        rightPriceScale: {
            borderColor: 'rgba(255, 255, 255, 0.1)',
        },
        timeScale: {
            borderColor: 'rgba(255, 255, 255, 0.1)',
            timeVisible: true,
            secondsVisible: false,
        },
    });

    candleSeries = chart.addCandlestickSeries({
        upColor: '#00BCD4',
        downColor: '#FF5252',
        borderVisible: false,
        wickUpColor: '#00BCD4',
        wickDownColor: '#FF5252',
    });

    // Wave Series
    wave200Series = chart.addLineSeries({ color: '#1e90ff', lineWidth: 4 });
    wave1Series = chart.addLineSeries({ color: '#00ced1', lineWidth: 2 });
    wave2Series = chart.addLineSeries({ color: '#00ced1', lineWidth: 2 });
    wave3Series = chart.addLineSeries({ color: '#1e90ff', lineWidth: 1 });
    wave4Series = chart.addLineSeries({ color: '#1e90ff', lineWidth: 1 });

    smmaSeries = chart.addLineSeries({ color: '#a020f0', lineWidth: 3 });

    // Handle resizing
    new ResizeObserver(entries => {
        if (entries.length === 0 || entries[0].target !== container) { return; }
        const newRect = entries[0].contentRect;
        chart.applyOptions({ height: newRect.height, width: newRect.width });
    }).observe(container);
}

function updateDashboards(dash) {
    if(!dash) return;
    
    const dTrend = document.getElementById('dash-trend');
    const dCloud = document.getElementById('dash-cloud');
    const dVol = document.getElementById('dash-vol');
    const dSmma = document.getElementById('dash-smma');
    const dTsi = document.getElementById('dash-tsi');
    const dW1m = document.getElementById('dash-wave-1m');
    const dW5m = document.getElementById('dash-wave-5m');
    
    if(dTrend) {
        dTrend.innerText = dash.trend;
        dTrend.className = 'dash-val ' + (dash.trend === 'LONG' ? 'c-green' : dash.trend === 'SHORT' ? 'c-red' : 'c-gray');
    }
    if(dCloud) {
        dCloud.innerText = dash.cloud;
        dCloud.className = 'dash-val ' + (dash.cloud === 'Bull' ? 'c-green' : 'c-red');
    }
    if(dVol) {
        dVol.innerText = dash.vol;
        dVol.className = 'dash-val ' + (dash.vol === 'YES' ? 'c-yellow' : 'c-gray');
    }
    if(dSmma) {
        dSmma.innerText = dash.smma;
        dSmma.className = 'dash-val ' + (dash.smma === 'Above' ? 'c-green' : 'c-red');
    }
    if(dTsi) {
        dTsi.innerText = dash.tsi;
        dTsi.className = 'dash-val ' + (dash.tsi === 'Curl Up' ? 'c-green' : dash.tsi === 'Curl Dn' ? 'c-red' : 'c-gray');
    }
    if(dW1m) {
        dW1m.innerText = dash.wave1m ? 'BULL' : 'BEAR';
        dW1m.className = 'dash-val dash-bg ' + (dash.wave1m ? 'bg-cyan' : 'bg-blue');
    }
    if(dW5m) {
        dW5m.innerText = dash.wave5m ? 'BULL' : 'BEAR';
        dW5m.className = 'dash-val dash-bg ' + (dash.wave5m ? 'bg-cyan' : 'bg-blue');
    }
}

worker.onmessage = function(e) {
    if (e.data.type === 'CALCULATE_SUCCESS') {
        const payload = e.data.payload;
        
        // Update Lines
        if(payload.wave200.length) wave200Series.setData(payload.wave200);
        if(payload.wave1.length) wave1Series.setData(payload.wave1);
        if(payload.wave2.length) wave2Series.setData(payload.wave2);
        if(payload.wave3.length) wave3Series.setData(payload.wave3);
        if(payload.wave4.length) wave4Series.setData(payload.wave4);
        if(payload.we_smma.length) smmaSeries.setData(payload.we_smma);

        // Update Markers
        if(payload.markers.length) {
            // Lightweight charts expects markers to be sorted by time
            let sortedMarkers = payload.markers.sort((a,b) => a.time - b.time);
            // Group markers by time, since LWC only allows one marker per time per series. We'll just take the most important or first one if there are duplicates.
            let uniqueMarkers = [];
            let seen = new Set();
            for(let m of sortedMarkers) {
                if(!seen.has(m.time)) {
                    uniqueMarkers.push(m);
                    seen.add(m.time);
                }
            }
            candleSeries.setMarkers(uniqueMarkers);
        }
        
        // Draw Target Lines (Clear old, draw new)
        tpLines.forEach(l => candleSeries.removePriceLine(l));
        tpLines = [];
        if(payload.targetLines && payload.targetLines.length) {
            payload.targetLines.forEach(l => {
                let pl = candleSeries.createPriceLine({
                    price: l.price,
                    color: l.color,
                    lineWidth: 1,
                    lineStyle: l.style === 'dashed' ? LightweightCharts.LineStyle.Dashed : LightweightCharts.LineStyle.Solid,
                    axisLabelVisible: true,
                    title: l.title,
                });
                tpLines.push(pl);
            });
        }

        updateDashboards(payload.dashboard);
    }
};

function generateMockData() {
    console.log("Using mock data fallback.");
    let candles = [];
    let time = Math.floor(Date.now() / 1000) - 1000 * 60;
    let val = 60000;
    for(let i=0; i<1000; i++) {
        let open = val + (Math.random()-0.5)*100;
        let close = open + (Math.random()-0.5)*200;
        let high = Math.max(open, close) + Math.random()*50;
        let low = Math.min(open, close) - Math.random()*50;
        let volume = Math.random() * 10;
        candles.push({ time, open, high, low, close, volume });
        time += 60;
        val = close;
    }
    return candles;
}

async function fetchHistoricalData() {
    try {
        const res = await fetch('https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=1000');
        const data = await res.json();
        
        if(!Array.isArray(data)) {
            console.error("Invalid data from Binance:", data);
            rawCandles = generateMockData();
        } else {
            rawCandles = data.map(d => ({
                time: Math.floor(d[0] / 1000), // Unix timestamp in seconds must be integer
                open: parseFloat(d[1]),
                high: parseFloat(d[2]),
                low: parseFloat(d[3]),
                close: parseFloat(d[4]),
                volume: parseFloat(d[5])
            }));
        }
    } catch (err) {
        console.error("Error fetching historical data, falling back to mock:", err);
        rawCandles = generateMockData();
    }
    
    candleSeries.setData(rawCandles);
    worker.postMessage({ type: 'CALCULATE', payload: { candles: rawCandles }});
}

function connectWebSocket() {
    const ws = new WebSocket('wss://stream.binance.com:9443/ws/btcusdt@kline_1m');
    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        const kline = message.k;
        const tick = {
            time: Math.floor(kline.t / 1000),
            open: parseFloat(kline.o),
            high: parseFloat(kline.h),
            low: parseFloat(kline.l),
            close: parseFloat(kline.c),
            volume: parseFloat(kline.v)
        };
        
        candleSeries.update(tick);
        
        // Update rawCandles array for the worker
        if (rawCandles.length > 0 && rawCandles[rawCandles.length - 1].time === tick.time) {
            rawCandles[rawCandles.length - 1] = tick;
        } else {
            rawCandles.push(tick);
        }

        // Throttle worker updates slightly in a real app, but for now we post immediately
        worker.postMessage({ type: 'CALCULATE', payload: { candles: rawCandles }});
    };
}

document.addEventListener('DOMContentLoaded', () => {
    initChart();
    fetchHistoricalData().then(() => {
        connectWebSocket();
    });
});
