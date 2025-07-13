// -- הגדרות גלובליות --
const DASHBOARD_REFRESH_INTERVAL_MS = REFRESH_INTERVAL * 1000; // זמן רענון בלוח הבקרה (במילישניות)
var refreshElapsed = 0;
let refreshIntervalId = null;

// -- פונקציית עזר ל-DOM Ready --
function onReady(fn) {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', fn);
  } else {
    fn();
  }
}

// -- טעינה ראשונית בעת טעינת הדף --
onReady(async () => { // Make the callback async
    // Restore scroll position on load
    const savedY = localStorage.getItem('dashboardScrollY');
    if (savedY !== null) window.scrollTo(0, parseInt(savedY));

    // Perform initial render immediately
    await renderDashboard();
    
    // Start refresh interval AFTER initial render
    setInterval(() => {
        // Start progress bar for subsequent refreshes
        
        // Save scroll position before render
        localStorage.setItem('dashboardScrollY', window.scrollY);
        renderDashboard();
        // Restore scroll after render (longer delay for DOM update)
        setTimeout(function() {
            var y = localStorage.getItem('dashboardScrollY');
            if (y !== null) window.scrollTo(0, parseInt(y));
        }, 55);
    }, DASHBOARD_REFRESH_INTERVAL_MS);

  // לוגיקת מודל גרף מוגדל
  const modal = document.getElementById('enlarged-chart-modal');
  const closeBtn = document.getElementById('close-chart-modal');
  if (closeBtn) {
    closeBtn.onmouseover = () => { modal.style.display = 'none'; };
  }
  window.onclick = (e) => {
    if (e.target === modal) modal.style.display = 'none';
  }
  
  // Save scroll position before unload
  window.addEventListener('beforeunload', () => {
      localStorage.setItem('dashboardScrollY', window.scrollY);
  });

  // כפתור איפוס עסקאות
  const resetBtn = document.getElementById('reset-trades-btn');
  if (resetBtn) {
    resetBtn.addEventListener('click', async () => {
      try {
        const res = await fetch('/api/reset_trades', { method: 'POST' });
        if (res.ok) {
          resetBtn.classList.add('flash');
          setTimeout(() => resetBtn.classList.remove('flash'), 700);
          // Save scroll position before render
          localStorage.setItem('dashboardScrollY', window.scrollY);
          renderDashboard(true);
          // Restore scroll after render (longer delay for DOM update)
          setTimeout(function() {
              var y = localStorage.getItem('dashboardScrollY');
              if (y !== null) window.scrollTo(0, parseInt(y));
          }, 300);
        }
      } catch (e) {
        console.error('Reset trades failed:', e);
      }
    });
  }
});

// -- מאזין קליקים לגרפים (לאחר הרנדר) --
async function addChartClickHandlers(resultsCache) { // Accept resultsCache
  const charts = document.querySelectorAll('canvas[data-symbol]');
  charts.forEach(chart => {
    chart.onclick = function () {
      const symbol = chart.getAttribute('data-symbol');
      if (!symbol) return;
      showEnlargedChart(symbol, resultsCache); // Pass resultsCache
    };
  });
}

// -- הצגת גרף מוגדל במודל --
async function showEnlargedChart(symbol, resultsCache) { // Accept resultsCache
  const modal = document.getElementById('enlarged-chart-modal');
  const canvas = document.getElementById('enlarged-chart-canvas');
  if (window.enlargedChartInstance) {
    window.enlargedChartInstance.destroy();
  }
  // Use the cached results directly
  if (!resultsCache || !resultsCache[symbol]) {
    // Fallback to fetching if cache is not available (should not happen if called from renderDashboard)
    resultsCache = await fetchData();
    if (!resultsCache || !resultsCache[symbol]) return;
  }
  await createEnlargedChart(canvas, symbol, resultsCache[symbol], resultsCache);
  modal.style.display = 'flex';
}

