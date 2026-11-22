// PhoneDeck — app do celular
'use strict';

const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const rid = () => Math.random().toString(36).slice(2, 10);
const clone = o => JSON.parse(JSON.stringify(o));
const safeColor = c => (/^#[0-9a-f]{3,8}$/i.test(c || '') ? c : '#1f2937');
const LS = {
  get(k, d) { try { const v = localStorage.getItem(k); return v === null ? d : v; } catch (e) { return d; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* modo privado */ } },
};

// ------------------------------------------------------------------ catálogos
const ACTIONS = [
  ['media', 'Mídia / volume'],
  ['player', 'Painel de música (Spotify)'],
  ['mic', 'Mutar microfone'],
  ['hotkey', 'Atalho de teclado'],
  ['clip', 'Clipe da tela (últimos segundos)'],
  ['desktop', 'Mostrar área de trabalho'],
  ['game', 'Abrir jogo instalado (Epic, EA app, Steam)'],
  ['open', 'Abrir programa, pasta ou site'],
  ['run', 'Rodar comando'],
  ['text', 'Digitar texto'],
  ['remote', 'Mouse e teclado (touchpad)'],
  ['stat', 'Mostrador ao vivo (GPU, CPU…)'],
  ['page', 'Ir para outra página'],
  ['open_clips', 'Abrir pasta de clipes'],
  ['lock', 'Bloquear o PC'],
  ['none', 'Nada (espaço vazio)'],
];
const MEDIA = [
  ['playpause', 'Play / Pause', 'play-pause'], ['next', 'Próxima', 'next'], ['prev', 'Anterior', 'prev'],
  ['stop', 'Parar', 'stop'], ['volup', 'Vol +', 'vol-up'], ['voldown', 'Vol −', 'vol-down'], ['mute', 'Mudo', 'vol-mute'],
];
const STATS = [
  ['fps', 'FPS (jogo aberto)', 'speed'],
  ['gpu', 'GPU', 'gpu'], ['gputemp', 'Temp. GPU', 'thermo'], ['vram', 'VRAM', 'chip'], ['cpu', 'CPU', 'cpu'],
  ['ram', 'RAM', 'ram'], ['volume', 'Volume', 'volume'], ['clock', 'Hora', 'clock'],
];
const SIZES = [['1x1', '1×1 — normal'], ['2x1', '2×1 — largo'], ['1x2', '1×2 — alto'], ['2x2', '2×2 — grande'],
  ['3x1', '3×1 — faixa'], ['3x2', '3×2 — painel'], ['4x1', '4×1 — faixa larga'], ['4x2', '4×2 — painel largo']];
const PLAYER_APPS = [['spotify', 'Spotify'], ['any', 'Qualquer player (o que estiver tocando)']];
const SUGGEST = { // nome e ícone sugeridos ao escolher a ação
  mic: ['Microfone', 'mic'], hotkey: ['Atalho', 'keyboard'], clip: ['Clipe', 'clip'], desktop: ['Área de trabalho', 'desktop'],
  open: ['Abrir', 'gamepad'], run: ['Comando', 'terminal'], text: ['Texto', 'type'], page: ['Página', 'grid'],
  open_clips: ['Meus clipes', 'folder'], lock: ['Bloquear PC', 'lock'], player: ['Spotify', 'music'], none: ['', ''],
  game: ['Jogo', 'gamepad'], remote: ['Mouse e teclado', 'mouse'],
};
const NOT_PINNABLE = ['stat', 'player', 'none']; // blocos grandes não cabem na faixa fixa
const MAX_PINNED = 3;
const COLORS = ['#1f2937', '#334155', '#7f1d1d', '#b91c1c', '#c2410c', '#a16207', '#4d7c0f', '#15803d',
  '#065f46', '#0e7490', '#1d4ed8', '#4338ca', '#6d28d9', '#a21caf', '#be185d', '#000000'];
const GRAPH = { gpu: 'gpu', cpu: 'cpu', ram: 'ram', gputemp: 'gputemp', vram: 'vram', fps: 'fps' };
const UNIT = { gpu: '%', cpu: '%', ram: '%', vram: '%', gputemp: '°C', fps: ' FPS' };
const MMA = { gpu: '%', cpu: '%', ram: '%', gputemp: '°', fps: '' }; // mín/méd/máx visíveis no bloco
const HIST_N = 60;   // blocos: último minuto
const HIST_MAX = 300; // tela cheia: até 5 min
const recent = (k, n = HIST_N) => (S.hist[k] || []).slice(-n);

// Temas: [id, nome, descrição, estilo da prévia, estilo dos quadradinhos]
const THEMES = [
  ['classico', 'Clássico', 'Botões coloridos e sólidos', 'background:#151923', 'solid'],
  ['minimal', 'Minimal', 'Limpo, só o ícone colorido', 'background:#16181d', 'minimal'],
  ['neon', 'Neon', 'Bordas que brilham no escuro', 'background:#05040b', 'neon'],
  ['fofo', 'Fofo', 'Tons pastel, tudo arredondado', 'background:#fff3f8', 'fofo'],
  ['glass', 'Liquid Glass', 'Vidro fosco sobre cores', 'background:radial-gradient(circle at 20% 30%,#8b5cf6,transparent 55%),radial-gradient(circle at 80% 70%,#06b6d4,transparent 55%),#0a0b1a', 'glass'],
  ['rgb', 'Gamer RGB', 'Borda arco-íris animada', 'background:#07070c', 'rgb'],
];
const SW = ['#ef4444', '#22c55e', '#3b82f6'];
function swatch(kind) {
  return SW.map(c => {
    const st = {
      solid: `background:${c}`,
      minimal: `background:#23262e;box-shadow:inset 0 0 0 7px #23262e,inset 0 0 0 11px ${c}`,
      neon: `background:transparent;border:2px solid ${c};box-shadow:0 0 8px ${c}`,
      fofo: `background:color-mix(in srgb,${c} 35%,#fff);border-radius:9px;box-shadow:0 3px 0 color-mix(in srgb,${c} 40%,#e9cfe0)`,
      glass: `background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.5);backdrop-filter:blur(6px)`,
      rgb: `background:#111;border:2px solid;border-image:linear-gradient(45deg,#ff004c,#ffe600,#00e0ff,#ff00c8) 1`,
    }[kind];
    return `<i style="${st}"></i>`;
  }).join('');
}

// ------------------------------------------------------------------ estado
const S = {
  layout: null, page: LS.get('pd_page', ''), edit: false,
  ws: null, connected: false, retry: 0, rt: 0, lastMsg: 0, offTimer: 0,
  tick: {}, pending: new Map(), token: '', hist: {},
};
for (const k of Object.values(GRAPH)) S.hist[k] = [];

(function initToken() {
  const q = new URLSearchParams(location.search).get('t');
  if (q) LS.set('pd_token', q);
  S.token = q || LS.get('pd_token', '');
})();

// ------------------------------------------------------------------ tema
const darkQuery = window.matchMedia ? matchMedia('(prefers-color-scheme: dark)') : null;
function currentTheme() {
  if (S.layout?.theme) return S.layout.theme;
  try { return JSON.parse(LS.get('pd_theme', '')) || { name: 'classico', mode: 'auto' }; } catch (e) { return { name: 'classico', mode: 'auto' }; }
}
function applyTheme() {
  const t = currentTheme();
  const dark = t.mode === 'auto' ? (darkQuery ? darkQuery.matches : true) : t.mode === 'dark';
  document.body.dataset.theme = t.name || 'classico';
  document.body.dataset.mode = dark ? 'dark' : 'light';
  LS.set('pd_theme', JSON.stringify(t));
  const bg = getComputedStyle(document.body).getPropertyValue('--bg').trim();
  const meta = $('meta[name="theme-color"]');
  if (meta && bg) meta.content = bg;
}
if (darkQuery) {
  const onChange = () => { if (currentTheme().mode === 'auto') applyTheme(); };
  if (darkQuery.addEventListener) darkQuery.addEventListener('change', onChange); else darkQuery.addListener(onChange);
}
applyTheme();

// ------------------------------------------------------------------ conexão
function connect() {
  if (S.ws && S.ws.readyState <= 1) return;
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  let ws;
  try { ws = new WebSocket(`${proto}://${location.host}/ws?t=${encodeURIComponent(S.token)}`); }
  catch (e) { scheduleReconnect(); return; }
  S.ws = ws;
  ws.onmessage = ev => {
    S.lastMsg = Date.now();
    let m; try { m = JSON.parse(ev.data); } catch (e) { return; }
    onMessage(m);
  };
  ws.onclose = ev => {
    if (S.ws !== ws) return;
    setConnected(false);
    if (ev.code === 4001) { showLogin(S.token ? 'Código incorreto.' : ''); return; }
    scheduleReconnect();
  };
}
function scheduleReconnect() {
  clearTimeout(S.rt);
  S.rt = setTimeout(connect, Math.min(4000, 400 * 2 ** S.retry++));
}
function send(obj) {
  if (S.ws && S.ws.readyState === 1) { S.ws.send(JSON.stringify(obj)); return true; }
  return false;
}
function setConnected(on) {
  S.connected = on;
  $('#conn').classList.toggle('ok', on);
  $('#fsConn').classList.toggle('hidden', on);
  clearTimeout(S.offTimer);
  if (on) {
    $('#offline').classList.add('hidden'); document.body.classList.remove('offline');
  } else {
    S.offTimer = setTimeout(() => {
      if (!S.connected && !S.loginOpen) { $('#offline').classList.remove('hidden'); document.body.classList.add('offline'); }
    }, 2500);
  }
}
// iPhone derruba a conexão quando o app vai para o fundo: reconecta ao voltar
document.addEventListener('visibilitychange', () => { if (!document.hidden && !S.connected) { S.retry = 0; connect(); } });
window.addEventListener('pageshow', () => { if (!S.connected) { S.retry = 0; connect(); } });
setInterval(() => { // conexão "zumbi"
  if (S.connected && Date.now() - S.lastMsg > 6000 && S.ws) { try { S.ws.close(); } catch (e) { /* */ } }
}, 2000);

function pushHistory(row) {
  for (const k of Object.values(GRAPH)) {
    const a = S.hist[k];
    a.push(row ? row[k] ?? null : null);
    if (a.length > HIST_MAX) a.shift();
  }
}

function onMessage(m) {
  switch (m.type) {
    case 'hello':
      S.retry = 0; setConnected(true); hideLogin();
      S.layout = m.layout;
      for (const k of Object.values(GRAPH)) S.hist[k] = [];
      (m.history || []).slice(-HIST_MAX).forEach(pushHistory);
      if (m.tick && m.tick.type) S.tick = m.tick;
      applyTheme(); render();
      break;
    case 'layout':
      S.layout = m.layout; applyTheme(); render();
      break;
    case 'tick': {
      S.tick = m;
      const g = m.gpu || {};
      pushHistory({ cpu: m.cpu, ram: m.ram, gpu: g.util, gputemp: g.temp,
        vram: g.mem_total ? Math.round(100 * g.mem_used / g.mem_total) : null, fps: (m.fps || {}).fps ?? null });
      updateLive();
      break;
    }
    case 'result':
      onResult(m);
      break;
    case 'games':
      S.games = m.items || [];
      renderPicker();
      break;
    case 'notice': // ex.: resultado da conferência do clipe
      toast(m.msg || '', m.kind === 'warn' ? 'warn' : '');
      break;
  }
}

// ------------------------------------------------------------------ login
function showLogin(err) {
  S.loginOpen = true;
  $('#offline').classList.add('hidden');
  $('#login').classList.remove('hidden');
  $('#pinErr').textContent = err || '';
  $('#pin').value = '';
}
function hideLogin() { S.loginOpen = false; $('#login').classList.add('hidden'); }
$('#pinOk').addEventListener('click', () => {
  const v = $('#pin').value.trim().toLowerCase();
  if (!v) return;
  S.token = v; LS.set('pd_token', v);
  $('#pinErr').textContent = 'Conectando…';
  if (S.ws) { const old = S.ws; S.ws = null; try { old.close(); } catch (e) { /* */ } }
  S.retry = 0; connect();
});
$('#pin').addEventListener('keydown', e => { if (e.key === 'Enter') $('#pinOk').click(); });

// ------------------------------------------------------------------ helpers
function findBtn(id) {
  for (const b of S.layout?.pinned || []) if (b.id === id) return b;
  for (const p of S.layout?.pages || []) for (const b of p.buttons) if (b.id === id) return b;
  return null;
}
// onde o botão mora: na faixa fixa ou numa página
function locate(id) {
  const pin = S.layout.pinned || [];
  const i = pin.findIndex(x => x.id === id);
  if (i >= 0) return { list: pin, i, pinned: true };
  for (const p of S.layout.pages) {
    const j = p.buttons.findIndex(x => x.id === id);
    if (j >= 0) return { list: p.buttons, i: j, pinned: false, page: p };
  }
  return null;
}
function curPage() { return S.layout.pages.find(p => p.id === S.page) || S.layout.pages[0]; }
function goPage(id) {
  if (!S.layout.pages.some(p => p.id === id)) { toast('Página não encontrada', 'err'); return; }
  S.page = id; LS.set('pd_page', id); render();
  const tab = $('#tabs .tab.on');
  if (tab && tab.scrollIntoView) tab.scrollIntoView({ block: 'nearest', inline: 'nearest' });
}
let toastTimer = 0;
function toast(msg, kind = '') {
  const t = $('#toast');
  t.textContent = msg; t.className = 'show ' + kind;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { t.className = kind; }, kind === 'warn' ? 8000 : kind === 'err' ? 3500 : 2200);
}
function flash(el, cls) {
  el.classList.remove('ok', 'err'); void el.offsetWidth; el.classList.add(cls);
  setTimeout(() => el.classList.remove(cls), 650);
}
// Vibração: Android usa navigator.vibrate; no iPhone (iOS 18+) o "switch" nativo dá um toque háptico.
const hapticLabel = (() => {
  const lab = document.createElement('label'); lab.className = 'haptic'; lab.setAttribute('aria-hidden', 'true');
  const inp = document.createElement('input'); inp.type = 'checkbox'; inp.setAttribute('switch', ''); inp.tabIndex = -1;
  lab.appendChild(inp); document.body.appendChild(lab); return lab;
})();
function haptic() {
  if (LS.get('pd_haptic', '1') !== '1') return;
  try { if (navigator.vibrate) navigator.vibrate(12); else hapticLabel.click(); } catch (e) { /* */ }
}
function sizeOf(b) {
  const [w, h] = String(b.size || '1x1').split('x').map(Number);
  return { w: w || 1, h: h || 1 };
}
function currentCols() {
  if (!S.layout) return 4;
  return Math.max(1, innerHeight >= innerWidth ? S.layout.grid.portrait : S.layout.grid.landscape);
}

