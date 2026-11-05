/**
 * FinTech Institutional Client-Side Script
 * Dynamic Market Surveillance & Analytical Engine for NSE & BSE
 */

document.addEventListener('DOMContentLoaded', () => {
    initGlobalSearch();
    initTabNavigation();
    initDCFCalculator();
    initLiveSync();
    initLiveTickerPolling();
    initStockDetailLiveSync();
});

/**
 * Global Stock Search with Autocomplete
 */
function initGlobalSearch() {
    const searchInput = document.getElementById('globalSearchInput');
    const searchDropdown = document.getElementById('globalSearchDropdown');

    if (!searchInput || !searchDropdown) return;

    let debounceTimer;

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.trim();
        clearTimeout(debounceTimer);

        if (query.length < 1) {
            searchDropdown.style.display = 'none';
            return;
        }

        debounceTimer = setTimeout(() => {
            fetch(`/api/search/?q=${encodeURIComponent(query)}`)
                .then(res => res.json())
                .then(data => {
                    const results = data.results || [];
                    if (results.length === 0) {
                        searchDropdown.innerHTML = '<div style="padding: 0.75rem 1rem; color: #64748b; font-size: 0.85rem;">No stocks found</div>';
                        searchDropdown.style.display = 'block';
                        return;
                    }

                    searchDropdown.innerHTML = results.map(s => `
                        <a href="${s.url}" class="search-item">
                            <div>
                                <span style="font-weight: 700; color: #60a5fa;">${s.clean_symbol}</span>
                                <span style="font-size: 0.75rem; background: rgba(255,255,255,0.08); padding: 0.1rem 0.35rem; border-radius: 3px; margin-left: 0.4rem;">${s.exchange}</span>
                                <div style="font-size: 0.75rem; color: #94a3b8;">${s.name}</div>
                            </div>
                            <div style="text-align: right;">
                                <div style="font-family: var(--font-mono); font-weight: 600;">${s.price}</div>
                                <div style="font-size: 0.75rem;" class="${s.is_positive ? 'text-positive' : 'text-negative'}">${s.change}</div>
                            </div>
                        </a>
                    `).join('');

                    searchDropdown.style.display = 'block';
                })
                .catch(err => console.error('Search error:', err));
        }, 200);
    });

    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !searchDropdown.contains(e.target)) {
            searchDropdown.style.display = 'none';
        }
    });
}

/**
 * Tab Navigation Component
 */
function initTabNavigation() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    if (!tabButtons.length) return;

    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-target');
            const parent = btn.closest('.tab-container') || document;

            parent.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            parent.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

            btn.classList.add('active');
            const targetPane = document.getElementById(targetId);
            if (targetPane) {
                targetPane.classList.add('active');
                // Trigger chart resizing when unhiding tab
                window.dispatchEvent(new Event('resize'));
                if (window.activePriceChart) {
                    setTimeout(() => window.activePriceChart.resize(), 50);
                }
            }
        });
    });
}

/**
 * Dynamic DCF Interactive Calculator
 */
