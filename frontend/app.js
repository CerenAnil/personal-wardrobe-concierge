/**
 * Wardrobe Concierge — frontend state machine
 *
 * States: idle -> processing -> awaiting_approval -> idle
 *
 * idle:               form is enabled, user fills in occasion + details
 * processing:         spinner shown, waiting for POST /outfit
 * awaiting_approval:  outfit card shown, waiting for "Wearing this" / "Show me alternatives"
 * idle (after):       result banner shown, form re-enabled
 */

const API = 'http://localhost:8000';
const USER_ID = 'user_001';

// ── State ──────────────────────────────────────────────────────────────────
let state = {
  phase:      'idle',      // idle | processing | awaiting_approval
  occasion:   '',
  sessionId:  null,
  rawQuery:   '',
};

// ── Color map for item dots ────────────────────────────────────────────────
const COLOR_MAP = {
  'white':       '#f5f5f0',
  'black':       '#1a1a1a',
  'navy':        '#1e2d5a',
  'dark indigo': '#1c2148',
  'mid blue':    '#4a6fa5',
  'light blue':  '#7bafd4',
  'grey':        '#808080',
  'charcoal':    '#2f3030',
  'light grey':  '#c0c0be',
  'camel':       '#c19a6b',
  'tan':         '#d2a679',
  'brown':       '#7b4f2e',
  'beige':       '#d4c4a8',
  'cream':       '#f5f0e8',
  'ivory':       '#fffff0',
  'olive':       '#6b6e3a',
  'dark green':  '#2d4a2d',
  'burgundy':    '#800020',
  'rust':        '#b7410e',
  'tortoiseshell': '#8b4513',
  'gold':        '#c5a028',
  'silver':      '#aaaaaa',
};

function colorDot(color) {
  const bg = COLOR_MAP[color?.toLowerCase()] || '#555';
  return `<div class="item-color-dot" style="background:${bg}" title="${color || ''}"></div>`;
}

function formalityDots(level) {
  return Array.from({ length: 5 }, (_, i) =>
    `<div class="dot ${i < level ? 'filled' : ''}"></div>`
  ).join('');
}

// ── DOM helpers ────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);
const messages = () => $('messages');

function setPhase(p) {
  state.phase = p;
  const btn = $('submitBtn');
  if (p === 'idle') {
    btn.disabled = !state.occasion;
    btn.textContent = 'Build outfit';
  } else {
    btn.disabled = true;
    btn.textContent = p === 'processing' ? 'Building...' : 'Building...';
  }
}

function hideEmpty() {
  const el = $('emptyState');
  if (el) el.style.display = 'none';
}

function addNode(html) {
  const div = document.createElement('div');
  div.innerHTML = html;
  const child = div.firstElementChild;
  messages().appendChild(child);
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

// ── Quick-fill prompts ──────────────────────────────────────────────────────
const app = {
  quickFill(query, occasion) {
    // Select the matching chip
    document.querySelectorAll('.chip').forEach(c => {
      c.classList.toggle('active', c.dataset.occasion === occasion);
    });
    state.occasion = occasion;
    state.rawQuery = query;
    $('submitBtn').disabled = false;
    // Trigger submit immediately
    this.submit(query);
  },

  // ── Submit ─────────────────────────────────────────────────────────────
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

    state.rawQuery = rawQuery;
    hideEmpty();
    setPhase('processing');

    // User bubble
    addNode(`<div class="query-bubble">${rawQuery}</div>`);

    // Spinner
    const spinnerNode = addNode(`
      <div class="status-row">
        <div class="spinner"></div>
        <span>Searching your wardrobe...</span>
      </div>
    `);

    try {
      const res = await fetch(`${API}/outfit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          raw_query:  rawQuery,
          user_id:    USER_ID,
          city:       city || null,
          dress_code: dressCode || null,
          who_with:   whoWith || null,
        }),
      });

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
      spinnerNode.remove();
      showError(`Could not reach the API server.\n\nMake sure it is running:\npython src/api/main.py`);
      setPhase('idle');
    }
  },

  // ── Approve / Decline ──────────────────────────────────────────────────
  async approve(approved) {
    if (state.phase !== 'awaiting_approval') return;

    // Disable both buttons immediately
    document.querySelectorAll('.approve-btn').forEach(b => b.disabled = true);

    const spinnerNode = addNode(`
      <div class="status-row">
        <div class="spinner"></div>
        <span>${approved ? 'Logging wear...' : 'Got it, skipping...'}</span>
      </div>
    `);

    try {
      const res = await fetch(`${API}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: state.sessionId, approved }),
      });

      spinnerNode.remove();

      if (!res.ok) {
        const err = await res.json();
        showError(err.detail || 'Approval error');
      } else if (approved) {
        addNode(`
          <div class="result-banner success">
            <span>Outfit logged to your wear history. Have a great time!</span>
          </div>
        `);
      } else {
        addNode(`
          <div class="result-banner declined">
            <span>No problem - try a different occasion or context.</span>
          </div>
        `);
      }
    } catch (err) {
      spinnerNode.remove();
      showError('Could not reach the API server.');
    }

    setPhase('idle');
    state.sessionId = null;
  },

  // ── Reset memory ───────────────────────────────────────────────────────
  async resetMemory() {
    try {
      await fetch(`${API}/memory/${USER_ID}`, { method: 'DELETE' });
      addNode(`<div class="result-banner declined"><span>Memory cleared for ${USER_ID}.</span></div>`);
    } catch {
      showError('Could not reach the API server.');
    }
  },
};