// ------------------------------------------------------------------ desenho
const badge = `<span class="badge">${icon('pencil')}</span>`;

function keyHTML(b, opts = {}) {
  const a = b.action || {};
  const style = `style="--c:${safeColor(b.color)}"`;
  const edit = S.edit && !opts.preview ? badge : '';
  const { w, h } = sizeOf(b);
  const cols = opts.cols || currentCols();
  const cw = Math.min(w, cols);
  const data = (opts.preview ? '' : `data-id="${esc(b.id)}" `) + `data-w="${cw}" data-h="${h}"`;
  if (a.type === 'stat') {
    const graph = !!GRAPH[a.stat];
    return `<div class="key stat${graph ? '' : ' nograph'}" ${data} ${style}>` +
      (graph ? '<div class="spark"><svg viewBox="0 0 100 100" preserveAspectRatio="none"><path class="area"/><path class="line"/></svg><span class="xh"></span><span class="now"></span></div>' : '') +
      `<div class="shead"><span class="sico">${icon(b.icon)}</span><span class="lbl">${esc(b.label)}</span><span class="sub"></span></div>` +
      `<div class="vrow"><div class="val">—</div>${MMA[a.stat] !== undefined && cw >= 2 ? '<div class="mma"></div>' : ''}</div>${edit}</div>`;
  }
  if (a.type === 'player') {
    const cls = cw >= 2 && h >= 2 ? 'pl-full' : (h === 1 && cw >= 2 ? 'pl-row' : 'pl-mini');
    return `<div class="key player ${cls}" ${data} ${style}><div class="pl-bg"></div>` +
      `<div class="pl-top"><div class="pl-art">${icon('music')}</div><div class="pl-meta">` +
      `<div class="pl-app">${icon(b.icon || 'music')}<span>${esc(b.label)}</span></div>` +
      `<div class="pl-title">—</div><div class="pl-artist"></div></div></div>` +
      `<div class="pl-prog"><i></i></div><div class="pl-ctrls">` +
      `<button class="pl-b" data-sub="shuffle" aria-label="Aleatório">${icon('shuffle')}</button>` +
      `<button class="pl-b" data-sub="prev" aria-label="Anterior">${icon('prev')}</button>` +
      `<button class="pl-b big" data-sub="playpause" aria-label="Play ou pausa">${icon('play')}</button>` +
      `<button class="pl-b" data-sub="next" aria-label="Próxima">${icon('next')}</button></div>${edit}</div>`;
  }
  if (a.type === 'none') {
    return `<div class="key empty" ${data}>${S.edit && !opts.preview ? `<div class="lbl" style="opacity:.5">vazio</div>${edit}` : ''}</div>`;
  }
  const hold = b.hold ? `<span class="holdmark" title="Segure para acionar">${icon('clock')}</span>` : '';
  return `<button class="key${opts.pin ? ' pin' : ''}" ${data} ${style}><div class="ico">${icon(b.icon)}</div>` +
    `<div class="lbl">${esc(b.label)}</div>${a.type === 'clip' ? '<span class="dot"></span>' : ''}${hold}${edit}</button>`;
}

function render() {
  if (!S.layout) return;
  const page = curPage();
  S.page = page.id;
  document.body.classList.toggle('nolabels', !S.layout.showLabels);
  document.body.classList.toggle('editing', S.edit);
  $('#editBtn').innerHTML = icon(S.edit ? 'check' : 'pencil');
  $('#editBtn').classList.toggle('on', S.edit);
  $('#setBtn').innerHTML = icon('sliders');
  $('#fsBtn').innerHTML = icon('expand');
  $('#fsBtn').classList.toggle('hidden', S.edit);
  $('#setBtn').classList.toggle('hidden', !S.edit);
  $('#tabs').innerHTML = S.layout.pages.map(p =>
    `<button class="tab${p.id === page.id ? ' on' : ''}" data-page="${esc(p.id)}">${esc(p.name)}</button>`).join('') +
    (S.edit ? '<button class="tab add" data-newpage="1" title="Nova página">＋</button>' : '');
  renderPinned();
  S.renderCols = currentCols();
  $('#deck').innerHTML = page.buttons.map(b => keyHTML(b)).join('') +
    (S.edit ? `<button class="key add" data-add="1" data-w="1" data-h="1"><div class="ico">${icon('plus')}</div><div class="lbl">Adicionar</div></button>` : '');
  sizeDeck();
  updateLive();
}

// Botões fixos: embaixo das abas (em pé), na coluna da esquerda (deitado) e no topo da tela cheia
function pinnedHTML(inFocus) {
  const pins = (S.layout.pinned || []).filter(b => !NOT_PINNABLE.includes((b.action || {}).type));
  if (!pins.length) return S.edit && !inFocus ? '<span class="pin-hint">Botões fixos: edite um botão › <b>Fixar no topo</b></span>' : '';
  return pins.map(b => keyHTML(b, { pin: true, cols: 1, preview: inFocus && S.edit })).join('');
}
function renderPinned() {
  $('#pinned').innerHTML = pinnedHTML(false);
  if (FS.open) $('#fsPinned').innerHTML = pinnedHTML(true);
}

// Simula o encaixe "denso" da grade para saber quantas linhas vão existir
function packedRows(items, cols) {
  const grid = [];
  let rows = 0;
  const free = (r, c, w, h) => {
    if (c + w > cols) return false;
    for (let y = r; y < r + h; y++) for (let x = c; x < c + w; x++) if (grid[y] && grid[y][x]) return false;
    return true;
  };
  for (const it of items) {
    const w = Math.min(it.w, cols), h = it.h;
    let done = false;
    for (let r = 0; !done; r++) {
      for (let c = 0; c < cols && !done; c++) {
        if (free(r, c, w, h)) {
          for (let y = r; y < r + h; y++) { grid[y] = grid[y] || []; for (let x = c; x < c + w; x++) grid[y][x] = 1; }
          rows = Math.max(rows, r + h); done = true;
        }
      }
    }
  }
  return Math.max(1, rows);
}

function sizeDeck() {
  if (!S.layout) return;
  const deck = $('#deck');
  const cols = currentCols();
  if (cols !== S.renderCols) { render(); return; } // girou o celular: redesenha (tamanhos dos painéis mudam)
  const kids = [...deck.children];
  for (const el of kids) {
    const w = Math.min(Number(el.dataset.w) || 1, cols), h = Number(el.dataset.h) || 1;
    el.style.gridColumn = w > 1 ? `span ${w}` : '';
    el.style.gridRow = h > 1 ? `span ${h}` : '';
  }
  const rows = packedRows(kids.map(el => ({ w: Number(el.dataset.w) || 1, h: Number(el.dataset.h) || 1 })), cols);
  const cs = getComputedStyle(deck);
  const W = deck.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
  const H = deck.clientHeight - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom);
  const gap = Math.round(Math.max(10, Math.min(18, Math.min(W, H) * 0.03))); // espaço maior = menos toque no vizinho
  const byW = (W - gap * (cols - 1)) / cols;
  const byH = (H - gap * (rows - 1)) / rows;
  let size = Math.floor(Math.min(byW, byH));
  let scroll = false;
  if (size < 64) { size = Math.floor(Math.min(byW, 64)); scroll = true; } // muitos botões: rola
  size = Math.min(size, 190);
  deck.style.setProperty('--cols', cols);
  deck.style.setProperty('--size', size + 'px');
  deck.style.setProperty('--gap', gap + 'px');
  deck.classList.toggle('scroll', scroll);
}
window.addEventListener('resize', () => requestAnimationFrame(sizeDeck));
window.addEventListener('orientationchange', () => setTimeout(sizeDeck, 250));

// ------------------------------------------------------------------ dados ao vivo
function statValue(stat, t) {
  const g = t.gpu || {};
  const a = t.audio || {};
  const pct = v => (typeof v === 'number' ? Math.max(0, Math.min(100, v)) : null);
  const avg = k => { const v = recent(k).filter(x => typeof x === 'number'); return v.length ? Math.round(v.reduce((s, x) => s + x, 0) / v.length) : null; };
  switch (stat) {
    case 'gpu': {
      if (g.util == null) return { html: '—', sub: t.gpu === null ? 'GPU não detectada' : '' };
      const bits = [];
      if (g.temp != null) bits.push(`${g.temp}°C`);
      if (g.mem_used != null) bits.push(`${g.mem_used}/${g.mem_total} GB`);
      return { html: `${g.util}<small>%</small>`, pct: pct(g.util), hot: g.util >= 95, sub: bits.join(' · ') || `méd. 1 min ${avg('gpu')}%` };
    }
    case 'fps': {
      const f = t.fps || {};
      if (f.fps != null) {
        return { html: `${f.fps}<small> FPS</small>`, pct: null,
          sub: [f.app, f.ms != null ? `${String(f.ms).replace('.', ',')} ms` : ''].filter(Boolean).join(' · ') };
      }
      const why = { no_exe: 'falta o PresentMon (veja no PC)', no_permission: 'falta liberar no PC', starting: 'iniciando…',
        error: 'erro no PresentMon', off: 'liga com o celular conectado' }[f.status];
      return { html: '—', sub: f.status === 'ok' ? 'abra um jogo' : (why || 'aguardando') };
    }
    case 'gputemp': return g.temp != null ? { html: `${g.temp}<small>°C</small>`, pct: pct(g.temp), hot: g.temp >= 83, sub: 'temperatura da GPU' } : { html: '—', sub: 'só placas NVIDIA' };
    case 'vram': return g.mem_used != null ? { html: `${g.mem_used}<small>/${g.mem_total} GB</small>`, pct: pct(100 * g.mem_used / g.mem_total), hot: g.mem_used / g.mem_total > 0.95, sub: 'memória de vídeo' } : { html: '—', sub: 'só placas NVIDIA' };
    case 'cpu': return t.cpu != null ? { html: `${t.cpu}<small>%</small>`, pct: pct(t.cpu), hot: t.cpu >= 95, sub: `méd. 1 min ${avg('cpu') ?? '—'}%` } : { html: '—' };
    case 'ram': return t.ram != null ? { html: `${t.ram}<small>%</small>`, pct: pct(t.ram), hot: t.ram >= 92, sub: t.ram_used != null ? `${t.ram_used}/${t.ram_total} GB` : '' } : { html: '—' };
    case 'volume':
      if (a.volume == null) return { html: '—' };
      return a.spk_muted ? { html: 'mudo', pct: 0, hot: true, sub: 'som do PC' } : { html: `${a.volume}<small>%</small>`, pct: pct(a.volume), sub: 'som do PC' };
    case 'clock': {
      const d = new Date();
      return { html: `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`, pct: null,
        sub: d.toLocaleDateString('pt-BR', { weekday: 'short', day: 'numeric', month: 'short' }) };
    }
  }
  return { html: '—' };
}

const hotIco = `<span class="hot-ico">${icon('warn')}</span>`;

// mín / média / máx do último minuto (ignora segundos sem dado e, no FPS, os zeros)
function histStats(key, n = HIST_N) {
  const v = recent(key, n).filter(x => typeof x === 'number' && (key !== 'fps' || x > 0));
  if (v.length < 2) return null;
  return { min: Math.min(...v), max: Math.max(...v), avg: Math.round(v.reduce((s, x) => s + x, 0) / v.length) };
}

function drawSpark(el, key) {
  const box = el.querySelector('.spark');
  if (!box) return;
  const raw = recent(key);
  let last = null;
  const vals = raw.map(v => (typeof v === 'number' ? (last = v) : last)).filter(v => v != null);
  if (vals.length < 2) { box.style.visibility = 'hidden'; return; }
  box.style.visibility = 'visible';
  const step = 100 / (HIST_N - 1);
  const off = HIST_N - vals.length;
  const top = key === 'fps' ? Math.max(60, Math.ceil(Math.max(...vals) * 1.1 / 30) * 30) : 100; // FPS: escala automática
  const y = v => 96 - Math.max(0, Math.min(top, v)) / top * 90;
  let line = '';
  vals.forEach((v, i) => { line += `${i ? 'L' : 'M'}${((off + i) * step).toFixed(2)},${y(v).toFixed(2)}`; });
  box.querySelector('.line').setAttribute('d', line);
  box.querySelector('.area').setAttribute('d', `${line}L100,100L${(off * step).toFixed(2)},100Z`);
  box.querySelector('.now').style.top = `${y(vals[vals.length - 1])}%`;
}

