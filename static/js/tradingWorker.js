/**
 * Alpha Trading Worker
 * Offloads indicator calculations to background thread.
 */

self.importScripts('/static/js/alphaIndicatorEngine.js');

const engine = new self.AlphaIndicatorEngine();

self.onmessage = function(e) {
    const { type, payload } = e.data;
    
    if (type === 'CALCULATE') {
        const candles = payload.candles;
        // Run heavy calculations
        const result = engine.calculate(candles);
        
        // Return structured payload back to main thread
        self.postMessage({
            type: 'CALCULATE_SUCCESS',
            payload: result
        });
    }
};
