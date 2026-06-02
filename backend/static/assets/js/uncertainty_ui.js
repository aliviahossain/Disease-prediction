/**
 * uncertainty_ui.js
 * Drop into: backend/static/js/uncertainty_ui.js
 * Add to base template before </body>:
 *   <script src="{{ url_for('static', filename='js/uncertainty_ui.js') }}"></script>
 *
 * Exports one function:  window.renderPredictionResult(container, apiResponse)
 *
 * - If apiResponse.is_sufficient === false  → renders amber warning card.
 * - If apiResponse.is_sufficient === true   → calls your existing render logic,
 *   then adds a risk badge so existing views are unchanged.
 */
 
(function () {
  'use strict';
 
  /* ── Inject styles once ──────────────────────────────────────────────── */
  if (!document.getElementById('uc-styles')) {
    const s = document.createElement('style');
    s.id = 'uc-styles';
    s.textContent = `
      .uc-card {
        display: flex; gap: 14px; align-items: flex-start;
        background: #fff8e6; border: 1.5px solid #e6a817;
        border-radius: 10px; padding: 18px 20px;
        animation: uc-in .3s ease; margin: 12px 0;
      }
      @media (prefers-color-scheme: dark) {
        .uc-card { background: #271f00; border-color: #c08000; }
        .uc-card .uc-title  { color: #ffd54f; }
        .uc-card .uc-reason { color: #c8a040; }
        .uc-card .uc-icon   { color: #ffd54f; }
        .uc-bar-fill        { background: #c08000; }
        .uc-bar-track       { background: #3a2c00; }
        .uc-badge.uc-warn   { color: #ffd54f; border-color: #ffd54f; }
        .uc-badge.uc-info   { color: #64b5f6; border-color: #64b5f6; }
      }
      .uc-icon   { font-size: 22px; flex-shrink: 0; color: #b07800; line-height: 1; margin-top: 2px; }
      .uc-body   { flex: 1; }
      .uc-title  { font-size: 15px; font-weight: 600; color: #7a5000; margin: 0 0 5px; }
      .uc-reason { font-size: 13px; color: #8a6200; line-height: 1.55; margin: 0 0 12px; }
      .uc-bar-label { font-size: 11px; color: #8a6200; margin-bottom: 3px; }
      .uc-bar-track { height: 5px; border-radius: 3px; background: #f0d888; overflow: hidden; }
      .uc-bar-fill  { height: 100%; border-radius: 3px; background: #d09000; transition: width .5s ease; }
      .uc-badges { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
      .uc-badge  {
        font-size: 11px; padding: 2px 9px; border-radius: 999px;
        border: 1px solid currentColor;
      }
      .uc-badge.uc-warn { color: #a07000; }
      .uc-badge.uc-info { color: #1565c0; }
      @keyframes uc-in { from { opacity:0; transform:translateY(5px); } to { opacity:1; transform:translateY(0); } }
    `;
    document.head.appendChild(s);
  }
 
  /* ── Helpers ─────────────────────────────────────────────────────────── */
 
  function esc(str) {
    return String(str || '')
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
 
  function buildUncertaintyCard(result) {
    const pct = Math.round((result.confidence || 0));   // already 0–100 from backend
    const el = document.createElement('div');
    el.className = 'uc-card';
    el.setAttribute('role', 'alert');
    el.setAttribute('aria-live', 'polite');
    el.innerHTML = `
      <div class="uc-icon" aria-hidden="true">⚠</div>
      <div class="uc-body">
        <p class="uc-title">Insufficient data to predict reliably</p>
        <p class="uc-reason">${esc(result.reason)}</p>
        <div class="uc-bar-label">Model confidence: ${pct}%</div>
        <div class="uc-bar-track"
             role="progressbar" aria-valuenow="${pct}" aria-valuemin="0" aria-valuemax="100"
             aria-label="Model confidence ${pct}%">
          <div class="uc-bar-fill" style="width:${pct}%"></div>
        </div>
        <div class="uc-badges">
          <span class="uc-badge uc-warn">Low confidence</span>
          <span class="uc-badge uc-info">Consult a healthcare professional</span>
        </div>
      </div>
    `;
    return el;
  }
 
  /* ── Public API ──────────────────────────────────────────────────────── */
 
  /**
   * Render a prediction API response into `container`.
   *
   * @param {HTMLElement} container  - Target DOM node (will be cleared first).
   * @param {object}      result     - Full JSON response from /api/ml/predict.
   *
   * Call this wherever your existing code renders prediction results, e.g.:
   *   const container = document.getElementById('prediction-results');
   *   renderPredictionResult(container, data);
   */
  window.renderPredictionResult = function (container, result) {
    if (!container) return;
    container.innerHTML = '';
 
    if (!result.is_sufficient) {
      container.appendChild(buildUncertaintyCard(result));
      return;
    }
    // When prediction IS sufficient, show colored confidence meter
function buildConfidenceMeter(confidence) {
    const pct = Math.round(confidence * 100);
    let band, color;
    
    if (pct < 40) {
        band = "Low"; color = "#22c55e";      // green
    } else if (pct < 70) {
        band = "Medium"; color = "#eab308";   // yellow  
    } else {
        band = "High"; color = "#ef4444";     // red
    }
    // render progress bar + badge
}
 
    // Sufficient data — let the rest of your existing rendering run.
    // This function intentionally does NOT replace your existing result HTML;
    // it only prepends a "sufficient data" notice and returns so that whatever
    // code already builds the full result card can continue unmodified.
    // Remove the dispatch below if you render entirely inside this function.
    container.dispatchEvent(new CustomEvent('predictionReady', { detail: result, bubbles: true }));
  };
 
  /**
   * Render uncertainty state for a single row in the predict-multiple table.
   * Call this after building each row to dim or badge low-confidence entries.
   *
   * @param {HTMLElement} row    - A <tr> or row container element.
   * @param {object}      pred   - One item from predictions[].
   */
  window.applyRowUncertainty = function (row, pred) {
    if (!row || pred.is_sufficient !== false) return;
    row.style.opacity = '0.55';
    row.title = pred.uncertainty_reason || 'Low confidence';
 
    const badge = document.createElement('span');
    badge.className = 'uc-badge uc-warn';
    badge.style.cssText = 'font-size:10px;padding:1px 7px;border-radius:999px;border:1px solid currentColor;color:#a07000;margin-left:6px;vertical-align:middle';
    badge.textContent = 'Low confidence';
 
    const firstCell = row.querySelector('td');
    if (firstCell) firstCell.appendChild(badge);
  };
})();