function updateLive() {
  if (!S.layout) return;
  const t = S.tick || {};
  const au = t.audio || {};
  for (const el of $$('#deck .key[data-id], .pinned .key[data-id]')) {
    const b = findBtn(el.dataset.id);
    if (!b) continue;
    const a = b.action || {};
    if (a.type === 'stat') {
      const v = statValue(a.stat, t);
      const val = el.querySelector('.val');
      const html = v.html + (v.hot ? hotIco : '');
      if (val.innerHTML !== html) val.innerHTML = html;
      el.classList.toggle('hot', !!v.hot);
      if (!el.classList.contains('scrub')) el.querySelector('.sub').textContent = v.sub || '';
      if (GRAPH[a.stat]) drawSpark(el, GRAPH[a.stat]);
      const mma = el.querySelector('.mma');
      if (mma) {
        const st = histStats(GRAPH[a.stat]); const u = MMA[a.stat];
        const h = st ? `<span><b>máx</b>${st.max}${u}</span><span><b>méd</b>${st.avg}${u}</span><span><b>mín</b>${st.min}${u}</span>` : '';
        if (mma.innerHTML !== h) mma.innerHTML = h;
      }
    } else if (a.type === 'player') {
      updatePlayer(el, a, t);
    } else if (a.type === 'mic') {
      const muted = au.mic_muted === true;
      el.classList.toggle('alert', muted);
      const want = muted ? 'mic-off' : (b.icon || 'mic');
      if (el.dataset.ic !== want) { el.dataset.ic = want; el.querySelector('.ico').innerHTML = icon(want); }
    } else if (a.type === 'media' && a.key === 'mute') {
      el.classList.toggle('alert', au.spk_muted === true);
    } else if (a.type === 'clip') {
      const c = t.clip || {};
      const dot = el.querySelector('.dot');
      if (dot) dot.className = 'dot ' + ({ running: 'run', ready: 'run', starting: 'wait', error: 'bad' }[c.status] || '');
    }
  }
  updateFocus();
}
setInterval(() => { if (!S.connected) updateLive(); }, 15000); // relógio continua andando offline

function updatePlayer(el, a, t) {
  const key = a.app === 'any' ? 'any' : 'spotify';
  const mi = ((t.media || {})[key]) || {};
  const set = (sel, txt) => { const n = el.querySelector(sel); if (n && n.textContent !== txt) n.textContent = txt; };
  if (!mi.present) {
    set('.pl-title', key === 'spotify' ? 'Spotify fechado' : 'Nada tocando');
    set('.pl-artist', key === 'spotify' ? 'Abra o Spotify no PC' : 'Dê play em alguma música');
  } else {
    set('.pl-title', mi.title || '—');
    set('.pl-artist', mi.artist || '');
  }
  const art = mi.present && mi.art ? mi.art : '';
  if (el.dataset.art !== art) {
    el.dataset.art = art;
    const box = el.querySelector('.pl-art');
    const bg = el.querySelector('.pl-bg');
    if (art) {
      const url = `art/${key}?v=${encodeURIComponent(art)}&t=${encodeURIComponent(S.token)}`;
      box.innerHTML = `<img alt="" src="${url}">`;
      bg.style.backgroundImage = `url("${url}")`;
    } else {
      box.innerHTML = icon('music');
      bg.style.backgroundImage = '';
    }
  }
  const playing = mi.status === 'playing';
  const pp = el.querySelector('[data-sub="playpause"]');
  if (pp && pp.dataset.st !== String(playing)) { pp.dataset.st = String(playing); pp.innerHTML = icon(playing ? 'pause' : 'play'); }
  const sh = el.querySelector('[data-sub="shuffle"]');
  if (sh) sh.classList.toggle('on', mi.shuffle === true);
  const bar = el.querySelector('.pl-prog i');
  if (bar) bar.style.width = mi.duration ? `${Math.min(100, 100 * (mi.position || 0) / mi.duration)}%` : '0%';
  const tm = el.querySelector('.pl-times');
  if (tm) {
    tm.children[0].textContent = mi.present && mi.duration ? fmtTime(mi.position) : '';
    tm.children[1].textContent = mi.present && mi.duration ? fmtTime(mi.duration) : '';
  }
}
function fmtTime(sec) {
  const v = Math.max(0, Math.round(Number(sec) || 0));
  return `${Math.floor(v / 60)}:${String(v % 60).padStart(2, '0')}`;
}

// ------------------------------------------------------------------ toques
// Toque seguro:
//  - por padrão o botão só aciona quando você SOLTA o dedo em cima dele;
//    encostou no botão errado? arraste o dedo para fora antes de soltar = cancelado
//  - botões com "Segurar para acionar" precisam ficar apertados ~0,6 s
//  - enquanto um dedo aperta um botão, outros toques são ignorados (evita a palma da mão)
const HOLD_MS = 600;
const TAP = { cur: null };
const tapMode = () => LS.get('pd_tap', 'release');

function onKeyDown(e) {
  if (S.edit || (e.pointerType === 'mouse' && e.button !== 0)) return;
  const el = e.target.closest('.key[data-id]');
  if (!el) return;
  let target = el, sub = null, focus = null;
  if (el.classList.contains('player')) {
    sub = e.target.closest('[data-sub]');
    if (sub) target = sub; else focus = 'music'; // fora dos botões: abre em tela cheia
  } else if (el.classList.contains('stat')) {
    const st = (findBtn(el.dataset.id)?.action || {}).stat;
    if (!GRAPH[st]) return; // hora e volume não abrem
    focus = st;
  }
  if (TAP.cur) return; // já tem um dedo em outro botão
  const b = findBtn(el.dataset.id);
  if (!b || (b.action || {}).type === 'none') return;
  e.preventDefault();
  const t = { el, target, sub, b, focus, pid: e.pointerId, hold: !!b.hold && !sub && !focus, done: false };
  TAP.cur = t;
  try { target.setPointerCapture(e.pointerId); } catch (err) { /* */ }
  target.classList.add('pressed');
  if (t.hold) startHold(t);
  else if (tapMode() === 'down' && !focus) fireTap(t);
}
$('#deck').addEventListener('pointerdown', onKeyDown);
$('#pinned').addEventListener('pointerdown', onKeyDown);
$('#fsPinned').addEventListener('pointerdown', onKeyDown);
$('#pinned').addEventListener('click', e => {
  if (!S.edit) return;
  const el = e.target.closest('.key[data-id]');
  if (el) openEditor(el.dataset.id);
});
$('#pinned').addEventListener('contextmenu', e => e.preventDefault());
function insideTarget(t, e) {
  const r = t.target.getBoundingClientRect(), m = 14; // tolerância de 14 px em volta do botão
  return e.clientX >= r.left - m && e.clientX <= r.right + m && e.clientY >= r.top - m && e.clientY <= r.bottom + m;
}
function endTap(t, cancelled) {
  clearTimeout(t.timer);
  t.el.classList.remove('holding');
  if (t.fill) t.fill.remove();
  setTimeout(() => t.target.classList.remove('pressed'), cancelled ? 0 : 120);
  if (TAP.cur === t) TAP.cur = null;
}
function fireTap(t) {
  if (t.done) return;
  t.done = true;
  if (t.focus) { haptic(); openFocus(t.focus, t.b.action.app === 'any' ? 'any' : (t.focus === 'music' ? 'spotify' : null)); }
  else if (t.sub) pressSub(t.el, t.sub); else press(t.el);
}
function startHold(t) {
  const fill = document.createElement('span');
  fill.className = 'hold-fill';
  t.el.appendChild(fill); t.fill = fill;
  void fill.offsetWidth; // começa a animação do zero
  t.el.classList.add('holding');
  t.timer = setTimeout(() => { fireTap(t); endTap(t, false); }, HOLD_MS);
}
document.addEventListener('pointermove', e => {
  const t = TAP.cur;
  if (!t || e.pointerId !== t.pid || t.done) return;
  if (!insideTarget(t, e)) endTap(t, true); // saiu do botão: cancela
});
document.addEventListener('pointerup', e => {
  const t = TAP.cur;
  if (!t || e.pointerId !== t.pid) return;
  if (!t.done) {
    if (t.hold) toast('Segure o botão para acionar');
    else if (insideTarget(t, e)) fireTap(t);
  }
  endTap(t, !t.done);
});
document.addEventListener('pointercancel', e => { const t = TAP.cur; if (t && e.pointerId === t.pid) endTap(t, true); });

$('#deck').addEventListener('click', e => {
  if (!S.edit || Date.now() - (S.swipeAt || 0) < 400) return;
  const el = e.target.closest('.key');
  if (!el) return;
  if (el.dataset.add) addButton();
  else if (el.dataset.id) openEditor(el.dataset.id);
});
// Mouse no PC: passe o cursor sobre o gráfico para ler um ponto
$('#deck').addEventListener('pointermove', e => {
  if (e.pointerType !== 'mouse') return;
  const el = e.target.closest('.key.stat');
  $$('#deck .key.stat.scrub').forEach(x => { if (x !== el) endScrub(x); });
  if (!el || el.classList.contains('nograph')) return;
  const b = findBtn(el.dataset.id); if (!b) return;
  const key = GRAPH[b.action.stat]; const box = el.querySelector('.spark'); if (!key || !box) return;
  const r = box.getBoundingClientRect();
  const f = Math.max(0, Math.min(1, (e.clientX - r.left) / r.width));
  const idx = Math.round(f * (HIST_N - 1));
  const arr = recent(key); const i = idx - (HIST_N - arr.length);
  const v = i >= 0 ? arr[i] : null;
  el.classList.add('scrub');
  box.querySelector('.xh').style.left = `${(idx / (HIST_N - 1)) * 100}%`;
  const ago = HIST_N - 1 - idx;
  const unit = UNIT[b.action.stat] || '%';
  el.querySelector('.sub').textContent = v == null ? 'sem dado' : `${ago ? `há ${ago} s` : 'agora'}: ${v}${unit}`;
});
$('#deck').addEventListener('pointerleave', () => $$('#deck .key.stat.scrub').forEach(endScrub));
function endScrub(el) { el.classList.remove('scrub'); updateLive(); }
$('#deck').addEventListener('contextmenu', e => e.preventDefault());
document.addEventListener('gesturestart', e => e.preventDefault()); // sem zoom de pinça

function press(el) {
  const b = findBtn(el.dataset.id);
  if (!b) return;
  const a = b.action || {};
  if (a.type === 'none') return;
  haptic();
  el.classList.add('pressed');
  setTimeout(() => el.classList.remove('pressed'), 140);
  if (a.type === 'page') { if (FS.open) closeFocus(); goPage(a.page); return; }
  if (a.type === 'remote') { openRemote(); return; }
  if (!S.connected) { flash(el, 'err'); toast('Sem conexão com o PC', 'err'); return; }
  S.pending.set(b.id, el);
  send({ type: 'press', id: b.id });
  if (a.type === 'clip' && S.tick.clip?.mode === 'ffmpeg') toast('Salvando clipe…');
}

function pressSub(el, btn) {
  haptic();
  btn.classList.add('pressed');
  setTimeout(() => btn.classList.remove('pressed'), 140);
  if (!S.connected) { flash(el, 'err'); toast('Sem conexão com o PC', 'err'); return; }
  S.pending.set(el.dataset.id, el);
  send({ type: 'press', id: el.dataset.id, sub: btn.dataset.sub });
  if (btn.dataset.sub === 'playpause') { // resposta instantânea na tela
    const playing = btn.dataset.st === 'true';
    btn.dataset.st = String(!playing); btn.innerHTML = icon(playing ? 'play' : 'pause');
  }
}

function onResult(m) {
  if (m.id === '_save') { if (!m.ok) toast(m.msg, 'err'); return; }
  let el = S.pending.get(m.id);
  S.pending.delete(m.id);
  if (!el || !el.isConnected) el = $(`.key[data-id="${CSS.escape(m.id)}"]`);
  if (el && !(m.ok && m.sub)) flash(el, m.ok ? 'ok' : 'err');
  if (m.msg) toast(m.msg, m.ok ? '' : 'err');
}

// ------------------------------------------------------------------ edição
$('#editBtn').addEventListener('click', () => { S.edit = !S.edit; closeSheet(); render(); });
$('#setBtn').addEventListener('click', () => openSettings());
$('#fsBtn').addEventListener('click', () => openFocus(null));
$('#tabs').addEventListener('click', e => {
  const t = e.target.closest('.tab');
  if (!t) return;
  if (t.dataset.newpage) return newPage();
  if (S.edit && t.dataset.page === S.page) return openPageEditor();
  goPage(t.dataset.page);
});

function persist() {
  if (!send({ type: 'save_layout', layout: S.layout })) toast('Sem conexão: a alteração não foi salva no PC', 'err');
}

function openSheet(html) {
  $('#sheetCard').innerHTML = html;
  $('#sheet').classList.remove('hidden');
  $('#sheetCard').scrollTop = 0;
}
function closeSheet() { $('#sheet').classList.add('hidden'); $('#sheetCard').innerHTML = ''; S.draft = null; S.pickerOpen = false; }
$('#sheet').addEventListener('click', e => { if (e.target.id === 'sheet') closeSheet(); });
document.addEventListener('keydown', e => {
  if (S.capturing) return;
  if (RM.open) { rmHardwareKey(e); return; }
  if (FS.open) {
    if (e.key === 'Escape') closeFocus();
    else if (e.key === 'ArrowLeft') fsGo(FS.idx - 1);
    else if (e.key === 'ArrowRight') fsGo(FS.idx + 1);
    return;
  }
  if (e.key === 'Escape') { closeSheet(); return; }
  const typing = /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement?.tagName || '');
  if (!typing && $('#sheet').classList.contains('hidden') && (e.key === 'ArrowLeft' || e.key === 'ArrowRight')) swipePage(e.key === 'ArrowRight' ? 1 : -1);
});
const closeIcon = () => icon('plus').replace('<svg', '<svg style="rotate:45deg"');

