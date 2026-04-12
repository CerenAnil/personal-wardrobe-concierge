/**
 * Wardrobe Concierge — frontend state machine
 *
 * States: idle -> processing -> awaiting_approval -> idle
 */

const API     = 'http://localhost:8000';
const USER_ID = 'user_001';

// ── State ──────────────────────────────────────────────────────────────────
let state = {
  phase:     'idle',   // idle | processing | awaiting_approval
  occasion:  '',
  sessionId: null,
};

// ── Color map ──────────────────────────────────────────────────────────────
const COLOR_MAP = {
  'white':         '#f5f5f0',
  'black':         '#1a1a1a',
  'navy':          '#1e2d5a',
  'dark indigo':   '#1c2148',
  'mid blue':      '#4a6fa5',
  'light blue':    '#7bafd4',
  'grey':          '#808080',
  'charcoal':      '#2f3030',
  'light grey':    '#c0c0be',
  'camel':         '#c19a6b',
  'tan':           '#d2a679',
  'brown':         '#7b4f2e',
  'beige':         '#d4c4a8',
  'cream':         '#f5f0e8',
  'ivory':         '#fffff0',
  'olive':         '#6b6e3a',
  'dark green':    '#2d4a2d',
  'burgundy':      '#800020',
  'rust':          '#b7410e',
  'tortoiseshell': '#8b4513',
  'gold':          '#c5a028',
  'silver':        '#aaaaaa',
};

function colorDot(color) {
  const bg = COLOR_MAP[color?.toLowerCase()] || '#444';
  return `<div class="item-color-dot" style="background:${bg}" title="${color || ''}"></div>`;
}

function formalityDots(level) {
  return Array.from({ length: 5 }, (_, i) =>
    `<div class="dot ${i < level ? 'filled' : ''}"></div>`
  ).join('');
}

// ── Loading messages ───────────────────────────────────────────────────────
const LOADING_MSGS = [
  'Searching your wardrobe...',
  'Checking colour harmony...',
  'Consulting the graph...',
  'Picking the right pieces...',
  'Almost there...',
];
let loadingMsgIdx = 0;
let loadingInterval = null;

function startLoadingCycle(node) {
  loadingMsgIdx = 0;
  const span = node.querySelector('span');
  loadingInterval = setInterval(() => {
    loadingMsgIdx = (loadingMsgIdx + 1) % LOADING_MSGS.length;
    if (span) span.textContent = LOADING_MSGS[loadingMsgIdx];
  }, 2200);
}

function stopLoadingCycle() {
  clearInterval(loadingInterval);
  loadingInterval = null;
}

// ── DOM helpers ────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);
const feed = () => $('messages');

function setPhase(p) {
  state.phase = p;
  const btn = $('submitBtn');
  const label = btn.querySelector('.btn-label');
  const spinner = btn.querySelector('.btn-spinner');
  if (p === 'idle') {
    btn.disabled = !state.occasion;
    label.textContent = 'Build outfit';
    spinner.hidden = true;
  } else {
    btn.disabled = true;
    label.textContent = p === 'processing' ? 'Building...' : 'Building...';
    spinner.hidden = false;
  }
}

function hideEmpty() {
  const el = $('emptyState');
  if (el) el.style.display = 'none';
}

function addNode(html) {
  const div = document.createElement('div');
  div.innerHTML = html.trim();
  const child = div.firstElementChild;
  feed().appendChild(child);
  child.scrollIntoView({ behavior: 'smooth', block: 'end' });
  return child;
}

// ── Occasion chips ─────────────────────────────────────────────────────────
document.querySelectorAll('.chip').forEach(chip => {
  chip.addEventListener('click', () => {
    document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
    state.occasion = chip.dataset.occasion;
    if (state.phase === 'idle') $('submitBtn').disabled = false;
  });
});

