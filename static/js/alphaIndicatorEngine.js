/**
 * Alpha SMC / Wolf X Indicator Engine
 * Performs all mathematical calculations mimicking Pine Script.
 */

class AlphaIndicatorEngine {
    constructor(inputs = {}) {
        this.inputs = {
            tsi_long: 25, tsi_short: 5, tsi_signal: 14,
            ema5_len: 5, ema10_len: 10,
            ha_bars: false, real_price: false,
            vol_ratio: 2, vol_lookback: 15,
            pivot_period: 10, max_ch_width: 5, min_strength: 5, max_sr: 2, loopback: 290,
            we_length: 200, wr_ema_len: 21, wr_smma_len: 200,
            tp1_rr: 1.0, tp2_rr: 3.0, tp3_rr: 5.0,
            ema1_len: 38, ema2_len: 50, ema3_len: 65, ema4_len: 80, ema200_len: 200,
            ...inputs
        };
    }

    // --- Math Helpers ---
    sma(data, length, getter = (d) => d) {
        let result = new Array(data.length).fill(NaN);
        let sum = 0;
        for (let i = 0; i < data.length; i++) {
            sum += getter(data[i]);
            if (i >= length) sum -= getter(data[i - length]);
            if (i >= length - 1) result[i] = sum / length;
        }
        return result;
    }

    ema(data, length, getter = (d) => d) {
        let result = new Array(data.length).fill(NaN);
        let alpha = 2 / (length + 1);
        let ema = NaN;
        for (let i = 0; i < data.length; i++) {
            let val = getter(data[i]);
            if (isNaN(ema)) {
                if (!isNaN(val)) ema = val;
            } else {
                ema = (val - ema) * alpha + ema;
            }
            result[i] = ema;
        }
        return result;
    }

    smma(data, length, getter = (d) => d) {
        let result = new Array(data.length).fill(NaN);
        let smma = NaN;
        // initial is SMA
        let smaArr = this.sma(data, length, getter);
        
        for (let i = 0; i < data.length; i++) {
            let val = getter(data[i]);
            if (isNaN(smma)) {
                if (!isNaN(smaArr[i])) smma = smaArr[i];
            } else {
                smma = (smma * (length - 1) + val) / length;
            }
            result[i] = smma;
        }
        return result;
    }

    t3(data, length, getter = (d) => d) {
        let c = 0.7;
        let e1 = this.ema(data, length, getter);
        let e2 = this.ema(e1, length, x=>x);
        let e3 = this.ema(e2, length, x=>x);
        let e4 = this.ema(e3, length, x=>x);
        let e5 = this.ema(e4, length, x=>x);
        let e6 = this.ema(e5, length, x=>x);

        let result = new Array(data.length).fill(NaN);
        for(let i=0; i<data.length; i++) {
            if (isNaN(e6[i])) continue;
            let v = (-c*c*c)*e6[i] + (3*c*c + 3*c*c*c)*e5[i] + (-6*c*c - 3*c - 3*c*c*c)*e4[i] + (1 + 3*c + c*c*c + 3*c*c)*e3[i];
            result[i] = v;
        }
        return result;
    }

    doubleSmooth(dataArr, ll, ls) {
        let e1 = this.ema(dataArr, ll, x=>x);
        return this.ema(e1, ls, x=>x);
    }

    highest(data, lookback, getter) {
        let res = new Array(data.length).fill(NaN);
        for(let i=0; i<data.length; i++) {
            let max = -Infinity;
            for(let j=Math.max(0, i-lookback+1); j<=i; j++) {
                max = Math.max(max, getter(data[j]));
            }
            res[i] = max === -Infinity ? NaN : max;
        }
        return res;
    }

    lowest(data, lookback, getter) {
        let res = new Array(data.length).fill(NaN);
        for(let i=0; i<data.length; i++) {
            let min = Infinity;
            for(let j=Math.max(0, i-lookback+1); j<=i; j++) {
                min = Math.min(min, getter(data[j]));
            }
            res[i] = min === Infinity ? NaN : min;
        }
        return res;
    }