function addButton() {
  const b = { id: rid(), label: 'Novo botão', icon: 'star', color: '#334155', size: '1x1', action: { type: 'hotkey', keys: '' } };
  openEditor(b.id, b);
}

function defaultsFor(type) {
  switch (type) {
    case 'media': return { type, key: 'playpause' };
    case 'player': return { type, app: 'spotify' };
    case 'game': return { type, name: '', target: '', platform: '' };
    case 'hotkey': return { type, keys: '' };
    case 'clip': return { type, seconds: 15 };
    case 'open': return { type, target: '', args: '' };
    case 'run': return { type, command: '' };
    case 'text': return { type, text: '' };
    case 'stat': return { type, stat: 'gpu' };
    case 'page': return { type, page: (S.layout.pages.find(p => p.id !== S.page) || S.layout.pages[0]).id };
    default: return { type };
  }
}
function suggestion(a) {
  if (a.type === 'media') { const m = MEDIA.find(x => x[0] === a.key); return m ? [m[1], m[2]] : ['Mídia', 'music']; }
  if (a.type === 'stat') { const m = STATS.find(x => x[0] === a.stat); return m ? [m[1], m[2]] : ['Mostrador', 'chart']; }
  if (a.type === 'page') { const p = S.layout.pages.find(x => x.id === a.page); return [p ? p.name : 'Página', 'grid']; }
  if (a.type === 'player') return a.app === 'any' ? ['Tocando agora', 'music'] : ['Spotify', 'music'];
  if (a.type === 'game') return [a.name || 'Jogo', 'gamepad'];
  return SUGGEST[a.type] || ['', ''];
}
const SIZE_FOR = { player: '3x2', stat: '2x1' };

function openEditor(id, fresh) {
  const orig = fresh || findBtn(id);
  if (!orig) return;
  const d = clone(orig);
  d.size = d.size || '1x1';
  const loc = fresh ? null : locate(id);
  S.draft = { b: d, isNew: !!fresh, auto: suggestion(d.action || {}), pin: !!loc?.pinned };
  const opt = (list, val) => list.map(([v, l]) => `<option value="${esc(v)}"${v === val ? ' selected' : ''}>${esc(l)}</option>`).join('');
  openSheet(`
    <div class="sheet-head">
      <div class="preview" id="pv"></div>
      <h3>${fresh ? 'Novo botão' : 'Editar botão'}</h3>
      <button class="iconbtn" id="eClose" aria-label="Fechar">${closeIcon()}</button>
    </div>
    <div class="field"><label for="eLabel">Nome</label><input id="eLabel" maxlength="40" value="${esc(d.label)}"></div>
    <div class="field"><label for="eType">Ação</label><select id="eType">${opt(ACTIONS, d.action.type)}</select></div>
    <div id="eParams"></div>
    <div class="field" id="ePinRow"><label class="toggle"><span>${icon('pin')} Fixar no topo</span> <input type="checkbox" id="ePin" ${S.draft.pin ? 'checked' : ''}></label>
      <div class="hint">Aparece em todas as páginas, embaixo das abas, e também na tela cheia. Até ${MAX_PINNED} botões fixos.</div></div>
    <div class="field" id="eSizeRow"><label for="eSize">Tamanho</label><select id="eSize">${opt(SIZES, d.size)}</select>
      <div class="hint">Blocos maiores ocupam mais quadradinhos da grade (ótimo para gráficos e para o painel de música).</div></div>
    <div class="field" id="eHoldRow"><label class="toggle">Segurar para acionar <input type="checkbox" id="eHold" ${d.hold ? 'checked' : ''}></label>
      <div class="hint">Para botões perigosos (fechar janela, bloquear, desligar…): só aciona se ficar apertado meio segundo.</div></div>
    <div class="field"><span>Ícone</span>
      <div class="icons" id="eIcons">${PICKABLE.map(k => `<button type="button" data-ic="${k}" class="${k === d.icon ? 'on' : ''}" title="${k}">${icon(k)}</button>`).join('')}</div>
      <input id="eIconTxt" maxlength="12" placeholder="…ou digite um emoji / texto (ex.: 🎮, OBS, F1)" value="${ICONS[d.icon] ? '' : esc(d.icon)}">
    </div>
    <div class="field"><span>Cor</span>
      <div class="inline"><div class="swatches" id="eSw">${COLORS.map(c => `<button type="button" data-c="${c}" style="background:${c}" class="${c === d.color ? 'on' : ''}"></button>`).join('')}</div>
      <input type="color" id="eColor" value="${safeColor(d.color).length === 7 ? safeColor(d.color) : '#1f2937'}"></div>
      <div class="hint">Cada tema usa a cor de um jeito: fundo sólido, borda neon, tom pastel…</div>
    </div>
    ${fresh ? '' : `<div class="row">
      <button class="btn" id="eLeft">${icon('left')} Mover</button>
      <button class="btn" id="eRight">Mover ${icon('right')}</button>
      <button class="btn" id="eDup">${icon('copy')} Duplicar</button>
      <button class="btn danger" id="eDel">${icon('trash')} Excluir</button>
    </div>`}
    <div class="row end">
      <button class="btn" id="eCancel">Cancelar</button>
      <button class="btn primary" id="eSave">${icon('check')} Salvar</button>
    </div>`);
  renderParams();
  renderPreview();

  $('#eClose').onclick = $('#eCancel').onclick = closeSheet;
  $('#eLabel').oninput = e => { d.label = e.target.value; renderPreview(); };
  $('#eType').onchange = e => {
    const old = S.draft.auto;
    const oldType = d.action.type;
    d.action = defaultsFor(e.target.value);
    // tamanho sugerido para gráficos e painel de música
    if (SIZE_FOR[d.action.type] && d.size === '1x1') d.size = SIZE_FOR[d.action.type];
    else if (SIZE_FOR[oldType] && d.size === SIZE_FOR[oldType] && !SIZE_FOR[d.action.type]) d.size = '1x1';
    $('#eSize').value = d.size;
    holdRow(); pinRow();
    applySuggestion(old);
    renderParams(); renderPreview();
  };
  $('#eSize').onchange = e => { d.size = e.target.value; renderPreview(); };
  $('#eHold').onchange = e => { if (e.target.checked) d.hold = true; else delete d.hold; renderPreview(); };
  const holdRow = () => $('#eHoldRow').classList.toggle('hidden', ['stat', 'player', 'none'].includes(d.action.type));
  holdRow();
  const pinRow = () => {
    const can = !NOT_PINNABLE.includes(d.action.type);
    $('#ePinRow').classList.toggle('hidden', !can);
    $('#eSizeRow').classList.toggle('hidden', can && S.draft.pin);
  };
  pinRow();
  $('#ePin').onchange = e => {
    const others = (S.layout.pinned || []).filter(x => x.id !== d.id).length;
    if (e.target.checked && others >= MAX_PINNED) { e.target.checked = false; toast(`Já tem ${MAX_PINNED} botões fixos`, 'err'); return; }
    S.draft.pin = e.target.checked; pinRow();
  };
  $('#eIcons').onclick = e => {
    const btn = e.target.closest('button[data-ic]'); if (!btn) return;
    d.icon = btn.dataset.ic; $('#eIconTxt').value = '';
    $$('#eIcons button').forEach(x => x.classList.toggle('on', x === btn)); renderPreview();
  };
  $('#eIconTxt').oninput = e => {
    const v = e.target.value.trim();
    if (v) { d.icon = v; $$('#eIcons button').forEach(x => x.classList.remove('on')); }
    renderPreview();
  };
  $('#eSw').onclick = e => {
    const btn = e.target.closest('button[data-c]'); if (!btn) return;
    d.color = btn.dataset.c; $('#eColor').value = d.color;
    $$('#eSw button').forEach(x => x.classList.toggle('on', x === btn)); renderPreview();
  };
  $('#eColor').oninput = e => { d.color = e.target.value; $$('#eSw button').forEach(x => x.classList.remove('on')); renderPreview(); };
  $('#eSave').onclick = saveDraft;
  if (!fresh) {
    $('#eLeft').onclick = () => moveButton(-1);
    $('#eRight').onclick = () => moveButton(1);
    $('#eDup').onclick = () => {
      const loc = locate(d.id); if (!loc) return;
      if (loc.pinned && loc.list.length >= MAX_PINNED) { toast(`Já tem ${MAX_PINNED} botões fixos`, 'err'); return; }
      const copy = clone(loc.list[loc.i]); copy.id = rid();
      loc.list.splice(loc.i + 1, 0, copy); persist(); closeSheet(); render(); toast('Botão duplicado');
    };
    $('#eDel').onclick = () => {
      if (!confirm(`Excluir o botão "${d.label || 'sem nome'}"?`)) return;
      const loc = locate(d.id); if (loc) loc.list.splice(loc.i, 1);
      persist(); closeSheet(); render();
    };
  }
}

function applySuggestion(oldAuto) {
  const d = S.draft.b;
  const neu = suggestion(d.action);
  const labelIsAuto = !d.label || d.label === oldAuto[0] || d.label === 'Novo botão';
  const iconIsAuto = !d.icon || d.icon === oldAuto[1] || (S.draft.isNew && d.icon === 'star');
  if (labelIsAuto) { d.label = neu[0]; const el = $('#eLabel'); if (el) el.value = d.label; }
  if (iconIsAuto && neu[1]) {
    d.icon = neu[1];
    $$('#eIcons button').forEach(x => x.classList.toggle('on', x.dataset.ic === d.icon));
    const t = $('#eIconTxt'); if (t) t.value = '';
  }
  S.draft.auto = neu;
}

function renderPreview() {
  const d = S.draft?.b; if (!d) return;
  const { w, h } = sizeOf(d);
  const pw = Math.min(w, 3);
  const pv = $('#pv');
  pv.style.setProperty('--pw', pw);
  pv.innerHTML = keyHTML(d, { preview: true, cols: 3 });
  const k = pv.firstElementChild;
  k.style.gridColumn = `span ${pw}`; k.style.gridRow = `span ${Math.min(h, 2)}`;
  const a = d.action;
  if (a.type === 'stat') {
    const v = statValue(a.stat, S.tick || {});
    k.querySelector('.val').innerHTML = v.html;
    k.querySelector('.sub').textContent = v.sub || '';
    if (GRAPH[a.stat]) drawSpark(k, GRAPH[a.stat]);
  } else if (a.type === 'player') {
    updatePlayer(k, a, S.tick || {});
  }
}