// ── App ────────────────────────────────────────────────────────────────────
const app = {

  quickFill(query, occasion) {
    document.querySelectorAll('.chip').forEach(c => {
      c.classList.toggle('active', c.dataset.occasion === occasion);
    });
    state.occasion = occasion;
    $('submitBtn').disabled = false;
    this.submit(query);
  },

  // ── Submit ───────────────────────────────────────────────────────────────
  async submit(overrideQuery) {
    if (state.phase !== 'idle') return;

    const city      = $('cityInput').value.trim();
    const dressCode = $('dressCodeInput').value;
    const whoWith   = $('whoWithInput').value.trim();
    const occasion  = state.occasion;

    if (!occasion) return;

    const rawQuery = overrideQuery ||
      [occasion, dressCode, city ? `in ${city}` : '', whoWith ? `with ${whoWith}` : '']
        .filter(Boolean).join(', ');

    hideEmpty();
    setPhase('processing');

    addNode(`<div class="query-bubble">${rawQuery}</div>`);

    const spinnerNode = addNode(`
      <div class="status-row">
        <div class="spinner"></div>
        <span>${LOADING_MSGS[0]}</span>
      </div>
    `);
    startLoadingCycle(spinnerNode);

    try {
      const res = await fetch(`${API}/outfit`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({
          raw_query:  rawQuery,
          user_id:    USER_ID,
          city:       city     || null,
          dress_code: dressCode || null,
          who_with:   whoWith  || null,
        }),
      });

      stopLoadingCycle();
      spinnerNode.remove();

      if (!res.ok) {
        const err = await res.json();
        showError(err.detail || 'Server error');
        setPhase('idle');
        return;
      }

      const data = await res.json();
      state.sessionId = data.session_id;

      if (data.status === 'error' || (!data.outfit && data.error)) {
        showError(data.error || 'Could not build an outfit. Check your API key and try again.');
        setPhase('idle');
        return;
      }

      if (data.status === 'awaiting_approval' && data.outfit) {
        renderOutfitCard(data.outfit, data.error);
        setPhase('awaiting_approval');
      } else {
        showError('Unexpected response from server.');
        setPhase('idle');
      }

    } catch (err) {
      stopLoadingCycle();
      spinnerNode.remove();
      showError(`Could not reach the API server.\n\nMake sure it is running:\npython src/api/main.py`);
      setPhase('idle');
    }
  },

  // ── Approve / Decline ────────────────────────────────────────────────────
  async approve(approved) {
    if (state.phase !== 'awaiting_approval') return;

    document.querySelectorAll('.approve-btn').forEach(b => b.disabled = true);

    const spinnerNode = addNode(`
      <div class="status-row">
        <div class="spinner"></div>
        <span>${approved ? 'Logging wear...' : 'Got it, skipping...'}</span>
      </div>
    `);

    try {
      const res = await fetch(`${API}/approve`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ session_id: state.sessionId, approved }),
      });

      spinnerNode.remove();

      if (!res.ok) {
        const err = await res.json();
        showError(err.detail || 'Approval error');
      } else if (approved) {
        addNode(`
          <div class="result-banner success">
            Outfit logged to your wear history. Have a great time!
          </div>
        `);
      } else {
        addNode(`
          <div class="result-banner declined">
            No problem - try a different occasion or context.
          </div>
        `);
      }
    } catch {
      spinnerNode.remove();
      showError('Could not reach the API server.');
    }

    setPhase('idle');
    state.sessionId = null;
  },

  // ── Reset memory ──────────────────────────────────────────────────────────
  async resetMemory() {
    try {
      await fetch(`${API}/memory/${USER_ID}`, { method: 'DELETE' });
      addNode(`<div class="result-banner declined">Memory cleared for ${USER_ID}.</div>`);
    } catch {
      showError('Could not reach the API server.');
    }
  },
};

// ── Render outfit card ─────────────────────────────────────────────────────
function renderOutfitCard(outfit, nonFatalError) {
  const items      = outfit.items || [];
  const readyClass = outfit.ready_to_wear ? 'yes' : 'no';
  const readyLabel = outfit.ready_to_wear ? 'Ready to wear' : 'Review needed';

  const itemsHtml = items.map(item => {
    const cat = (item.category || '').toLowerCase();
    return `
      <div class="outfit-item" data-category="${cat}">
        ${colorDot(item.color)}
        <div class="item-body">
          <div class="item-name">${item.name}</div>
          <div class="item-meta">
            <span class="category-badge">${item.category || ''}</span>
            <div class="formality-dots">${formalityDots(item.formality)}</div>
          </div>
          <div class="item-reason">${item.reason || ''}</div>
        </div>
      </div>
    `;
  }).join('');

  const noteLines = [];
  if (outfit.weather_summary && outfit.weather_summary !== 'weather not available') {
    noteLines.push(`<div class="note-line"><span class="note-icon">&#x1F324;</span><span>${outfit.weather_summary}</span></div>`);
  }
  if (outfit.occasion_notes) {
    noteLines.push(`<div class="note-line warn"><span class="note-icon">&#x26A0;</span><span>${outfit.occasion_notes}</span></div>`);
  }
  if (outfit.gap_message && outfit.gap_message !== 'Outfit is complete.') {
    noteLines.push(`<div class="note-line warn"><span class="note-icon">&#x1F50D;</span><span>${outfit.gap_message}</span></div>`);
  }
  if (nonFatalError) {
    noteLines.push(`<div class="note-line warn"><span class="note-icon">&#x26A1;</span><span>Graph warning: ${nonFatalError.split('\n')[0]}</span></div>`);
  }
  const notesHtml = noteLines.length
    ? `<div class="outfit-notes">${noteLines.join('')}</div>`
    : '';

  const html = `
    <div class="outfit-card">
      <div class="outfit-header">
        <div class="outfit-header-left">
          <div class="outfit-title">${(outfit.occasion || '').replace(/-/g, ' ')} outfit</div>
          <div class="outfit-meta">
            ${outfit.color_palette && outfit.color_palette !== 'unknown'
              ? `<span class="palette-badge">${outfit.color_palette}</span>` : ''}
            <span>${items.length} piece${items.length !== 1 ? 's' : ''}</span>
          </div>
        </div>
        <span class="ready-badge ${readyClass}">${readyLabel}</span>
      </div>

      <div class="outfit-items">${itemsHtml}</div>

      ${notesHtml}

      <div class="approval-bar">
        <button class="approve-btn yes" onclick="app.approve(true)">Wearing this</button>
        <button class="approve-btn no"  onclick="app.approve(false)">Show me alternatives</button>
      </div>
    </div>
  `;

  addNode(html);
}

// ── Error display ──────────────────────────────────────────────────────────
function showError(msg) {
  addNode(`<div class="result-banner error">${msg}</div>`);
}

// ── Init ───────────────────────────────────────────────────────────────────
setPhase('idle');