    // --- Main Calculation ---
    calculate(candles) {
        const out = {
            wave1: [], wave2: [], wave3: [], wave4: [], wave200: [],
            e5: [], e13: [], e34: [], e50: [], e72: [], e89: [], e8: [], e9: [],
            we_smma: [],
            ha: [],
            markers: [], // combined markers (signals, volume, tsi)
            dashboard: {},
            mtf: { '1M': false, '5M': false }, // Mocked or calculated if data provided
            targetLines: []
        };

        const len = candles.length;
        if (len === 0) return out;

        const getC = d => d.close;
        const getH = d => d.high;
        const getL = d => d.low;
        const getO = d => d.open;
        const getV = d => d.volume;

        // Wolf Waves Core
        const wave1 = this.ema(candles, this.inputs.ema1_len, getC);
        const wave2 = this.ema(candles, this.inputs.ema2_len, getC);
        const wave3 = this.ema(candles, this.inputs.ema3_len, getC);
        const wave4 = this.ema(candles, this.inputs.ema4_len, getC);
        const wave200 = this.ema(candles, this.inputs.ema200_len, getC);

        // EMA Clouds
        const e5 = this.ema(candles, 5, getC);
        const e13 = this.ema(candles, 13, getC);
        const e34 = this.ema(candles, 34, getC);
        const e50 = this.ema(candles, 50, getC);
        const e72 = this.ema(candles, 72, getC);
        const e89 = this.ema(candles, 89, getC);
        const e8 = this.ema(candles, 8, getC);
        const e9 = this.ema(candles, 9, getC);

        // Wolf Edge SMMA
        const we_smma = this.smma(candles, this.inputs.we_length, getC);

        // TSI
        let pc = new Array(len).fill(0);
        let apc = new Array(len).fill(0);
        for (let i = 1; i < len; i++) {
            pc[i] = candles[i].close - candles[i-1].close;
            apc[i] = Math.abs(pc[i]);
        }
        let smooth_pc = this.doubleSmooth(pc, this.inputs.tsi_long, this.inputs.tsi_short);
        let smooth_apc = this.doubleSmooth(apc, this.inputs.tsi_long, this.inputs.tsi_short);
        let tsi_v = new Array(len).fill(NaN);
        for(let i=0; i<len; i++) {
            if(smooth_apc[i] !== 0) tsi_v[i] = 100.0 * (smooth_pc[i] / smooth_apc[i]);
        }
        let tsi_s = this.ema(tsi_v, this.inputs.tsi_signal, x=>x);

        // Volume Spikes
        let vol_sma = this.sma(candles, this.inputs.vol_lookback, getV);

        // Heikin-Ashi
        let ha_o = new Array(len).fill(NaN);
        let ha_c = new Array(len).fill(NaN);
        let ha_h = new Array(len).fill(NaN);
        let ha_l = new Array(len).fill(NaN);
        for(let i=0; i<len; i++) {
            ha_c[i] = (candles[i].open + candles[i].high + candles[i].low + candles[i].close) / 4.0;
            if (i === 0) {
                ha_o[i] = (candles[i].open + candles[i].close) / 2.0;
            } else {
                ha_o[i] = (ha_o[i-1] + ha_c[i-1]) / 2.0;
            }
            ha_h[i] = Math.max(candles[i].high, ha_o[i], ha_c[i]);
            ha_l[i] = Math.min(candles[i].low, ha_o[i], ha_c[i]);
        }

        // Wolf Rush 2025 Strategy Engine
        const wr_ema = this.ema(candles, this.inputs.wr_ema_len, getC);
        const wr_smma = this.smma(candles, this.inputs.wr_smma_len, getC);
        
        let trade_side = 0; // 0=flat, 1=long, -1=short
        let wait_buy = false;
        let wait_sell = false;
        let trend = 0;

        let ep = NaN, sl = NaN, tp1 = NaN, tp2 = NaN, tp3 = NaN;
        
        let highest20 = this.highest(candles, 20, getH);
        let lowest20 = this.lowest(candles, 20, getL);

        // Dashboard State Variables
        let dash_tsi = "-";
        let dash_vol = "-";
        let dash_trend = "FLAT";
        let dash_cloud = "Bear";
        let dash_smma = "Below";
        let dash_wave_1m = false; // Mock unless real data provided
        let dash_wave_5m = false;

        // Iterate through time for stateful logic (crosses, strategy signals, markers)
        for (let i = 1; i < len; i++) {
            const time = candles[i].time;
            
            // Format Outputs for Series
            if (!isNaN(wave200[i])) out.wave200.push({time, value: wave200[i]});
            if (!isNaN(wave1[i])) out.wave1.push({time, value: wave1[i]});
            if (!isNaN(wave2[i])) out.wave2.push({time, value: wave2[i]});
            if (!isNaN(wave3[i])) out.wave3.push({time, value: wave3[i]});
            if (!isNaN(wave4[i])) out.wave4.push({time, value: wave4[i]});
            
            if (!isNaN(e5[i])) out.e5.push({time, value: e5[i]});
            if (!isNaN(e13[i])) out.e13.push({time, value: e13[i]});
            if (!isNaN(e34[i])) out.e34.push({time, value: e34[i]});
            if (!isNaN(e50[i])) out.e50.push({time, value: e50[i]});
            if (!isNaN(e72[i])) out.e72.push({time, value: e72[i]});
            if (!isNaN(e89[i])) out.e89.push({time, value: e89[i]});
            if (!isNaN(e8[i])) out.e8.push({time, value: e8[i]});
            if (!isNaN(e9[i])) out.e9.push({time, value: e9[i]});
            if (!isNaN(we_smma[i])) out.we_smma.push({time, value: we_smma[i]});

            out.ha.push({time, open: ha_o[i], high: ha_h[i], low: ha_l[i], close: ha_c[i]});

            // TSI Cross
            let tsi_curl_up = tsi_v[i] > tsi_v[i-1] && tsi_v[i] < tsi_s[i];
            let tsi_curl_down = tsi_v[i] < tsi_v[i-1] && tsi_v[i] > tsi_s[i];
            if (tsi_curl_up) {
                out.markers.push({time, position: 'belowBar', color: 'white', shape: 'circle', text: 'Curl Up'});
            }
            if (tsi_curl_down) {
                out.markers.push({time, position: 'aboveBar', color: 'red', shape: 'circle', text: 'Curl Dn'});
            }

            // Volume Spike
            let vol_spike = candles[i].volume > (this.inputs.vol_ratio * vol_sma[i-1]);
            if (vol_spike) {
                out.markers.push({time, position: 'bottom', color: 'white', shape: 'square', text: 'Vol'});
            }

            // Wolf Rush Strategy
            let cross_up = (wr_ema[i-1] <= wr_smma[i-1]) && (wr_ema[i] > wr_smma[i]) && (candles[i].close > wr_smma[i]);
            let cross_dn = (wr_ema[i-1] >= wr_smma[i-1]) && (wr_ema[i] < wr_smma[i]) && (candles[i].close < wr_smma[i]);
            let bull72 = e72[i] > e89[i];
            let bear72 = e89[i] > e72[i];

            if (cross_up && trade_side === -1) trade_side = 0;
            if (cross_dn && trade_side === 1) trade_side = 0;
            if (cross_up && trade_side === 0 && !wait_sell && !wait_buy) { wait_buy = true; wait_sell = false; }
            if (cross_dn && trade_side === 0 && !wait_buy && !wait_sell) { wait_sell = true; wait_buy = false; }
            if (wait_buy && bull72 && trade_side === 0) { trade_side = 1; wait_buy = false; wait_sell = false; }
            if (wait_sell && bear72 && trade_side === 0) { trade_side = -1; wait_buy = false; wait_sell = false; }

            let we_above = (wr_ema[i] > we_smma[i]) && bull72;
            let we_below = (wr_ema[i] < we_smma[i]) && bear72;
            let we_above_prev = (wr_ema[i-1] > we_smma[i-1]) && (e72[i-1] > e89[i-1]);
            let we_below_prev = (wr_ema[i-1] < we_smma[i-1]) && (e72[i-1] < e89[i-1]);

            let sig_buy = we_above && !we_above_prev && trend < 1;
            let sig_sell = we_below && !we_below_prev && trend > -1;

            if (sig_buy) {
                trend = 1;
                ep = candles[i].close;
                sl = lowest20[i];
                let r = Math.abs(ep - sl);
                tp1 = ep + r * this.inputs.tp1_rr;
                tp2 = ep + r * this.inputs.tp2_rr;
                tp3 = ep + r * this.inputs.tp3_rr;
                out.markers.push({time, position: 'belowBar', color: '#00bcd4', shape: 'arrowUp', text: 'BUY', size: 2});
            }

            if (sig_sell) {
                trend = -1;
                ep = candles[i].close;
                sl = highest20[i];
                let r = Math.abs(ep - sl);
                tp1 = ep - r * this.inputs.tp1_rr;
                tp2 = ep - r * this.inputs.tp2_rr;
                tp3 = ep - r * this.inputs.tp3_rr;
                out.markers.push({time, position: 'aboveBar', color: '#0846fd', shape: 'arrowDown', text: 'SELL', size: 2});
            }

            if (trend === 1 && candles[i].low <= sl) trend = 2; // SL Hit Buy
            if (trend === -1 && candles[i].high >= sl) trend = -2; // SL Hit Sell

            // Final Dashboard State for the last bar
            if (i === len - 1) {
                dash_tsi = tsi_curl_up ? "Curl Up" : tsi_curl_down ? "Curl Dn" : "-";
                dash_vol = vol_spike ? "YES" : "-";
                dash_cloud = bull72 ? "Bull" : "Bear";
                dash_smma = candles[i].close > we_smma[i] ? "Above" : "Below";
                dash_trend = trend === 1 ? "LONG" : trend === -1 ? "SHORT" : trend === 2 ? "SL Hit B" : trend === -2 ? "SL Hit S" : "FLAT";
                
                // Mocks for MTF (in real prod, you'd pass 1m and 5m data)
                let fg = (wave1[i] + wave2[i])/2;
                let sg = (wave3[i] + wave4[i])/2;
                dash_wave_1m = fg > sg; // Assuming current TF is 1m, this is true.
                dash_wave_5m = fg > sg; // Mock

                if (trend === 1 || trend === -1) {
                    out.targetLines = [
                        { price: ep, title: 'Entry', color: 'gray', style: 'dashed' },
                        { price: sl, title: 'SL', color: 'red', style: 'solid' },
                        { price: tp1, title: 'TP1', color: 'green', style: 'dashed' },
                        { price: tp2, title: 'TP2', color: 'green', style: 'dashed' },
                        { price: tp3, title: 'TP3', color: 'green', style: 'dashed' }
                    ];
                }
            }
        }

        // Add S/R Logic here (simplified for performance in JS)
        // Finding pivots
        const pivot_period = this.inputs.pivot_period;
        let phs = [], pls = [];
        for (let i = pivot_period; i < len - pivot_period; i++) {
            let isPh = true, isPl = true;
            for(let j=1; j<=pivot_period; j++) {
                if (candles[i-j].high >= candles[i].high || candles[i+j].high > candles[i].high) isPh = false;
                if (candles[i-j].low <= candles[i].low || candles[i+j].low < candles[i].low) isPl = false;
            }
            if (isPh) phs.push({i, val: candles[i].high});
            if (isPl) pls.push({i, val: candles[i].low});
        }
        
        // We skip the complex 300-bar overlap strength algorithm for MVP due to O(N^2) JS bottleneck 
        // and just return the latest 2 S/R zones.
        let sr_boxes = [];
        if (phs.length > 0 && pls.length > 0) {
            let lastPh = phs[phs.length-1];
            let lastPl = pls[pls.length-1];
            sr_boxes.push({ top: lastPh.val + 10, bottom: lastPh.val - 10, type: 'resistance', startIndex: Math.max(0, len - 300) });
            sr_boxes.push({ top: lastPl.val + 10, bottom: lastPl.val - 10, type: 'support', startIndex: Math.max(0, len - 300) });
        }
        out.sr_boxes = sr_boxes;

        out.dashboard = {
            trend: dash_trend,
            cloud: dash_cloud,
            vol: dash_vol,
            smma: dash_smma,
            tsi: dash_tsi,
            wave1m: dash_wave_1m,
            wave5m: dash_wave_5m
        };

        return out;
    }
}

// Export for Node/Worker or Browser
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AlphaIndicatorEngine;
} else if (typeof self !== 'undefined') {
    self.AlphaIndicatorEngine = AlphaIndicatorEngine;
} else if (typeof window !== 'undefined') {
    window.AlphaIndicatorEngine = AlphaIndicatorEngine;
}