function renderParams() {
  const d = S.draft.b; const a = d.action;
  const opt = (list, val) => list.map(([v, l]) => `<option value="${esc(v)}"${v === val ? ' selected' : ''}>${esc(l)}</option>`).join('');
  let h = '';
  switch (a.type) {
    case 'media':
      h = `<div class="field"><label>Tecla</label><select data-k="key">${opt(MEDIA, a.key)}</select></div>`; break;
    case 'player':
      h = `<div class="field"><label>Controlar</label><select data-k="app">${opt(PLAYER_APPS, a.app)}</select>
        <div class="hint">Mostra capa, música e artista, com aleatório, voltar, play/pause e próxima.
        Funciona com o Spotify do PC (e com outros players no modo "qualquer").</div></div>`; break;
    case 'hotkey':
      h = `<div class="field"><label>Atalho</label>
        <div class="inline"><input data-k="keys" placeholder="ex.: ctrl+shift+m" value="${esc(a.keys)}" autocapitalize="off" autocorrect="off" spellcheck="false">
        <button type="button" class="btn" id="eRec" title="Pressione as teclas no teclado do PC">${icon('keyboard')}</button></div>
        <div class="hint">Use <code>+</code> para combinar e <code>,</code> para uma sequência. Exemplos:
          <code>ctrl+shift+m</code> <code>alt+f10</code> <code>win+g</code> <code>ctrl+c, alt+tab, ctrl+v</code>.
          Teclas: ctrl, shift, alt, win, a–z, 0–9, f1–f24, enter, esc, tab, space, up/down/left/right, printscreen, delete…
          No PC, toque no teclado ao lado e pressione o atalho.</div></div>`; break;
    case 'clip': {
      const c = S.tick.clip || {};
      const buf = c.buffer || 30;
      const aud = c.audio || {};
      const audTxt = Object.keys(aud).length
        ? `Grava ${aud.system ? 'o som do PC' : ''}${aud.system && aud.mic ? ' e ' : ''}${aud.mic ? 'o microfone' : ''} junto.` : '';
      h = `<div class="field"><label>Segundos</label><input type="number" inputmode="numeric" min="3" max="${buf}" data-k="seconds" value="${esc(a.seconds)}">
        <div class="hint">${c.mode === 'hotkey'
          ? 'O PC está no modo <b>atalho</b>: o botão envia o atalho configurado no settings.json (ex.: Alt+F10 da NVIDIA).'
          : `O PC guarda até <b>${buf}s</b> (mude <code>buffer_seconds</code> no settings.json). ${audTxt} Os clipes vão para Vídeos\\PhoneDeck.`}</div></div>`;
      break;
    }
    case 'game': {
      const where = a.target
        ? `Escolhido na lista: <b>${esc(a.platform || 'PC')}</b>. Se o jogo mudar de lugar, o PhoneDeck procura de novo pelo nome.`
        : 'O PhoneDeck procura o jogo pelo nome no PC (Epic, EA app, Steam ou atalhos) e abre pelo launcher certo.';
      h = `<div class="field"><label>Jogo</label>
        <div class="inline"><input data-k="name" placeholder="ex.: Battlefield 6" value="${esc(a.name)}" autocapitalize="off" autocorrect="off" spellcheck="false">
        <button type="button" class="btn" id="ePick">${icon('gamepad')} Lista</button></div>
        <div class="hint">${where}</div></div><div id="gPicker"></div>`;
      break;
    }
    case 'open':
      h = `<div class="field"><button type="button" class="btn" id="ePick2">${icon('gamepad')} Escolher um jogo ou app instalado no PC</button></div>
        <div class="field"><label>O que abrir</label><input data-k="target" placeholder="programa, jogo, pasta, arquivo ou link" value="${esc(a.target)}" autocapitalize="off" autocorrect="off" spellcheck="false">
        <div class="hint">Exemplos: <code>https://twitch.tv</code> <code>steam://rungameid/2807960</code> <code>spotify:</code> <code>discord:</code>
          <code>%USERPROFILE%\\Downloads</code>. Jogos da Epic: na Epic, clique nos “…” do jogo › <i>Criar atalho</i>, e copie o link do atalho.</div></div>
        <div class="field"><label>Argumentos (opcional)</label><input data-k="args" value="${esc(a.args)}" autocapitalize="off" autocorrect="off" spellcheck="false"></div>`; break;
    case 'run':
      h = `<div class="field"><label>Comando (cmd do Windows)</label><textarea data-k="command" autocapitalize="off" autocorrect="off" spellcheck="false" placeholder="ex.: shutdown /s /t 60">${esc(a.command)}</textarea>
        <div class="hint">Roda escondido, sem janela. Ex.: <code>shutdown /s /t 60</code> (desligar em 1 min).</div></div>`; break;
    case 'text':
      h = `<div class="field"><label>Texto a digitar</label><textarea data-k="text">${esc(a.text)}</textarea>
        <div class="hint">Digita no programa que estiver em foco no PC (aceita acentos e emoji).</div></div>`; break;
    case 'stat':
      h = `<div class="field"><label>Mostrar</label><select data-k="stat">${opt(STATS, a.stat)}</select>
        <div class="hint">FPS, GPU, CPU, RAM, temperatura e VRAM mostram um gráfico do último minuto, com mín/méd/máx nos blocos largos.
        O FPS é do jogo em primeiro plano (precisa do PresentMon; toque no bloco para ver o 1% low).
        Temperatura e VRAM só aparecem em placas NVIDIA.</div></div>`; break;
    case 'page':
      h = `<div class="field"><label>Página</label><select data-k="page">${opt(S.layout.pages.map(p => [p.id, p.name]), a.page)}</select></div>`; break;
    case 'mic':
      h = '<p class="hint">Liga/desliga o microfone padrão do Windows. O botão fica vermelho quando está mutado.</p>'; break;
    case 'desktop':
      h = '<p class="hint">Mostra a área de trabalho (igual a Win+D). Toque de novo para voltar às janelas.</p>'; break;
    case 'open_clips':
      h = '<p class="hint">Abre a pasta onde os clipes são salvos.</p>'; break;
    case 'lock':
      h = '<p class="hint">Bloqueia o PC (igual a Win+L).</p>'; break;
    case 'none':
      h = '<p class="hint">Deixa um espaço vazio na grade, útil para organizar.</p>'; break;
  }
  $('#eParams').innerHTML = h;
  $$('#eParams [data-k]').forEach(inp => {
    const ev = inp.tagName === 'SELECT' ? 'change' : 'input';
    inp.addEventListener(ev, () => {
      const old = suggestion(a);
      a[inp.dataset.k] = inp.type === 'number' ? Number(inp.value) : inp.value;
      if (a.type === 'game' && inp.dataset.k === 'name') { a.target = ''; a.platform = ''; applySuggestion(old); }
      if (['key', 'stat', 'page', 'app'].includes(inp.dataset.k)) applySuggestion(old);
      renderPreview();
    });
  });
  const rec = $('#eRec');
  if (rec) rec.onclick = () => captureHotkey(rec);
  const pick = $('#ePick');
  if (pick) pick.onclick = () => openPicker();
  const pick2 = $('#ePick2');
  if (pick2) pick2.onclick = () => {
    const old = S.draft.auto;
    S.draft.b.action = defaultsFor('game');
    $('#eType').value = 'game';
    applySuggestion(old);
    renderParams(); renderPreview(); openPicker();
  };
}

// Lista de jogos/apps instalados no PC (vem do servidor)
const PLAT_LABEL = { 'Epic Games': 'Epic Games', 'EA app': 'EA app', Steam: 'Steam', Atalho: 'Atalhos do Windows' };
function openPicker() {
  S.pickerOpen = true; S.pickerQ = '';
  if (!send({ type: 'list_games' })) { toast('Sem conexão com o PC', 'err'); return; }
  const box = $('#gPicker');
  if (box) box.innerHTML = '<div class="picker"><p class="hint">Procurando jogos no PC…</p></div>';
}
function renderPicker() {
  const box = $('#gPicker');
  if (!box || !S.pickerOpen || !S.draft) return;
  const q = norm(S.pickerQ || '');
  const list = (S.games || []).map((g, i) => ({ ...g, i })).filter(g => !q || norm(g.name).includes(q));
  let html = '', last = '';
  for (const g of list.slice(0, 250)) {
    if (g.platform !== last) { last = g.platform; html += `<div class="pgroup">${esc(PLAT_LABEL[g.platform] || g.platform)}</div>`; }
    html += `<button type="button" class="pitem" data-i="${g.i}"><b>${esc(g.name)}</b><small>${esc(g.platform)}</small></button>`;
  }
  if (!html) html = `<p class="hint">${(S.games || []).length ? 'Nada encontrado com esse nome.' : 'Nenhum jogo encontrado no PC.'}</p>`;
  const had = $('#gSearch');
  if (!had) {
    box.innerHTML = `<div class="picker"><input id="gSearch" placeholder="Buscar (ex.: battlefield)" autocapitalize="off" autocorrect="off" spellcheck="false"><div class="plist" id="gList"></div></div>`;
    $('#gSearch').oninput = e => { S.pickerQ = e.target.value; renderPicker(); };
    $('#gList').onclick = e => {
      const b = e.target.closest('.pitem'); if (!b) return;
      const g = S.games[Number(b.dataset.i)]; if (!g) return;
      const a = S.draft.b.action; const old = suggestion(a);
      Object.assign(a, { type: 'game', name: g.name, target: g.target, platform: g.platform });
      S.pickerOpen = false;
      applySuggestion(old); renderParams(); renderPreview();
      toast(`${g.name} (${g.platform})`);
    };
  }
  $('#gList').innerHTML = html;
}
function norm(t) {
  return String(t || '').replace(/[\u2122\u00ae\u00a9\u2120]/g, '').normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
}

// Captura um atalho pressionado no teclado (quando está editando pelo PC)
const CODE_NAMES = {
  Escape: 'esc', Enter: 'enter', NumpadEnter: 'enter', Tab: 'tab', Space: 'space', Backspace: 'backspace', Delete: 'delete',
  Insert: 'insert', Home: 'home', End: 'end', PageUp: 'pageup', PageDown: 'pagedown', ArrowUp: 'up', ArrowDown: 'down',
  ArrowLeft: 'left', ArrowRight: 'right', PrintScreen: 'printscreen', Pause: 'pause', CapsLock: 'capslock',
  Minus: '-', Equal: '=', BracketLeft: '[', BracketRight: ']', Backslash: '\\', Semicolon: ';', Quote: "'",
  Comma: ',', Period: '.', Slash: '/', Backquote: '`', NumpadMultiply: 'multiply', NumpadAdd: 'add',
  NumpadSubtract: 'subtract', NumpadDecimal: 'decimal', NumpadDivide: 'divide',
  MediaPlayPause: 'playpause', MediaTrackNext: 'nexttrack', MediaTrackPrevious: 'prevtrack',
};
function captureHotkey(btn) {
  const input = $('#eParams [data-k="keys"]');
  btn.classList.add('rec'); input.value = 'pressione o atalho…'; S.capturing = true;
  const onKey = e => {
    e.preventDefault(); e.stopPropagation();
    if (['Control', 'Shift', 'Alt', 'Meta', 'OS'].includes(e.key)) return;
    let k = CODE_NAMES[e.code];
    if (!k) {
      if (/^Key[A-Z]$/.test(e.code)) k = e.code.slice(3).toLowerCase();
      else if (/^Digit\d$/.test(e.code)) k = e.code.slice(5);
      else if (/^F\d{1,2}$/.test(e.code)) k = e.code.toLowerCase();
      else if (/^Numpad\d$/.test(e.code)) k = 'num' + e.code.slice(6);
      else return;
    }
    const mods = [e.ctrlKey && 'ctrl', e.shiftKey && 'shift', e.altKey && 'alt', e.metaKey && 'win'].filter(Boolean);
    input.value = [...mods, k].join('+');
    input.dispatchEvent(new Event('input'));
    stop();
  };
  const stop = () => { document.removeEventListener('keydown', onKey, true); btn.classList.remove('rec'); setTimeout(() => { S.capturing = false; }, 0); };
  document.addEventListener('keydown', onKey, true);
  setTimeout(() => { if (btn.classList.contains('rec')) { stop(); if (input.value.startsWith('pressione')) input.value = S.draft?.b.action.keys || ''; } }, 8000);
}

function saveDraft() {
  const d = S.draft.b; const a = d.action;
  if (a.type === 'hotkey' && !String(a.keys || '').trim()) return toast('Escreva o atalho (ex.: ctrl+shift+m)', 'err');
  if (a.type === 'open' && !String(a.target || '').trim()) return toast('Diga o que abrir', 'err');
  if (a.type === 'run' && !String(a.command || '').trim()) return toast('Escreva o comando', 'err');
  if (a.type === 'clip') a.seconds = Math.max(3, Math.min(300, Number(a.seconds) || 15));
  const pin = S.draft.pin && !NOT_PINNABLE.includes(a.type);
  if (pin) d.size = '1x1';
  S.layout.pinned = S.layout.pinned || [];
  const loc = S.draft.isNew ? null : locate(d.id);
  if (loc && loc.pinned === pin) loc.list[loc.i] = d; // continua no mesmo lugar
  else {
    if (pin && S.layout.pinned.length >= MAX_PINNED) return toast(`Já tem ${MAX_PINNED} botões fixos`, 'err');
    if (loc) loc.list.splice(loc.i, 1);
    if (pin) S.layout.pinned.push(d); else curPage().buttons.push(d);
    if (loc) toast(pin ? 'Fixado no topo: aparece em todas as páginas' : 'Saiu do topo e voltou para esta página');
  }
  persist(); closeSheet(); render();
}

function moveButton(dir) {
  const loc = locate(S.draft.b.id); if (!loc) return;
  const list = loc.list, i = loc.i, j = i + dir;
  if (j < 0 || j >= list.length) return;
  [list[i], list[j]] = [list[j], list[i]];
  persist(); render(); toast(dir < 0 ? 'Movido para trás' : 'Movido para frente');
}

// ------------------------------------------------------------------ páginas
function newPage() {
  const name = (prompt('Nome da nova página:', `Página ${S.layout.pages.length + 1}`) || '').trim();
  if (!name) return;
  const p = { id: rid(), name: name.slice(0, 40), buttons: [] };
  S.layout.pages.push(p); S.page = p.id; persist(); render();
}
function openPageEditor() {
  const page = curPage();
  const pid = page.id;
  const many = S.layout.pages.length > 1;
  openSheet(`
    <div class="sheet-head"><h3>Página</h3>
      <button class="iconbtn" id="pClose">${closeIcon()}</button></div>
    <div class="field"><label>Nome</label><input id="pName" maxlength="40" value="${esc(page.name)}"></div>
    <div class="row">
      <button class="btn" id="pLeft">${icon('left')} Mover</button>
      <button class="btn" id="pRight">Mover ${icon('right')}</button>
      ${many ? `<button class="btn danger" id="pDel">${icon('trash')} Excluir página</button>` : ''}
    </div>
    <div class="row end"><button class="btn" id="pCancel">Cancelar</button><button class="btn primary" id="pSave">${icon('check')} Salvar</button></div>`);
  $('#pClose').onclick = $('#pCancel').onclick = closeSheet;
  $('#pSave').onclick = () => {
    const pg = S.layout.pages.find(p => p.id === pid);
    if (pg) pg.name = $('#pName').value.trim().slice(0, 40) || pg.name;
    persist(); closeSheet(); render();
  };
  const mv = dir => {
    const ps = S.layout.pages; const i = ps.findIndex(p => p.id === pid); const j = i + dir;
    if (i < 0 || j < 0 || j >= ps.length) return;
    [ps[i], ps[j]] = [ps[j], ps[i]]; persist(); render();
  };
  $('#pLeft').onclick = () => mv(-1);
  $('#pRight').onclick = () => mv(1);
  if (many) $('#pDel').onclick = () => {
    if (!confirm(`Excluir a página "${page.name}" e todos os botões dela?`)) return;
    S.layout.pages = S.layout.pages.filter(p => p.id !== pid);
    S.page = S.layout.pages[0].id; persist(); closeSheet(); render();
  };
}

// ------------------------------------------------------------------ tela cheia
// Toque num gráfico ou no painel de música: abre em tela cheia. Deslize para os lados
// para passar pelos itens escolhidos em Ajustes › Tela cheia (padrão: música, GPU, CPU, RAM e FPS).
const FS_VIEWS = { music: ['Música', 'music'], gpu: ['GPU', 'gpu'], cpu: ['CPU', 'cpu'], ram: ['RAM', 'ram'],
  fps: ['FPS', 'speed'], gputemp: ['Temp. GPU', 'thermo'], vram: ['VRAM', 'chip'] };