// -- יצירת/עדכון גרף קווי מרובה (לוח בקרה) --
async function createOrUpdateMultiLineChart(symbol, metric, resultsCache, clearBuySell = false) {
  let chartInstance = window.dashboardChartInstances[symbol];
  let canvas = document.querySelector(`canvas[data-symbol="${symbol}"]`);

  // If canvas doesn't exist but chart instance does, destroy it (shouldn't happen with new render logic)
  if (!canvas && chartInstance) {
    chartInstance.destroy();
    delete window.dashboardChartInstances[symbol];
    chartInstance = null;
  }

  const colors = {
    med: '#00e5ff', binance: '#ff9800', bybit: '#4caf50', okx: '#e91e63'
  };

  const histories = [
    { key: 'price_history', label: 'med', color: colors.med },
    { key: 'binance_history', label: 'Binance', color: colors.binance },
    { key: 'bybit_history', label: 'Bybit', color: colors.bybit },
    { key: 'okx_history', label: 'OKX', color: colors.okx }
  ];

  let minY = Infinity, maxY = -Infinity;
  histories.forEach(h => {
    const hist = metric[h.key] || [];
    hist.forEach(p => {
      if (p[1] < minY) minY = p[1];
      if (p[1] > maxY) maxY = p[1];
    });
  });
  if (minY === Infinity) minY = 0;
  if (maxY === -Infinity) maxY = 100;

  let baseHistory = metric.price_history || [];
  if (baseHistory.length === 0 && metric.binance_history) {
    baseHistory = metric.binance_history.map((p, i) => {
      const binance = p[1];
      const bybit = metric.bybit_history[i]?.[1] ?? 0;
      const okx = metric.okx_history[i]?.[1] ?? 0;
      const med = (binance + bybit + okx) / 3;
      return [p[0], med];
    });
  }
  const labels = baseHistory.map(p => new Date(p[0] * 1000).toLocaleTimeString());

  const datasets = histories.map(h => ({
    label: `${symbol} - ${h.label}`,
    data: (metric[h.key] || []).map(p => p[1]),
    borderColor: h.color,
    borderWidth: 1.2,
    pointRadius: 1.6,
    fill: false,
    yAxisID: 'y',
  }));

  const { buyPoints, sellPoints } = await fetchTradePoints(symbol, resultsCache);
  if (!clearBuySell) {
    if (buyPoints.length)
      datasets.push({ label: 'Buy', data: buyPoints.map(p => ({ x: p.x, y: p.y })), backgroundColor: 'green', type: 'scatter', pointRadius: 10 });
    if (sellPoints.length)
      datasets.push({ label: 'Sell', data: sellPoints.map(p => ({ x: p.x, y: p.y })), backgroundColor: 'red', type: 'scatter', pointRadius: 10 });
  }

  if (chartInstance) {
    // Update existing chart
    chartInstance.data.labels = labels;
    chartInstance.data.datasets = datasets;
    chartInstance.options.scales.y.min = minY;
    chartInstance.options.scales.y.max = maxY;
    chartInstance.update();
  } else {
    // Create new chart
    // Canvas should already exist and be appended by renderDashboard
    if (!canvas) {
      console.error(`Canvas for symbol ${symbol} not found when creating new chart instance.`);
      return; // Should not happen with the new renderDashboard logic
    }
    chartInstance = new Chart(canvas.getContext('2d'), {
      type: 'line',
      data: { labels, datasets },
      options: {
        responsive: true,
        animation: false,
        plugins: {
          legend: { labels: { color: '#fff' } },
          title: { display: true, text: `${symbol} - Price`, color: '#00e5ff' },
          zoom: {
            pan: { enabled: true, mode: 'xy' },
            zoom: { drag: { enabled: true }, wheel: { enabled: false }, pinch: { enabled: true }, mode: 'xy' }
          }
        },
        scales: {
          x: { ticks: { color: '#ccc' }, title: { text: 'זמן', display: true, color: '#ccc' } },
          y: { ticks: { color: '#ccc' }, min: minY, max: maxY }
        }
      }
    });
    window.dashboardChartInstances[symbol] = chartInstance;
  }
}