// ── Render outfit card ─────────────────────────────────────────────────────
function renderOutfitCard(outfit, nonFatalError) {
  const items = outfit.items || [];
  const readyClass = outfit.ready_to_wear ? 'yes' : 'no';
  const readyLabel = outfit.ready_to_wear ? 'Ready to wear' : 'Review needed';

  // Items HTML
  const itemsHtml = items.map(item => {
    const lastWorn = item.last_worn
      ? `<span class="last-worn">last worn ${item.last_worn}</span>`
      : `<span class="last-worn">never worn</span>`;

    return `
      <div class="outfit-item">
        ${colorDot(item.color)}
        <div class="item-body">
          <div class="item-name">${item.name}</div>
          <div class="item-meta">
            <span class="category-badge">${item.category}</span>
            <div class="formality-dots">${formalityDots(item.formality)}</div>
            ${lastWorn}
          </div>
          <div class="item-reason">${item.reason || ''}</div>
        </div>
      </div>
    `;
  }).join('');

  // Notes section
  let notesHtml = '';
  const noteLines = [];
  if (outfit.weather_summary && outfit.weather_summary !== 'weather not available') {
    noteLines.push(`<div class="note-line"><span class="note-icon">🌤</span><span>${outfit.weather_summary}</span></div>`);
  }
  if (outfit.occasion_notes) {
    noteLines.push(`<div class="note-line warn"><span class="note-icon">⚠</span><span>${outfit.occasion_notes}</span></div>`);
  }
  if (outfit.gap_message && outfit.gap_message !== 'Outfit is complete.') {
    noteLines.push(`<div class="note-line warn"><span class="note-icon">🔍</span><span>${outfit.gap_message}</span></div>`);
  }
  if (nonFatalError) {
    noteLines.push(`<div class="note-line warn"><span class="note-icon">⚡</span><span>Graph warning: ${nonFatalError.split('\n')[0]}</span></div>`);
  }
  if (noteLines.length) {
    notesHtml = `<div class="outfit-notes">${noteLines.join('')}</div>`;
  }

  const html = `
    <div class="outfit-card">
      <div class="outfit-header">
        <div class="outfit-header-left">
          <div class="outfit-title">${outfit.occasion?.replace('-', ' ')} outfit</div>
          <div class="outfit-meta">
            ${outfit.color_palette && outfit.color_palette !== 'unknown'
              ? `<span class="palette-badge">🎨 ${outfit.color_palette}</span>` : ''}
            <span>${items.length} pieces</span>
          </div>
        </div>
        <span class="ready-badge ${readyClass}">${readyLabel}</span>
      </div>

      <div class="outfit-items">${itemsHtml}</div>

      ${notesHtml}

      <div class="approval-bar">
        <button class="approve-btn yes" onclick="app.approve(true)">
          Wearing this
        </button>
        <button class="approve-btn no" onclick="app.approve(false)">
          Show me alternatives
        </button>
      </div>
    </div>
  `;

  addNode(html);
}

// ── Error display ──────────────────────────────────────────────────────────
function showError(msg) {
  addNode(`<div class="result-banner error">${msg}</div>`);
}

// ── Init ──────────────────────────────────────────────────────────────────
setPhase('idle');