const FS_DEFAULT = ['music', 'gpu', 'cpu', 'ram', 'fps'];
const FS_COLOR = { fps: '#0e7490', gpu: '#15803d', cpu: '#1d4ed8', ram: '#6d28d9', gputemp: '#c2410c', vram: '#065f46' };
const FS_UNIT = { gpu: '%', cpu: '%', ram: '%', vram: '%', gputemp: '°', fps: '' };
const FS = { open: false, views: [], idx: 0, app: 'spotify', raf: 0, tipTimer: 0 };
const fsRange = () => (LS.get('pd_fs_range', '60') === '300' ? 300 : 60);

function fsList() {
  const l = (S.layout?.fullscreen || []).filter(v => FS_VIEWS[v]);
  return l.length ? l : FS_DEFAULT.slice();
}
function eachButton(fn) {
  for (const p of S.layout?.pages || []) for (const b of p.buttons) { const r = fn(b); if (r) return r; }
  return null;
}
// a cor do gráfico segue a cor do bloco desse mostrador na grade
const statColor = st => eachButton(b => (b.action?.type === 'stat' && b.action.stat === st ? safeColor(b.color) : null)) || FS_COLOR[st] || '#334155';
const playerApp = () => eachButton(b => (b.action?.type === 'player' ? (b.action.app === 'any' ? 'any' : 'spotify') : null)) || 'spotify';

function openFocus(view, app) {
  if (!S.layout) return;
  FS.app = app || playerApp();
  FS.views = fsList();
  if (view && !FS.views.includes(view)) FS.views.unshift(view); // tocou num gráfico que não está na lista: entra na frente
  FS.idx = Math.max(0, FS.views.indexOf(view));
  buildFocus();
  $('#focus').classList.remove('hidden');
  document.body.classList.add('fs-open');
  FS.open = true;
  FS.openedAt = performance.now();
  const tr = $('#fsTrack');
  tr.scrollLeft = FS.idx * tr.clientWidth;
  fsSync();
  updateFocus();
  keepAwake(true);
  // no PC (mouse), ocupa o monitor inteiro
  if (matchMedia('(pointer: fine)').matches && document.documentElement.requestFullscreen && !document.fullscreenElement) {
    document.documentElement.requestFullscreen().catch(() => {});
  }
}
function closeFocus() {
  if (!FS.open) return;
  FS.open = false;
  $('#focus').classList.add('hidden');
  document.body.classList.remove('fs-open');
  $('#fsTrack').innerHTML = '';
  keepAwake(false);
  if (document.fullscreenElement && document.exitFullscreen) document.exitFullscreen().catch(() => {});
}

function buildFocus() {
  $('#fsTrack').innerHTML = FS.views.map(v => (v === 'music' ? fsMusicHTML() : fsStatHTML(v))).join('');
  $('#fsDots').innerHTML = FS.views.length > 1
    ? FS.views.map((v, i) => `<button data-i="${i}" aria-label="${esc(FS_VIEWS[v][0])}"></button>`).join('') : '';
  $('#fsClose').innerHTML = icon('x');
  $('#fsPinned').innerHTML = pinnedHTML(true);
  $('#fsPrev').innerHTML = icon('left');
  $('#fsNext').innerHTML = icon('right');
  const r = String(fsRange());
  $$('#fsRange button').forEach(b => b.classList.toggle('on', b.dataset.r === r));
}
function fsMusicHTML() {
  return `<section class="fs-slide fs-music" data-view="music"><div class="pl-bg"></div>
    <div class="fsm-body"><div class="pl-art">${icon('music')}</div>
      <div class="fsm-side">
        <div class="pl-app">${icon('music')}<span>${FS.app === 'any' ? 'Música' : 'Spotify'}</span></div>
        <div class="pl-title">—</div><div class="pl-artist"></div>
        <div class="pl-prog"><i></i></div><div class="pl-times"><span></span><span></span></div>
        <div class="pl-ctrls">
          <button class="pl-b" data-sub="shuffle" aria-label="Aleatório">${icon('shuffle')}</button>
          <button class="pl-b" data-sub="prev" aria-label="Anterior">${icon('prev')}</button>
          <button class="pl-b big" data-sub="playpause" aria-label="Play ou pausa">${icon('play')}</button>
          <button class="pl-b" data-sub="next" aria-label="Próxima">${icon('next')}</button>
        </div>
      </div></div></section>`;
}
function fsStatHTML(v) {
  const [name, ic] = FS_VIEWS[v];
  return `<section class="fs-slide fs-stat" data-view="${v}" style="--c:${statColor(v)}">
    <div class="fss-info">
      <div class="fss-head"><span class="fss-ico">${icon(ic)}</span><b>${name}</b><span class="fss-sub"></span></div>
      <div class="fss-val">—</div>
      <div class="fss-mma"></div>
    </div>
    <div class="fss-chart"><svg aria-hidden="true"></svg><span class="fss-xh"></span><span class="fss-pt"></span><span class="fss-tip"></span></div>
  </section>`;
}

function updateFocus() {
  if (!FS.open) return;
  const t = S.tick || {};
  for (const sl of $$('#fsTrack .fs-slide')) {
    if (sl.dataset.view === 'music') updatePlayer(sl, { app: FS.app }, t);
    else updateFsStat(sl, sl.dataset.view, t);
  }
}
function updateFsStat(sl, v, t) {
  const val = statValue(v, t);
  const html = val.html + (val.hot ? hotIco : '');
  const ve = sl.querySelector('.fss-val');
  if (ve.innerHTML !== html) ve.innerHTML = html;
  sl.classList.toggle('hot', !!val.hot);
  const sub = sl.querySelector('.fss-sub');
  if (sub.textContent !== (val.sub || '')) sub.textContent = val.sub || '';
  const n = fsRange(), key = GRAPH[v], u = FS_UNIT[v];
  const st = histStats(key, n);
  const cells = st ? [['máx', st.max], ['méd', st.avg], ['mín', st.min]] : [];
  if (st && v === 'fps' && t.fps?.low1 != null) cells.push(['1% low', t.fps.low1]);
  const mh = cells.length ? cells.map(([k, x]) => `<div><small>${k}</small><b>${x}${u}</b></div>`).join('')
    : `<div class="none">Sem dados ${n === 60 ? 'no último minuto' : 'nos últimos 5 minutos'}</div>`;
  const me = sl.querySelector('.fss-mma');
  if (me.innerHTML !== mh) me.innerHTML = mh;
  drawFsChart(sl.querySelector('.fss-chart'), key, n, st, u);
}

// escala fixa (0–100) para %, e "redonda" para o FPS
function fsScale(key, vals) {
  if (key === 'fps') {
    const mx = vals.length ? Math.max(...vals) : 60;
    const step = mx <= 75 ? 15 : mx <= 150 ? 30 : mx <= 300 ? 60 : 120;
    return { top: Math.max(60, Math.ceil((mx * 1.08) / step) * step), step };
  }
  return key === 'gputemp' ? { top: 100, step: 20 } : { top: 100, step: 25 };
}
function drawFsChart(box, key, n, st, u) {
  const W = box.clientWidth, H = box.clientHeight;
  if (!W || !H) return;
  const all = recent(key, n);
  const ok = v => typeof v === 'number' && (key !== 'fps' || v > 0);
  const { top, step } = fsScale(key, all.filter(ok));
  const L = 44, R = 12, T = 10, B = 26, pw = W - L - R, ph = H - T - B;
  const off = n - all.length;
  const X = i => L + ((off + i) / (n - 1)) * pw;
  const Y = v => T + ph - (Math.max(0, Math.min(top, v)) / top) * ph;
  const ticks = top / step, every = ph / ticks < 24 ? 2 : 1;
  let g = '';
  for (let k = 0; k <= ticks; k++) {
    const y = Y(k * step).toFixed(1);
    g += `<line class="gl${k ? '' : ' base'}" x1="${L}" x2="${W - R}" y1="${y}" y2="${y}"/>`;
    if (k % every === 0) g += `<text class="yl" x="${L - 8}" y="${(+y + 4).toFixed(1)}">${k * step}${u}</text>`;
  }
  const xl = n === 60 ? ['−1 min', '−30 s', 'agora'] : ['−5 min', '−2,5 min', 'agora'];
  g += `<text class="xl" x="${L}" y="${H - 6}">${xl[0]}</text><text class="xl mid" x="${(L + pw / 2).toFixed(1)}" y="${H - 6}">${xl[1]}</text>` +
    `<text class="xl end" x="${W - R}" y="${H - 6}">${xl[2]}</text>`;
  // uma linha por trecho contínuo: onde não teve dado (jogo fechado, PC sem resposta) fica um buraco
  let line = '', area = '', seg = [];
  const flush = () => {
    if (seg.length > 1) {
      const d = seg.map(([i, v], j) => `${j ? 'L' : 'M'}${X(i).toFixed(1)},${Y(v).toFixed(1)}`).join('');
      line += d;
      area += `${d}L${X(seg[seg.length - 1][0]).toFixed(1)},${T + ph}L${X(seg[0][0]).toFixed(1)},${T + ph}Z`;
    }
    seg = [];
  };
  all.forEach((v, i) => { if (ok(v)) seg.push([i, v]); else flush(); });
  flush();
  let extra = '';
  if (st) {
    const ya = Y(st.avg).toFixed(1);
    extra += `<line class="avg" x1="${L}" x2="${W - R}" y1="${ya}" y2="${ya}"/><text class="al" x="${L + 8}" y="${(ya - 7).toFixed(1)}">méd ${st.avg}${u}</text>`;
  }
  const last = all.length ? all[all.length - 1] : null;
  if (ok(last)) extra += `<circle class="now" cx="${X(all.length - 1).toFixed(1)}" cy="${Y(last).toFixed(1)}" r="5.5"/>`;
  const svg = box.querySelector('svg');
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  svg.innerHTML = `${g}<path class="area" d="${area}"/><path class="line" d="${line}"/>${extra}`;
  box._geo = { L, pw, n, off, all, u, key, Y, ok };
  if (box._scrubX != null) fsScrub(box, box._scrubX);
}
// ler um ponto: passe o mouse (PC) ou toque no gráfico (celular)
function fsScrub(box, clientX) {
  const g = box._geo;
  if (!g) return;
  box._scrubX = clientX;
  const r = box.getBoundingClientRect();
  const f = Math.max(0, Math.min(1, (clientX - r.left - g.L) / g.pw));
  const idx = Math.round(f * (g.n - 1)), i = idx - g.off;
  const v = i >= 0 && i < g.all.length ? g.all[i] : null;
  const x = g.L + (idx / (g.n - 1)) * g.pw;
  const ago = g.n - 1 - idx;
  const when = !ago ? 'agora' : ago < 60 ? `há ${ago} s` : `há ${Math.floor(ago / 60)} min${ago % 60 ? ` ${ago % 60} s` : ''}`;
  const tip = box.querySelector('.fss-tip'), pt = box.querySelector('.fss-pt');
  tip.innerHTML = `<small>${when}</small>${g.ok(v) ? `${v}${g.key === 'fps' ? ' FPS' : g.u}` : 'sem dado'}`;
  box.querySelector('.fss-xh').style.left = `${x}px`;
  const tw = tip.offsetWidth || 120;
  tip.style.left = `${Math.max(tw / 2, Math.min(r.width - tw / 2, x))}px`;
  box.classList.toggle('has-pt', g.ok(v));
  if (g.ok(v)) { pt.style.left = `${x}px`; pt.style.top = `${g.Y(v)}px`; }
  box.classList.add('scrub');
}
function fsEndScrub(box) { box._scrubX = null; box.classList.remove('scrub'); }