// -- יצירת גרף מוגדל במודל --
async function createEnlargedChart(canvas, symbol, metric, resultsCache, clearBuySell = false) {
  const colors = {
    med: '#00e5ff', binance: '#ff9800', bybit: '#4caf50', okx: '#e91e63'
  };
  const histories = [
    { key: 'price_history', label: 'med', color: colors.med },
    { key: 'binance_history', label: 'Binance', color: colors.binance },
    { key: 'bybit_history', label: 'Bybit', color: colors.bybit },
    { key: 'okx_history', label: 'OKX', color: colors.okx }
  ];
  let minY = Infinity, maxY = -Infinity;
  histories.forEach(h => {
    const hist = metric[h.key] || [];
    hist.forEach(p => {
      if (p[1] < minY) minY = p[1];
      if (p[1] > maxY) maxY = p[1];
    });
  });
  if (minY === Infinity) minY = 0;
  if (maxY === -Infinity) maxY = 100;
  let baseHistory = metric.price_history || [];
  if (baseHistory.length === 0 && metric.binance_history) {
    baseHistory = metric.binance_history.map((p, i) => {
      const binance = p[1];
      const bybit = metric.bybit_history[i]?.[1] ?? 0;
      const okx = metric.okx_history[i]?.[1] ?? 0;
      const med = (binance + bybit + okx) / 3;
      return [p[0], med];
    });
  }
  const labels = baseHistory.map(p => new Date(p[0] * 1000).toLocaleTimeString());
  const datasets = histories.map(h => ({
    label: `${symbol} - ${h.label}`,
    data: (metric[h.key] || []).map(p => p[1]),
    borderColor: h.color,
    borderWidth: 2,
    pointRadius: 2,
    fill: false,
    yAxisID: 'y',
  }));
  const { buyPoints, sellPoints } = await fetchTradePoints(symbol, resultsCache);
  if (!clearBuySell) {
    if (buyPoints.length)
      datasets.push({ label: 'Buy', data: buyPoints.map(p => ({ x: p.x, y: p.y })), backgroundColor: 'green', type: 'scatter', pointRadius: 12 });
    if (sellPoints.length)
      datasets.push({ label: 'Sell', data: sellPoints.map(p => ({ x: p.x, y: p.y })), backgroundColor: 'red', type: 'scatter', pointRadius: 12 });
  }
  window.enlargedChartInstance = new Chart(canvas.getContext('2d'), {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true,
      plugins: {
        legend: { labels: { color: '#fff' } },
        title: { display: true, text: `${symbol} - Price (מוגדל)`, color: '#00e5ff' },
        zoom: {
          pan: { enabled: true, mode: 'xy' },
          zoom: { drag: { enabled: true }, wheel: { enabled: false }, pinch: { enabled: true }, mode: 'xy' }
        }
      },
      scales: {
        x: { ticks: { color: '#ccc' }, title: { text: 'זמן', display: true, color: '#ccc' } },
        y: { ticks: { color: '#ccc' }, min: minY, max: maxY }
      }
    }
  });
}

// -- שליפת נתונים עיקריים --
async function fetchData() {
  try {
    const res = await fetch('/api/live');
    if (!res.ok) {
      console.error("HTTP error!", res.status);
      return null;
    }
    const response = await res.json();
    return response.data;
  } catch (error) {
    console.error("Error fetching data:", error);
    return null;
  }
}