function initDCFCalculator() {
    const dcfForm = document.getElementById('dcfCalculatorForm');
    if (!dcfForm) return;

    const symbol = dcfForm.getAttribute('data-symbol');
    const fcfInput = document.getElementById('dcf_fcf');
    const cagrInput = document.getElementById('dcf_cagr');
    const waccInput = document.getElementById('dcf_wacc');
    const terminalInput = document.getElementById('dcf_terminal');
    const cashInput = document.getElementById('dcf_cash');
    const debtInput = document.getElementById('dcf_debt');

    const recalculate = () => {
        const payload = {
            fcf_per_share: parseFloat(fcfInput.value) || 0,
            fcf_cagr: parseFloat(cagrInput.value) || 12,
            wacc: parseFloat(waccInput.value) || 11,
            terminal_growth: parseFloat(terminalInput.value) || 3,
            cash_per_share: parseFloat(cashInput.value) || 0,
            debt_per_share: parseFloat(debtInput.value) || 0
        };

        // Update slider labels
        if (document.getElementById('cagr_val')) document.getElementById('cagr_val').textContent = `${payload.fcf_cagr}%`;
        if (document.getElementById('wacc_val')) document.getElementById('wacc_val').textContent = `${payload.wacc}%`;
        if (document.getElementById('terminal_val')) document.getElementById('terminal_val').textContent = `${payload.terminal_growth}%`;

        fetch(`/research/${symbol}/api/dcf/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(data => {
            if (data.intrinsic_value_per_share !== undefined) {
                document.getElementById('dcf_intrinsic_val').textContent = `₹${data.intrinsic_value_per_share.toFixed(2)}`;
                
                const upsideElem = document.getElementById('dcf_upside_val');
                const sign = data.upside_potential_pct >= 0 ? '+' : '';
                upsideElem.textContent = `${sign}${data.upside_potential_pct.toFixed(1)}%`;
                upsideElem.className = data.upside_potential_pct >= 0 ? 'text-positive' : 'text-negative';

                document.getElementById('dcf_mos_val').textContent = `${data.margin_of_safety_pct.toFixed(1)}%`;
                
                const verdictElem = document.getElementById('dcf_verdict_val');
                verdictElem.textContent = data.valuation_verdict;
                if (data.valuation_verdict === 'Undervalued') {
                    verdictElem.className = 'action-badge action-strong-buy';
                } else if (data.valuation_verdict === 'Fairly Valued') {
                    verdictElem.className = 'action-badge action-research';
                } else {
                    verdictElem.className = 'action-badge action-avoid';
                }

                document.getElementById('dcf_pv_explicit').textContent = `₹${data.pv_explicit_fcfs.toFixed(2)}`;
                document.getElementById('dcf_pv_terminal').textContent = `₹${data.pv_terminal_value.toFixed(2)}`;
                document.getElementById('dcf_terminal_weight').textContent = `${data.terminal_value_weight_pct}%`;
            }
        })
        .catch(err => console.error('DCF calculation error:', err));
    };

    [fcfInput, cagrInput, waccInput, terminalInput, cashInput, debtInput].forEach(elem => {
        if (elem) {
            elem.addEventListener('input', recalculate);
        }
    });
}

/**
 * Real-Time Exchange Synchronization Trigger
 */
function initLiveSync() {
    const btnSync = document.getElementById('btnSyncMarket');
    const spinIcon = document.getElementById('syncSpinIcon');
    const btnText = document.getElementById('syncBtnText');

    if (!btnSync) return;

    btnSync.addEventListener('click', () => {
        btnSync.disabled = true;
        btnSync.style.opacity = '0.7';
        if (spinIcon) spinIcon.style.animation = 'spin 1s linear infinite';
        if (btnText) btnText.textContent = 'Syncing...';

        fetch('/api/market/sync/')
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showToast(`Exchange sync complete: ${data.updated_count} equities updated.`, 'success');
                    updateTickerBar(data.indices);

                    // If active on a stock research page, keep its chart synchronized
                    const btnStockSync = document.getElementById('btnSyncStock');
                    if (btnStockSync && !btnStockSync.disabled) {
                        btnStockSync.click();
                    }
                } else {
                    showToast('Market sync completed with cached feeds.', 'info');
                }
            })
            .catch(err => {
                console.warn('Sync notice:', err);
                showToast('Exchange feed latency; using cached real-time prices.', 'info');
            })
            .finally(() => {
                btnSync.disabled = false;
                btnSync.style.opacity = '1';
                if (spinIcon) spinIcon.style.animation = 'none';
                if (btnText) btnText.textContent = 'Sync Live Feeds';
            });
    });
}

/**
 * Continuous Background Ticker Polling (45-second cycle)
 */
function initLiveTickerPolling() {
    setInterval(() => {
        fetch('/api/market/pulse/')
            .then(res => res.json())
            .then(data => {
                if (data.indices) {
                    updateTickerBar(data.indices);
                }
            })
            .catch(err => console.debug('Pulse polling skipped:', err));
    }, 45000);
}

/**
 * Updates Ticker Bar Chips with Smooth Animation
 */
function updateTickerBar(indices) {
    if (!indices || !indices.length) return;

    indices.forEach(idx => {
        // e.g. ^nsei -> nsei
        const slug = idx.symbol.toLowerCase().replace(/[^a-z0-9]/g, '-').replace(/^-+|-+$/g, '');
        const valElem = document.getElementById(`ticker-val-${slug}`);
        const pctElem = document.getElementById(`ticker-pct-${slug}`);

        if (valElem) {
            valElem.textContent = idx.value.toFixed(2);
            valElem.className = `val ${idx.is_positive ? 'text-positive' : 'text-negative'}`;
        }
        if (pctElem) {
            const sign = idx.is_positive ? '+' : '';
            pctElem.textContent = `${sign}${idx.change_pct.toFixed(2)}%`;
            pctElem.className = idx.is_positive ? 'text-positive' : 'text-negative';
        }
    });
}

/**
 * Single Stock Live Sync in Stock Analysis Page
 */
function initStockDetailLiveSync() {
    const btnSync = document.getElementById('btnSyncStock');
    const spinIcon = document.getElementById('stockSyncSpin');
    const btnText = document.getElementById('stockSyncText');

    if (!btnSync) return;

    btnSync.addEventListener('click', () => {
        const symbol = btnSync.getAttribute('data-symbol');
        if (!symbol) return;

        btnSync.disabled = true;
        if (spinIcon) spinIcon.style.animation = 'spin 1s linear infinite';
        if (btnText) btnText.textContent = 'Syncing...';

        fetch(`/research/${encodeURIComponent(symbol)}/api/sync/`)
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const priceElem = document.getElementById('stockLivePrice');
                    const changeElem = document.getElementById('stockLiveChange');
                    const peElem = document.getElementById('stockLivePE');
                    const compElem = document.getElementById('stockLiveComposite');
                    const actionElem = document.getElementById('stockLiveAction');

                    if (priceElem && data.current_price) {
                        priceElem.textContent = `₹${data.current_price.toFixed(2)}`;
                    }
                    if (changeElem && data.day_change !== undefined) {
                        const sign = data.day_change_pct >= 0 ? '▲ +' : '▼ ';
                        changeElem.textContent = `${sign}${data.day_change.toFixed(2)} (${data.day_change_pct.toFixed(2)}%)`;
                        changeElem.className = `font-mono ${data.day_change_pct >= 0 ? 'text-positive' : 'text-negative'}`;
                    }
                    if (peElem && data.pe_ratio) {
                        peElem.textContent = data.pe_ratio.toFixed(1);
                    }
                    if (compElem && data.composite_score) {
                        compElem.textContent = `${data.composite_score.toFixed(1)} / 100`;
                    }
                    if (actionElem && data.action) {
                        actionElem.textContent = data.action;
                    }

                    // Dynamically refresh technical tracking chart with updated tracking data
                    if (data.chart_data && typeof window.updatePriceChartWithData === 'function') {
                        window.updatePriceChartWithData(data.chart_data);
                    }

                    showToast(`Updated ${data.clean_symbol} to live exchange price ₹${data.current_price.toFixed(2)} and refreshed tracking chart`, 'success');
                }
            })
            .catch(err => {
                console.error('Stock quote sync error:', err);
                showToast('Unable to fetch live quote at this moment.', 'error');
            })
            .finally(() => {
                btnSync.disabled = false;
                if (spinIcon) spinIcon.style.animation = 'none';
                if (btnText) btnText.textContent = 'Sync Live Quote';
            });
    });
}

/**
 * Lightweight Toast Notification Component
 */
function showToast(message, type = 'info') {
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.style.cssText = 'position: fixed; bottom: 20px; right: 20px; z-index: 9999; display: flex; flex-direction: column; gap: 8px;';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    const bg = type === 'success' ? '#065f46' : type === 'error' ? '#991b1b' : '#1e3a8a';
    const border = type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6';

    toast.style.cssText = `
        background: ${bg};
        border-left: 4px solid ${border};
        color: #fff;
        padding: 0.75rem 1.25rem;
        border-radius: 6px;
        font-size: 0.82rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        opacity: 0;
        transform: translateY(10px);
        transition: all 0.25s ease;
        display: flex;
        align-items: center;
        gap: 8px;
    `;
    toast.innerHTML = `<span>●</span><span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateY(0)';
    }, 10);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue || '';
}

// Add CSS keyframe for spinner
const style = document.createElement('style');
style.textContent = `
    @keyframes spin { 100% { transform: rotate(360deg); } }
`;
document.head.appendChild(style);