function fsSync() {
  const tr = $('#fsTrack');
  FS.idx = Math.max(0, Math.min(FS.views.length - 1, Math.round(tr.scrollLeft / Math.max(1, tr.clientWidth))));
  $$('#fsDots button').forEach((b, k) => b.classList.toggle('on', k === FS.idx));
  $('#fsRange').classList.toggle('off', FS.views[FS.idx] === 'music');
  $('#fsPrev').disabled = FS.idx === 0;
  $('#fsNext').disabled = FS.idx >= FS.views.length - 1;
}
function fsGo(i) {
  if (!FS.open || i < 0 || i >= FS.views.length) return;
  const tr = $('#fsTrack');
  tr.scrollTo({ left: i * tr.clientWidth, behavior: 'smooth' });
}
$('#fsTrack').addEventListener('scroll', () => {
  if (!FS.open) return;
  cancelAnimationFrame(FS.raf);
  FS.raf = requestAnimationFrame(fsSync);
}, { passive: true });
const fsJustOpened = () => performance.now() - (FS.openedAt || 0) < 450; // o mesmo toque que abriu não aciona nada aqui
$('#fsTrack').addEventListener('click', e => {
  if (fsJustOpened()) return;
  const b = e.target.closest('[data-sub]');
  if (b) { fsPress(b); return; }
  const box = e.target.closest('.fss-chart');
  if (box && !matchMedia('(hover: hover)').matches) { // celular: toque mostra o valor daquele ponto por 3 s
    fsScrub(box, e.clientX);
    clearTimeout(FS.tipTimer);
    FS.tipTimer = setTimeout(() => fsEndScrub(box), 3000);
  }
});
$('#fsTrack').addEventListener('pointermove', e => {
  if (e.pointerType !== 'mouse') return;
  const box = e.target.closest('.fss-chart');
  $$('#fsTrack .fss-chart.scrub').forEach(x => { if (x !== box) fsEndScrub(x); });
  if (box) fsScrub(box, e.clientX);
});
$('#fsTrack').addEventListener('pointerleave', () => $$('#fsTrack .fss-chart.scrub').forEach(fsEndScrub));
$('#fsClose').addEventListener('click', () => { if (!fsJustOpened()) closeFocus(); });
$('#fsPrev').addEventListener('click', () => fsGo(FS.idx - 1));
$('#fsNext').addEventListener('click', () => fsGo(FS.idx + 1));
$('#fsDots').addEventListener('click', e => { const b = e.target.closest('[data-i]'); if (b) fsGo(Number(b.dataset.i)); });
$('#fsRange').addEventListener('click', e => {
  const b = e.target.closest('[data-r]');
  if (!b) return;
  LS.set('pd_fs_range', b.dataset.r);
  $$('#fsRange button').forEach(x => x.classList.toggle('on', x === b));
  $$('#fsTrack .fss-chart').forEach(fsEndScrub);
  updateFocus();
});
// arrastar para baixo fecha
(() => {
  let d = null;
  $('#focus').addEventListener('pointerdown', e => { if (e.pointerType !== 'mouse') d = { id: e.pointerId, x: e.clientX, y: e.clientY }; });
  $('#focus').addEventListener('pointerup', e => {
    if (!d || e.pointerId !== d.id) return;
    const dx = e.clientX - d.x, dy = e.clientY - d.y;
    d = null;
    if (dy > 90 && Math.abs(dx) < dy * 0.6) closeFocus();
  });
  $('#focus').addEventListener('pointercancel', () => { d = null; });
})();
window.addEventListener('resize', () => {
  if (!FS.open) return;
  requestAnimationFrame(() => { const tr = $('#fsTrack'); tr.scrollLeft = FS.idx * tr.clientWidth; updateFocus(); });
});

function fsPress(btn) {
  haptic();
  btn.classList.add('pressed');
  setTimeout(() => btn.classList.remove('pressed'), 140);
  if (!S.connected) { toast('Sem conexão com o PC', 'err'); return; }
  send({ type: 'press', id: `_player:${FS.app}`, sub: btn.dataset.sub });
  if (btn.dataset.sub === 'playpause') { // resposta instantânea na tela
    const playing = btn.dataset.st === 'true';
    btn.dataset.st = String(!playing);
    btn.innerHTML = icon(playing ? 'play' : 'pause');
  }
}

// tela acesa enquanto a tela cheia está aberta (iPhone com iOS 18.4 ou mais novo)
let wakeLock = null;
async function keepAwake(on) {
  try {
    if (on && !wakeLock && navigator.wakeLock) {
      wakeLock = await navigator.wakeLock.request('screen');
      wakeLock.addEventListener('release', () => { wakeLock = null; });
    } else if (!on && wakeLock) {
      const w = wakeLock; wakeLock = null; await w.release();
    }
  } catch (e) { wakeLock = null; }
}
document.addEventListener('visibilitychange', () => { if (!document.hidden && FS.open) keepAwake(true); });

// ------------------------------------------------------------------ deslizar entre páginas
// Arraste a grade para o lado: a página acompanha o dedo e troca ao soltar.
// Encostou num botão e começou a deslizar? O botão é cancelado (nada é acionado).
const SWP = { cur: null };
const pageIndex = () => S.layout.pages.findIndex(p => p.id === curPage().id);
$('#deck').addEventListener('pointerdown', e => {
  if (e.pointerType === 'mouse' || !S.layout || S.layout.pages.length < 2) return;
  SWP.cur = { id: e.pointerId, x: e.clientX, y: e.clientY, t: performance.now(), on: false, dx: 0 };
}, true);
document.addEventListener('pointermove', e => {
  const s = SWP.cur;
  if (!s || e.pointerId !== s.id) return;
  const dx = e.clientX - s.x, dy = e.clientY - s.y;
  if (!s.on) {
    if (Math.abs(dy) > 28 && Math.abs(dy) > Math.abs(dx)) { SWP.cur = null; return; } // gesto vertical: não é troca de página
    if (Math.abs(dx) < 14 || Math.abs(dx) < Math.abs(dy) * 1.3) return;
    s.on = true;
    if (TAP.cur) endTap(TAP.cur, true);
    $('#deck').style.transition = 'none';
  }
  const i = pageIndex(), n = S.layout.pages.length;
  const edge = (i === 0 && dx > 0) || (i === n - 1 && dx < 0);
  s.dx = dx;
  $('#deck').style.transform = `translateX(${edge ? dx * 0.25 : dx}px)`;
});
function endSwipe(e, cancelled) {
  const s = SWP.cur;
  if (!s || e.pointerId !== s.id) return;
  SWP.cur = null;
  if (!s.on) return;
  S.swipeAt = Date.now();
  const deck = $('#deck');
  const speed = Math.abs(s.dx) / Math.max(1, performance.now() - s.t);
  const far = Math.abs(s.dx) > Math.min(110, deck.clientWidth * 0.25) || (speed > 0.45 && Math.abs(s.dx) > 40);
  const dir = !cancelled && far ? (s.dx < 0 ? 1 : -1) : 0;
  if (!dir || !swipePage(dir)) {
    deck.style.transition = 'transform .22s ease';
    deck.style.transform = '';
  }
}
document.addEventListener('pointerup', e => endSwipe(e, false));
document.addEventListener('pointercancel', e => endSwipe(e, true));
function swipePage(dir) {
  if (!S.layout) return false;
  const j = pageIndex() + dir;
  if (j < 0 || j >= S.layout.pages.length) return false;
  const deck = $('#deck'), w = deck.clientWidth;
  haptic();
  deck.style.transition = 'transform .15s ease-in, opacity .15s';
  deck.style.transform = `translateX(${-dir * w * 0.5}px)`;
  deck.style.opacity = '0';
  setTimeout(() => {
    goPage(S.layout.pages[j].id);
    deck.style.transition = 'none';
    deck.style.transform = `translateX(${dir * w * 0.3}px)`;
    void deck.offsetWidth;
    deck.style.transition = 'transform .22s ease-out, opacity .22s';
    deck.style.transform = '';
    deck.style.opacity = '';
  }, 150);
  return true;
}

// ------------------------------------------------------------------ mouse e teclado
// Touchpad e teclado para mexer no PC pelo celular. Gestos do touchpad:
//   1 dedo move · toque = clique · toque duplo e arraste = arrastar
//   2 dedos rolam (como no iPhone) · toque com 2 dedos = botão direito
const RM = { open: false, mods: new Set(), lastWarn: 0 };
const TP = { n: 0, max: 0, start: 0, sx: 0, sy: 0, last: null, moved: false, dragPending: false, dragging: false,
  lastTap: 0, mx: 0, my: 0, wx: 0, wy: 0, raf: 0 };
const RM_SPEEDS = [0.7, 1.0, 1.4, 1.9, 2.6];
const rmSpeed = () => Math.max(1, Math.min(5, Number(LS.get('pd_rm_speed', '3')) || 3));
// [tecla, rótulo] — "mod:" = fica ligada até a próxima tecla; "combo:" = atalho pronto
const RM_KEYS = [
  ['esc', 'Esc'], ['tab', 'Tab'], ['mod:ctrl', 'Ctrl'], ['mod:alt', 'Alt'], ['mod:shift', 'Shift'], ['mod:win', 'Win'],
  ['left', '←'], ['up', '↑'], ['down', '↓'], ['right', '→'], ['backspace', 'ic:backspace'], ['delete', 'Del'], ['enter', 'Enter'],
  ['combo:alt+tab', 'Alt+Tab'], ['combo:ctrl+c', 'Copiar'], ['combo:ctrl+v', 'Colar'], ['combo:ctrl+z', 'Desfazer'],
  ['combo:ctrl+a', 'Tudo'], ['combo:win+d', 'Área de trab.'], ['printscreen', 'Print'], ['f5', 'F5'], ['f11', 'F11'],
];

function sendRemote(o) {
  if (send({ type: 'remote', ...o })) return true;
  if (Date.now() - RM.lastWarn > 3000) { RM.lastWarn = Date.now(); toast('Sem conexão com o PC', 'err'); }
  return false;
}
function openRemote() {
  if (FS.open) closeFocus();
  RM.open = true; RM.mods.clear(); RM.openedAt = performance.now();
  $('#rmClose').innerHTML = icon('x');
  $('#rmKb').innerHTML = icon('keyboard');
  renderRmKeys(); renderRmSpeed();
  $('#remote').classList.remove('hidden');
  document.body.classList.add('rm-open');
  fitRemote();
}
function closeRemote() {
  if (!RM.open) return;
  RM.open = false;
  if (TP.dragging) { sendRemote({ op: 'button', button: 'left', action: 'up' }); TP.dragging = false; }
  for (const b of $$('.rm-mb.down')) { sendRemote({ op: 'button', button: b.dataset.mb, action: 'up' }); b.classList.remove('down'); }
  $('#kbIn').blur();
  $('#remote').classList.add('hidden');
  $('#remote').style.height = ''; $('#remote').style.top = '';
  document.body.classList.remove('rm-open');
}
// com o teclado do iPhone aberto, a tela útil encolhe: o touchpad acompanha (fica acima do teclado)
function fitRemote() {
  if (!RM.open) return;
  const vv = window.visualViewport;
  const r = $('#remote');
  if (vv) { r.style.height = `${vv.height}px`; r.style.top = `${vv.offsetTop}px`; }
  $('#rmKb').classList.toggle('on', document.activeElement === $('#kbIn'));
}
if (window.visualViewport) {
  visualViewport.addEventListener('resize', fitRemote);
  visualViewport.addEventListener('scroll', fitRemote);
}
// o mesmo toque que abriu a tela não pode acionar a tecla que ficou embaixo do dedo
const rmJustOpened = () => performance.now() - (RM.openedAt || 0) < 450;
// tocar numa tecla não tira o foco do campo de texto (senão o teclado do celular fecha)
for (const sel of ['#rmKeys', '#rmKb', '.rm-speed', '#rmClose']) $(sel).addEventListener('pointerdown', e => e.preventDefault());
$('#rmClose').addEventListener('click', () => { if (!rmJustOpened()) closeRemote(); });
$('#rmKb').addEventListener('click', () => {
  if (rmJustOpened()) return;
  const kb = $('#kbIn');
  if (document.activeElement === kb) kb.blur();
  else { kb.value = ' '; kb.focus(); kb.setSelectionRange(1, 1); }
  setTimeout(fitRemote, 50);
});
$('#kbIn').addEventListener('focus', () => setTimeout(fitRemote, 300));
$('#kbIn').addEventListener('blur', () => setTimeout(fitRemote, 300));
$('.rm-speed').addEventListener('click', e => {
  const b = e.target.closest('[data-sp]'); if (!b || rmJustOpened()) return;
  LS.set('pd_rm_speed', String(Math.max(1, Math.min(5, rmSpeed() + Number(b.dataset.sp)))));
  renderRmSpeed(); haptic();
});
function renderRmSpeed() { $('#rmSpeed').textContent = `vel. ${rmSpeed()}`; }

// --- touchpad
const tp = $('#tp');
const center = ts => { let x = 0, y = 0; for (const t of ts) { x += t.clientX; y += t.clientY; } return { x: x / ts.length, y: y / ts.length }; };
function tpFlush() {
  TP.raf = 0;
  const ix = Math.trunc(TP.mx), iy = Math.trunc(TP.my);
  if (ix || iy) { TP.mx -= ix; TP.my -= iy; sendRemote({ op: 'move', dx: ix, dy: iy }); }
  const wy = Math.trunc(TP.wy), wx = Math.trunc(TP.wx);
  if (wy || wx) { TP.wy -= wy; TP.wx -= wx; sendRemote({ op: 'wheel', dy: wy, dx: wx }); }
}
const tpSchedule = () => { if (!TP.raf) TP.raf = requestAnimationFrame(tpFlush); };
function tpMove(dx, dy) { // aceleração: devagar = preciso, rápido = atravessa a tela
  const v = Math.hypot(dx, dy);
  const gain = RM_SPEEDS[rmSpeed() - 1] * (1 + Math.min(v, 40) / 14);
  TP.mx += dx * gain; TP.my += dy * gain; tpSchedule();
}
function tpScroll(dx, dy) { // rolagem "natural", como no iPhone: o conteúdo segue o dedo
  TP.wy += dy * 4; TP.wx -= dx * 4; tpSchedule();
}
tp.addEventListener('touchstart', e => {
  e.preventDefault();
  const n = e.touches.length;
  if (TP.n === 0) { // começou um gesto novo
    TP.start = performance.now(); TP.moved = false; TP.max = n;
    const c = center(e.touches); TP.sx = c.x; TP.sy = c.y;
    TP.dragPending = n === 1 && TP.start - TP.lastTap < 300; // toque e, logo em seguida, encostou de novo: vai arrastar
  }
  TP.max = Math.max(TP.max, n); TP.n = n; TP.last = center(e.touches);
  tp.classList.add('active');
}, { passive: false });
tp.addEventListener('touchmove', e => {
  e.preventDefault();
  const c = center(e.touches);
  const dx = c.x - TP.last.x, dy = c.y - TP.last.y;
  TP.last = c;
  if (!TP.moved && Math.hypot(c.x - TP.sx, c.y - TP.sy) > 8) TP.moved = true;
  if (e.touches.length >= 2) { tpScroll(dx, dy); return; }
  if (TP.max >= 2) return; // tirou um dos 2 dedos: não move o ponteiro com o que sobrou
  if (TP.dragPending && TP.moved && !TP.dragging) {
    TP.dragging = true; haptic();
    sendRemote({ op: 'button', button: 'left', action: 'down' });
  }
  tpMove(dx, dy);
}, { passive: false });
function tpEnd(e, cancelled) {
  e.preventDefault();
  TP.n = e.touches.length;
  if (TP.n) { TP.last = center(e.touches); return; } // ainda tem dedo na tela
  tp.classList.remove('active');
  tpFlush();
  const quick = performance.now() - TP.start < 280 && !TP.moved;
  if (TP.dragging) { sendRemote({ op: 'button', button: 'left', action: 'up' }); TP.dragging = false; }
  else if (!cancelled && quick) {
    if (TP.max >= 2) { sendRemote({ op: 'button', button: 'right', action: 'click' }); haptic(); }
    else { sendRemote({ op: 'button', button: 'left', action: 'click' }); TP.lastTap = performance.now(); }
  }
  TP.dragPending = false;
}
tp.addEventListener('touchend', e => tpEnd(e, false), { passive: false });
tp.addEventListener('touchcancel', e => tpEnd(e, true), { passive: false });