// -- שליפת נקודות מסחר לכל סימבול --
async function fetchTradePoints(symbol, cache = null) {
  if (cache && cache[symbol]) {
    return {
      buyPoints: cache[symbol].buyPoints || [],
      sellPoints: cache[symbol].sellPoints || []
    };
  }
  try {
    const res = await fetch('/api/live');
    if (!res.ok) return { buyPoints: [], sellPoints: [] };
    const results = await res.json();
    if (results.data && results.data[symbol]) {
      return {
        buyPoints: results.data[symbol].buyPoints || [],
        sellPoints: results.data[symbol].sellPoints || []
      };
    }
  } catch (e) {
    console.error("Error fetching trade points:", e);
  }
  return { buyPoints: [], sellPoints: [] };
}

// Global object to store chart instances
window.dashboardChartInstances = window.dashboardChartInstances || {};

// -- רנדר לוח בקרה --
async function renderDashboard(clearBuySell = false) {
  refreshElapsed = 0;
  const results = await fetchData();
  refreshElapsed = 0;

  const chartContainer = document.getElementById('line-charts');
  
  if (!results || Object.keys(results).length === 0) {
    // Destroy all existing charts and clear container if no data
    for (const symbol in window.dashboardChartInstances) {
      window.dashboardChartInstances[symbol].destroy();
      delete window.dashboardChartInstances[symbol];
    }
    chartContainer.innerHTML = '<p style="color:white;">אין נתונים זמינים.</p>';
    return;
  }

  const sortedSymbols = Object.keys(results).sort((a, b) => (a === "ALL" ? -1 : b === "ALL" ? 1 : a.localeCompare(b)));
  chartContainer.style.gridTemplateColumns = sortedSymbols.length > 2 ? 'repeat(2, 1fr)' : '';

  const currentSymbols = new Set(sortedSymbols.filter(s => s !== 'ALL'));
  const existingChartSymbols = new Set(Object.keys(window.dashboardChartInstances));

  // Remove charts for symbols that are no longer present
  for (const symbol of existingChartSymbols) {
    if (!currentSymbols.has(symbol)) {
      if (window.dashboardChartInstances[symbol]) {
        window.dashboardChartInstances[symbol].destroy();
        delete window.dashboardChartInstances[symbol];
      }
      const cardToRemove = document.querySelector(`canvas[data-symbol="${symbol}"]`)?.closest('.card');
      if (cardToRemove) {
        cardToRemove.remove();
      }
    }
  }

  // Create or update charts for current symbols
  // This loop now ensures cards/canvases are in the DOM before chart creation/update
  for (const symbol of sortedSymbols) {
    if (symbol === 'ALL') continue;
    const metric = results[symbol];
    if (!metric || (!metric.price_history && !(metric.binance_history && metric.bybit_history && metric.okx_history))) continue;

    let card = document.querySelector(`.card canvas[data-symbol="${symbol}"]`)?.closest('.card');
    if (!card) {
      // Create new card and canvas if it doesn't exist
      card = document.createElement('div');
      card.className = 'card';
      const canvas = document.createElement('canvas');
      canvas.setAttribute('data-symbol', symbol);
      card.appendChild(canvas);
      chartContainer.appendChild(card); // Append immediately
    }
    // If card already exists, it's already in the DOM, no need to re-append
    
    await createOrUpdateMultiLineChart(symbol, metric, results, clearBuySell);
  }

  updateTable(results);
  addTransactionButtonListeners();
  // window.scrollTo(0, 0); // Removed to allow scroll restoration
  // resetRefreshProgress(); // Removed from here, now called in setInterval
  addChartClickHandlers(results); // Pass results to the handler
}

