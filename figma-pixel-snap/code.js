// Pixel Snap — 選択レイヤーの端数pxを丸め、ほぼ中央のものを正確に中央へ寄せる
// ビルド不要のプレーンJS。Figmaデスクトップ版で manifest.json を読み込んで使う。

const DEFAULT_OPTIONS = {
  unit: 1,              // 位置の丸め単位(px)。サイズとAuto Layoutの値は常に1px単位
  roundPosition: true,  // X/Y を丸める
  roundSize: true,      // W/H を丸める
  roundLayout: true,    // Auto Layout の padding / gap を丸める
  centerX: true,        // 左右中央から threshold 以内のズレを中央へ
  centerY: false,       // 上下中央から threshold 以内のズレを中央へ
  threshold: 3,         // 「ほぼ中央」とみなすズレ幅(px)
  includeChildren: true,
  skipLocked: true,
};

const STORAGE_KEY = 'pixel-snap-options';
const EPS = 0.001;
const FRAME_LIKE = new Set(['FRAME', 'COMPONENT', 'COMPONENT_SET', 'INSTANCE']);
// 座標系を持たない（子の x/y が親の親基準になる）ノード
const PASS_THROUGH = new Set(['GROUP', 'BOOLEAN_OPERATION']);
const NO_RESIZE = new Set([
  'GROUP', 'BOOLEAN_OPERATION', 'LINE', 'SLICE', 'SECTION', 'CONNECTOR',
  'STICKY', 'SHAPE_WITH_TEXT', 'WIDGET', 'EMBED', 'LINK_UNFURL', 'MEDIA', 'TABLE',
]);
const LAYOUT_PROPS = [
  'paddingLeft', 'paddingRight', 'paddingTop', 'paddingBottom',
  'itemSpacing', 'counterAxisSpacing',
];

function snap(v, unit) { return Math.round(v / unit) * unit; }
function same(a, b) { return Math.abs(a - b) < EPS; }
function fmt(v) { return String(Math.round(v * 100) / 100); }
function isRotated(n) { return 'rotation' in n && Math.abs(n.rotation) > 0.01; }

function normalizeOptions(raw) {
  const o = Object.assign({}, DEFAULT_OPTIONS, raw || {});
  o.unit = [1, 2, 4, 8].includes(Number(o.unit)) ? Number(o.unit) : 1;
  o.threshold = Math.min(Math.max(Number(o.threshold) || 0, 0), 50);
  return o;
}

function inInstance(n) {
  for (let p = n.parent; p; p = p.parent) if (p.type === 'INSTANCE') return true;
  return false;
}

// 子を先に並べる（後順）。グループは子を整えた後に自身を動かすため
function collectTargets(selection, opts) {
  const out = [];
  const seen = new Set();
  function walk(n) {
    if (seen.has(n.id)) return;
    seen.add(n.id);
    if (opts.skipLocked && n.locked) return;
    if (opts.includeChildren && 'children' in n && n.type !== 'INSTANCE') {
      for (const c of n.children) walk(c);
    }
    out.push(n);
  }
  for (const n of selection) walk(n);
  return out.filter((n) => !inInstance(n));
}

// Auto Layout の子は位置をレイアウトが決めるので触らない
function canMove(n) {
  const p = n.parent;
  if (!p || p.type === 'DOCUMENT' || !('x' in n)) return false;
  if ('layoutMode' in p && p.layoutMode !== 'NONE' && n.layoutPositioning !== 'ABSOLUTE') return false;
  return true;
}

// n.x / n.y の基準になっている、中央寄せの基準フレーム
function referenceFrame(n) {
  let p = n.parent;
  while (p && PASS_THROUGH.has(p.type)) p = p.parent;
  return p && FRAME_LIKE.has(p.type) ? p : null;
}

function planSize(n, opts) {
  if (!opts.roundSize || NO_RESIZE.has(n.type) || !('resizeWithoutConstraints' in n) || isRotated(n)) return null;
  let fixW = true;
  let fixH = true;
  try {
    if ('layoutSizingHorizontal' in n && n.layoutSizingHorizontal !== 'FIXED') fixW = false;
    if ('layoutSizingVertical' in n && n.layoutSizingVertical !== 'FIXED') fixH = false;
  } catch (e) { /* レイアウト外のノードでは読めないことがある */ }
  if (n.type === 'TEXT') {
    if (n.textAutoResize === 'WIDTH_AND_HEIGHT') { fixW = false; fixH = false; }
    if (n.textAutoResize === 'HEIGHT') fixH = false;
  }
  const w = n.width;
  const h = n.height;
  const nw = fixW && w > 0 ? Math.max(1, Math.round(w)) : w;
  const nh = fixH && h > 0 ? Math.max(1, Math.round(h)) : h;
  if (same(nw, w) && same(nh, h)) return null;
  return { w: nw, h: nh };
}

async function loadFonts(n) {
  if (n.hasMissingFont) throw new Error('フォントが見つからないためサイズを変更できません');
  if (n.characters.length === 0) {
    if (n.fontName !== figma.mixed) await figma.loadFontAsync(n.fontName);
    return;
  }
  const fonts = n.getRangeAllFontNames(0, n.characters.length);
  await Promise.all(fonts.map((f) => figma.loadFontAsync(f)));
}