// --- botões do mouse: segurar = botão apertado (dá para arrastar com o outro dedo no touchpad)
$$('.rm-mb').forEach(b => {
  const up = () => { if (!b.classList.contains('down')) return; b.classList.remove('down'); sendRemote({ op: 'button', button: b.dataset.mb, action: 'up' }); };
  b.addEventListener('pointerdown', e => {
    e.preventDefault();
    if (rmJustOpened()) return;
    haptic();
    b.classList.add('down');
    try { b.setPointerCapture(e.pointerId); } catch (err) { /* */ }
    sendRemote({ op: 'button', button: b.dataset.mb, action: 'down' });
  });
  b.addEventListener('pointerup', up);
  b.addEventListener('pointercancel', up);
});

// --- teclas especiais
function renderRmKeys() {
  const firstCombo = RM_KEYS.findIndex(x => x[0].startsWith('combo:'));
  $('#rmKeys').innerHTML = RM_KEYS.map(([k, l], i) =>
    `<button class="rm-k${k.startsWith('mod:') && RM.mods.has(k.slice(4)) ? ' on' : ''}${i === firstCombo ? ' sep' : ''}" data-k="${esc(k)}">` +
    `${l.startsWith('ic:') ? icon(l.slice(3)) : esc(l)}</button>`).join('');
}
function rmKey(name) { // aplica Ctrl/Alt/Shift/Win que estiverem ligados
  const combo = [...RM.mods, name].join('+');
  sendRemote({ op: 'key', keys: combo });
  if (RM.mods.size) { RM.mods.clear(); renderRmKeys(); }
}
$('#rmKeys').addEventListener('click', e => {
  const b = e.target.closest('[data-k]'); if (!b || rmJustOpened()) return;
  haptic();
  const k = b.dataset.k;
  if (k.startsWith('mod:')) {
    const m = k.slice(4);
    if (RM.mods.has(m)) RM.mods.delete(m); else RM.mods.add(m);
    renderRmKeys(); return;
  }
  if (k.startsWith('combo:')) { sendRemote({ op: 'key', keys: k.slice(6) }); return; }
  rmKey(k);
});

// --- teclado do iPhone: cada letra digitada vai na hora para o PC
const KB_SENTINEL = ' '; // sempre tem 1 caractere no campo, para o "apagar" funcionar mesmo vazio
function rmText(text) {
  if (!text) return;
  if (RM.mods.size && text.length === 1) { // ex.: Ctrl ligado + "c" = Ctrl+C
    const ch = text.toLowerCase();
    const name = /^[a-z0-9]$/.test(ch) ? ch : ch === ' ' ? 'space' : null;
    if (name) { rmKey(name); return; }
  }
  sendRemote({ op: 'text', text });
  if (RM.mods.size) { RM.mods.clear(); renderRmKeys(); }
}
const kbIn = $('#kbIn');
kbIn.addEventListener('beforeinput', e => {
  const t = e.inputType || '';
  let handled = true;
  if (t === 'insertText' || t === 'insertFromPaste' || t === 'insertReplacementText') {
    rmText(e.data ?? (e.dataTransfer ? e.dataTransfer.getData('text/plain') : ''));
  } else if (t === 'insertLineBreak' || t === 'insertParagraph') rmKey('enter');
  else if (t === 'deleteContentBackward' || t === 'deleteWordBackward') rmKey('backspace');
  else if (t === 'deleteContentForward') rmKey('delete');
  else handled = false; // composição (ex.: japonês): deixa o "input" abaixo resolver
  if (handled) e.preventDefault();
});
kbIn.addEventListener('input', () => { // navegadores que não deixam cancelar o beforeinput
  const v = kbIn.value;
  if (v === KB_SENTINEL) return;
  if (v.length > KB_SENTINEL.length) rmText(v.slice(KB_SENTINEL.length));
  else rmKey('backspace');
  kbIn.value = KB_SENTINEL; kbIn.setSelectionRange(1, 1);
});
// teclado físico (iPad / PC): setas, Tab, Esc… também vão para o PC
const HW_KEYS = { ArrowLeft: 'left', ArrowRight: 'right', ArrowUp: 'up', ArrowDown: 'down', Tab: 'tab', Escape: 'esc',
  Home: 'home', End: 'end', PageUp: 'pageup', PageDown: 'pagedown', Delete: 'delete' };
function rmHardwareKey(e) {
  const name = HW_KEYS[e.key];
  if (e.key === 'Escape' && document.activeElement !== kbIn) { closeRemote(); return; }
  if (name && document.activeElement === kbIn) { e.preventDefault(); rmKey(name); }
}

// ------------------------------------------------------------------ ajustes
function openSettings() {
  const L = S.layout;
  const th = L.theme || { name: 'classico', mode: 'auto' };
  const c = S.tick.clip || {};
  const clipTxt = { running: 'gravando em segundo plano', starting: 'iniciando…', paused: 'em espera', ready: 'modo atalho', off: 'em espera', error: 'erro: ' + (c.error || '') }[c.status] || '—';
  openSheet(`
    <div class="sheet-head"><h3>Ajustes</h3>
      <button class="iconbtn" id="sClose">${closeIcon()}</button></div>
    <h4>Tema</h4>
    <div class="themes" id="sThemes">${THEMES.map(([id, name, desc, bg, kind]) => `
      <button class="theme-card${id === th.name ? ' on' : ''}" data-theme="${id}">
        <div class="sw" style="${bg}">${swatch(kind)}</div><b>${name}</b><small>${desc}</small></button>`).join('')}
    </div>
    <div class="field" style="margin-top:12px"><span>Aparência</span>
      <div class="seg" id="sMode">${[['auto', 'Automático'], ['dark', 'Escuro'], ['light', 'Claro']].map(([m, n]) =>
        `<button data-mode="${m}" class="${m === th.mode ? 'on' : ''}">${n}</button>`).join('')}</div>
      <div class="hint">Automático segue o modo claro/escuro do iPhone.</div></div>
    <hr>
    <h4>Toque</h4>
    <div class="field"><span>Acionar o botão</span>
      <div class="seg" id="sTap">${[['release', 'Ao soltar o dedo'], ['down', 'Ao encostar']].map(([m, n]) =>
        `<button data-tap="${m}" class="${m === tapMode() ? 'on' : ''}">${n}</button>`).join('')}</div>
      <div class="hint">“Ao soltar” evita toques sem querer: encostou no botão errado? Arraste o dedo para fora antes de soltar.</div></div>
    <hr>
    <h4>Tela cheia</h4>
    <p class="hint fs-hint">Toque num gráfico, no painel de música ou em ${icon('expand')} para abrir. Deslize para os lados para trocar.
      Escolha o que aparece e a ordem:</p>
    <div class="fslist" id="sFs"></div>
    <hr>
    <h4>Grade</h4>
    <div class="field"><span>Colunas com o celular em pé</span>
      <div class="stepper"><button class="btn" data-g="portrait" data-d="-1">−</button><b id="gP">${L.grid.portrait}</b><button class="btn" data-g="portrait" data-d="1">+</button></div></div>
    <div class="field"><span>Colunas com o celular deitado</span>
      <div class="stepper"><button class="btn" data-g="landscape" data-d="-1">−</button><b id="gL">${L.grid.landscape}</b><button class="btn" data-g="landscape" data-d="1">+</button></div></div>
    <label class="toggle">Mostrar nomes nos botões <input type="checkbox" id="sLabels" ${L.showLabels ? 'checked' : ''}></label>
    <label class="toggle">Vibrar ao tocar <input type="checkbox" id="sHaptic" ${LS.get('pd_haptic', '1') === '1' ? 'checked' : ''}></label>
    <hr>
    <p class="hint">PC: <b>${esc(location.host)}</b> · ${S.tick.usb ? 'ligado pelo cabo USB' : 'ligado pela rede'}<br>
    Clipe: ${esc(clipTxt)}${c.encoder ? ` (${esc(c.capture)} + ${esc(c.encoder)}${c.direct ? ', direto na GPU' : ''})` : ''}${c.last_check?.fps != null ? ` · último: ${Math.round(c.last_check.fps)} fps` : ''}<br>
    GPU: ${esc(S.tick.gpu?.name || 'não detectada')}</p>
    <div class="row">
      <button class="btn danger" id="sReset">Restaurar botões padrão</button>
      <button class="btn" id="sLogout">Trocar código de acesso</button>
    </div>
    <div class="row end"><button class="btn primary" id="sOk">${icon('check')} Pronto</button></div>`);
  $('#sClose').onclick = $('#sOk').onclick = closeSheet;
  const setTheme = patch => {
    S.layout.theme = { ...(S.layout.theme || { name: 'classico', mode: 'auto' }), ...patch };
    applyTheme(); persist();
    $$('#sThemes .theme-card').forEach(x => x.classList.toggle('on', x.dataset.theme === S.layout.theme.name));
    $$('#sMode button').forEach(x => x.classList.toggle('on', x.dataset.mode === S.layout.theme.mode));
  };
  $('#sThemes').onclick = e => { const b = e.target.closest('.theme-card'); if (b) setTheme({ name: b.dataset.theme }); };
  $('#sMode').onclick = e => { const b = e.target.closest('button[data-mode]'); if (b) setTheme({ mode: b.dataset.mode }); };
  $('#sTap').onclick = e => {
    const b = e.target.closest('button[data-tap]'); if (!b) return;
    LS.set('pd_tap', b.dataset.tap);
    $$('#sTap button').forEach(x => x.classList.toggle('on', x === b));
  };
  renderFsSettings();
  $('#sFs').onchange = e => {
    const v = e.target.dataset.v; if (!v) return;
    let l = fsList();
    if (e.target.checked) { if (!l.includes(v)) l.push(v); }
    else if (l.length > 1) l = l.filter(x => x !== v);
    else { e.target.checked = true; toast('Deixe pelo menos um item'); return; }
    S.layout.fullscreen = l; persist(); renderFsSettings();
  };
  $('#sFs').onclick = e => {
    const b = e.target.closest('[data-mv]'); if (!b) return;
    const l = fsList(); const i = l.indexOf(b.dataset.mv); const j = i + Number(b.dataset.d);
    if (i < 0 || j < 0 || j >= l.length) return;
    [l[i], l[j]] = [l[j], l[i]];
    S.layout.fullscreen = l; persist(); renderFsSettings();
  };
  $$('[data-g]').forEach(b => b.onclick = () => {
    const k = b.dataset.g; const max = k === 'portrait' ? 8 : 12; const g = S.layout.grid;
    g[k] = Math.max(1, Math.min(max, g[k] + Number(b.dataset.d)));
    $(k === 'portrait' ? '#gP' : '#gL').textContent = g[k];
    persist(); render();
  });
  $('#sLabels').onchange = e => { S.layout.showLabels = e.target.checked; persist(); render(); };
  $('#sHaptic').onchange = e => LS.set('pd_haptic', e.target.checked ? '1' : '0');
  $('#sReset').onclick = () => {
    if (!confirm('Apagar tudo e voltar aos botões padrão? (o tema é mantido)')) return;
    send({ type: 'reset_layout' }); closeSheet(); S.page = '';
  };
  $('#sLogout').onclick = () => { closeSheet(); S.edit = false; showLogin(''); };
}

function renderFsSettings() {
  const sel = fsList();
  const all = [...sel, ...Object.keys(FS_VIEWS).filter(v => !sel.includes(v))];
  const up = icon('left').replace('<svg', '<svg style="rotate:90deg"'), down = icon('right').replace('<svg', '<svg style="rotate:90deg"');
  $('#sFs').innerHTML = all.map(v => {
    const i = sel.indexOf(v), on = i >= 0;
    const name = v === 'music' ? 'Controles de música' : FS_VIEWS[v][0];
    return `<div class="fsrow${on ? ' on' : ''}"><label><input type="checkbox" data-v="${v}" ${on ? 'checked' : ''}>` +
      `<span class="fi">${icon(FS_VIEWS[v][1])}</span><span>${on ? `<b>${i + 1}.</b> ` : ''}${name}</span></label>` +
      `<button class="iconbtn" data-mv="${v}" data-d="-1" aria-label="Subir" ${on && i > 0 ? '' : 'disabled'}>${up}</button>` +
      `<button class="iconbtn" data-mv="${v}" data-d="1" aria-label="Descer" ${on && i < sel.length - 1 ? '' : 'disabled'}>${down}</button></div>`;
  }).join('');
}

// ------------------------------------------------------------------ início
render();
connect();