// -- עדכון טבלת נתונים --
function updateTable(results) {
  //resetRefreshProgress(); // Removed from here, now called in setInterval
  const tbody = document.getElementById('SQL_DB_DashboardData-table').getElementsByTagName('tbody')[0];
  const existingRows = new Map();
  
  // Map existing rows by symbol
  Array.from(tbody.rows).forEach(row => {
    const symbol = row.cells[0].textContent;
    existingRows.set(symbol, row);
  });

  const sortedSymbols = Object.keys(results).sort((a, b) => (a === "ALL" ? -1 : b === "ALL" ? 1 : a.localeCompare(b)));
  const fragment = document.createDocumentFragment();

  for (const symbol of sortedSymbols) {
    if (symbol === 'ALL') continue;
    const m = results[symbol];
    let row = existingRows.get(symbol);

    if (row) {
      // Update existing row
      row.cells[1].textContent = m.momentum?.toFixed(4) || '';
      row.cells[2].textContent = m.buy_pressure?.toFixed(4) || '';
      row.cells[3].textContent = m.sell_pressure?.toFixed(4) || '';
      const signalCell = row.cells[4];
      signalCell.textContent = m.signal || '';
      signalCell.className = m.signal ? `signal-${m.signal.toLowerCase()}` : '';
      row.cells[5].textContent = m.position || '';
      const pnlCell = row.cells[6];
      pnlCell.textContent = (typeof m.pnl_pct === 'number') ? `${m.pnl_pct.toFixed(4)}%` : '';
      pnlCell.className = ''; // Clear previous classes
      const pnlClass = m.pnl_pct > 0 ? 'positive-pnl' : m.pnl_pct < 0 ? 'negative-pnl' : null;
      if (pnlClass) pnlCell.classList.add(pnlClass);
      row.cells[7].textContent = m.total_buy_trades ?? '';
      row.cells[8].textContent = m.total_sell_trades ?? '';
      const profitCell = row.cells[9];
      profitCell.textContent = m.total_profit?.toFixed(4) || '';
      profitCell.className = ''; // Clear previous classes
      const profitClass = m.total_profit > 0 ? 'positive-pnl' : m.total_profit < 0 ? 'negative-pnl' : null;
      if (profitClass) profitCell.classList.add(profitClass);

      const btn = row.cells[10].querySelector('.transactions-button');
      if (btn) {
        if ((m.total_buy_trades ?? 0) === 0 && (m.total_sell_trades ?? 0) === 0) {
          btn.classList.add('disabled');
          btn.disabled = true;
        } else {
          btn.classList.remove('disabled');
          btn.disabled = false;
        }
      }
      existingRows.delete(symbol); // Mark as processed
    } else {
      // Create new row
      row = tbody.insertRow();
      row.insertCell().textContent = symbol;
      row.insertCell().textContent = m.momentum?.toFixed(4) || '';
      row.insertCell().textContent = m.buy_pressure?.toFixed(4) || '';
      row.insertCell().textContent = m.sell_pressure?.toFixed(4) || '';
      const signalCell = row.insertCell();
      signalCell.textContent = m.signal || '';
      if (m.signal) signalCell.className = `signal-${m.signal.toLowerCase()}`;
      row.insertCell().textContent = m.position || '';
      const pnlCell = row.insertCell();
      pnlCell.textContent = (typeof m.pnl_pct === 'number') ? `${m.pnl_pct.toFixed(4)}%` : '';
      const pnlClass = m.pnl_pct > 0 ? 'positive-pnl' : m.pnl_pct < 0 ? 'negative-pnl' : null;
      if (pnlClass) pnlCell.classList.add(pnlClass);
      row.insertCell().textContent = m.total_buy_trades ?? '';
      row.insertCell().textContent = m.total_sell_trades ?? '';
      const profitCell = row.insertCell();
      profitCell.textContent = m.total_profit?.toFixed(4) || '';
      const profitClass = m.total_profit > 0 ? 'positive-pnl' : m.total_profit < 0 ? 'negative-pnl' : null;
      if (profitClass) profitCell.classList.add(profitClass);

      const txCell = row.insertCell();
      const btn = document.createElement('button');
      btn.textContent = 'הצג עסקאות';
      btn.className = 'transactions-button';
      btn.dataset.symbol = symbol;
      if ((m.total_buy_trades ?? 0) === 0 && (m.total_sell_trades ?? 0) === 0) {
        btn.classList.add('disabled');
        btn.disabled = true;
      }
      txCell.appendChild(btn);
    }
    fragment.appendChild(row); // Append to fragment to maintain order
  }

  // Remove rows that are no longer present
  existingRows.forEach(row => row.remove());

  // Append the reordered/updated rows to the tbody
  tbody.innerHTML = ''; // Clear existing content before appending fragment
  tbody.appendChild(fragment);
}