// 中央寄せ判定＋丸め。戻り値は新しい座標と注記
function planAxis(pos, size, refSize, center, opts) {
  let next = pos;
  let centered = false;
  const notes = [];
  if (center && refSize !== null) {
    const target = (refSize - size) / 2;
    if (Math.abs(pos - target) <= opts.threshold) {
      next = target;
      centered = true;
    }
  }
  if (opts.roundPosition) {
    const rounded = centered ? Math.round(next) : snap(next, opts.unit);
    if (centered && !same(rounded, next)) notes.push('幅の偶奇が合わず中央から0.5pxずれます');
    next = rounded;
  }
  return { next, centered: centered && !same(pos, next), notes };
}

async function run(rawOptions, apply) {
  const opts = normalizeOptions(rawOptions);
  const selection = figma.currentPage.selection;
  if (selection.length === 0) return { error: 'レイヤーを選択してください', rows: [], count: 0 };

  const targets = collectTargets(selection, opts);
  const predicted = new Map(); // 確認モード用：丸めた後のサイズの予測
  const sizeOf = (n) => predicted.get(n.id) || { w: n.width, h: n.height };
  const rows = new Map();
  const errors = [];
  const record = (n, text) => {
    if (!rows.has(n.id)) rows.set(n.id, { id: n.id, name: n.name, type: n.type, changes: [] });
    rows.get(n.id).changes.push(text);
  };

  // 1周目：サイズと Auto Layout の値（子→親の順）
  for (const n of targets) {
    try {
      const s = planSize(n, opts);
      if (s) {
        if (!same(s.w, n.width)) record(n, `W ${fmt(n.width)} → ${fmt(s.w)}`);
        if (!same(s.h, n.height)) record(n, `H ${fmt(n.height)} → ${fmt(s.h)}`);
        predicted.set(n.id, s);
        if (apply) {
          if (n.type === 'TEXT') await loadFonts(n);
          // 制約で子が動かないように resizeWithoutConstraints を使う
          n.resizeWithoutConstraints(s.w, s.h);
        }
      }
      if (opts.roundLayout && 'layoutMode' in n && n.layoutMode !== 'NONE') {
        for (const prop of LAYOUT_PROPS) {
          const v = n[prop];
          if (typeof v !== 'number' || same(v, Math.round(v))) continue;
          record(n, `${prop} ${fmt(v)} → ${Math.round(v)}`);
          if (apply) n[prop] = Math.round(v);
        }
      }
    } catch (e) {
      errors.push(`${n.name}: ${e.message}`);
    }
  }

  // 2周目：位置（子→親の順。グループは子が整ってから動かす）
  for (const n of targets) {
    try {
      if (!canMove(n)) continue;
      const size = sizeOf(n);
      const ref = referenceFrame(n);
      const refSize = ref ? sizeOf(ref) : null;
      const rotated = isRotated(n);
      const ax = planAxis(n.x, size.w, refSize && !rotated ? refSize.w : null, opts.centerX, opts);
      const ay = planAxis(n.y, size.h, refSize && !rotated ? refSize.h : null, opts.centerY, opts);
      if (!same(ax.next, n.x)) record(n, `X ${fmt(n.x)} → ${fmt(ax.next)}${ax.centered ? '（中央寄せ）' : ''}`);
      if (!same(ay.next, n.y)) record(n, `Y ${fmt(n.y)} → ${fmt(ay.next)}${ay.centered ? '（中央寄せ）' : ''}`);
      for (const note of new Set(ax.notes.concat(ay.notes))) record(n, `※ ${note}`);
      if (apply) {
        if (!same(ax.next, n.x)) n.x = ax.next;
        if (!same(ay.next, n.y)) n.y = ay.next;
      }
    } catch (e) {
      errors.push(`${n.name}: ${e.message}`);
    }
  }

  if (apply) figma.commitUndo();
  const list = Array.from(rows.values()).filter((r) => r.changes.some((c) => !c.startsWith('※')));
  return { rows: list, count: list.length, scanned: targets.length, errors };
}

async function loadOptions() {
  try {
    return normalizeOptions(await figma.clientStorage.getAsync(STORAGE_KEY));
  } catch (e) {
    return normalizeOptions();
  }
}

async function main() {
  if (figma.command === 'quick') {
    const result = await run(await loadOptions(), true);
    if (result.error) figma.notify(result.error, { error: true });
    else figma.notify(`${result.scanned}レイヤー中 ${result.count}個を調整しました（Cmd/Ctrl+Z で戻せます）`);
    figma.closePlugin();
    return;
  }

  figma.showUI(__html__, { width: 340, height: 560, themeColors: true });
  figma.ui.postMessage({ type: 'init', options: await loadOptions(), selection: figma.currentPage.selection.length });
  figma.on('selectionchange', () => {
    figma.ui.postMessage({ type: 'selection', selection: figma.currentPage.selection.length });
  });

  figma.ui.onmessage = async (msg) => {
    if (msg.type === 'run') {
      const options = normalizeOptions(msg.options);
      await figma.clientStorage.setAsync(STORAGE_KEY, options);
      const result = await run(options, msg.apply);
      figma.ui.postMessage(Object.assign({ type: 'result', apply: msg.apply }, result));
      if (msg.apply && !result.error) figma.notify(`${result.count}個のレイヤーを調整しました`);
    }
    if (msg.type === 'focus') {
      const node = await figma.getNodeByIdAsync(msg.id);
      if (node && 'x' in node) figma.viewport.scrollAndZoomIntoView([node]);
    }
  };
}

// テスト用に Node.js からも読み込めるようにする
if (typeof module !== 'undefined') {
  module.exports = { run, planAxis, planSize, normalizeOptions };
} else {
  main();
}