// -- התחל את סרגל ההתקדמות לרענון --
function updateRefreshProgress() {
  const bar = document.getElementById('refresh-progress-bar');
  const label = document.getElementById('refresh-progress-label');
  if (!bar || !label) return;
  const percent = Math.min(100, (refreshElapsed / REFRESH_INTERVAL) * 100);
  bar.style.width = `${percent}%`;
  let left = REFRESH_INTERVAL - refreshElapsed;
  label.textContent = ` בעוד ${parseInt(left)} שניות`;
  refreshElapsed += 0.25;
}

// Run updateRefreshProgress every 1 second
if (window.refreshProgressIntervalId) {
  clearInterval(window.refreshProgressIntervalId);
}
window.refreshProgressIntervalId = setInterval(updateRefreshProgress, 250);



// -- עסקאות: הוספת מאזינים לכפתורים (באמצעות Event Delegation) --
function addTransactionButtonListeners() {
  const tbody = document.getElementById('SQL_DB_DashboardData-table').getElementsByTagName('tbody')[0];
  // Remove any existing listener to prevent duplicates
  if (window.transactionTableListener) {
    tbody.removeEventListener('click', window.transactionTableListener);
  }

  const listener = async function (event) {
    const button = event.target.closest('.transactions-button');
    if (button && !button.disabled) {
      const symbol = button.dataset.symbol;
      displayTransactions(symbol);
    }
  };
  tbody.addEventListener('click', listener);
  window.transactionTableListener = listener; // Store the listener to remove it later
}

// -- פונקציה להצגת עסקאות (סטאב) --
async function displayTransactions(symbol) {
  try {
    const response = await fetch(`/api/transactions/${symbol}`);
    const transactions = await response.json();
    let html = `<h3>עסקאות עבור ${symbol}</h3>`;
    if (transactions.length === 0) {
      html += "<p>אין עסקאות זמינות.</p>";
    } else {
      html += `<table>
        <tr>
          <th>סוג</th>
          <th>מחיר</th>
          <th>זמן</th>
          <th>סיבה</th>
          <th>אות</th>
          <th>רווח (%)</th>
        </tr>`;
      transactions.forEach(tx => {
        html += `<tr>
          <td>${tx.action ?? ''}</td>
          <td>${Number(tx.price).toFixed(4)}</td>
          <td>${tx.timestamp ?? ''}</td>
          <td>${tx.reason ?? ''}</td>
          <td>${tx.signal ?? ''}</td>
          <td>${tx.net_profit !== undefined && tx.net_profit !== null ? (tx.net_profit * 100).toFixed(2) : ''}</td>
        </tr>`;
      });
      html += `</table>`;
    }
    const modal = document.getElementById('transactions-modal');
    if (modal) {
      // Add close button always at the top
      modal.innerHTML = `<button id="close-transactions-modal" style="float:left;">סגור❌ </button>` + html;
      modal.style.display = 'block';
      // Add close event
      document.getElementById('close-transactions-modal').onclick = function() {
        modal.style.display = 'none';
        modal.innerHTML = ""; // clear content
      };
    } 
  } catch (error) {
    console.error("Error fetching transactions:", error);
    const modal = document.getElementById('transactions-modal');
    if (modal) {
      modal.innerHTML = `<h3>שגיאה בטעינת עסקאות</h3>`;
      modal.style.display = 'block';
    }
  }    
} 