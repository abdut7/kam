// Build script: content/*.md (+ content/overlays/*.md)  ->  dist/atlas.html
// Usage: node build/build.mjs   (run from anywhere)
//
// Track files:    content/NN-<name>[-part].md   merged in sorted order per prefix
// Overlay files:  content/overlays/NN-<name>.md  sections whose title matches an existing
//                 section are merged INTO it ("In plain words" / "From your saved posts"
//                 go to the top, other blocks go before Practice); unmatched sections are
//                 added as new sections (at the start when tagged [Start here], else at the end).
// Section tags:   "## Title [Basics]" / [Core] / [Advanced] / [Start here] / [New]
// Block types:    ### Concepts you must understand | ### Practice | ### In plain words
//                 ### From your saved posts | ### Q. <question> | ### C. <concept card>
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { marked } from 'marked';
import hljs from 'highlight.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const CONTENT = path.join(ROOT, 'content');
const OVERLAYS = path.join(CONTENT, 'overlays');
const TEMPLATE = path.join(ROOT, 'build', 'template.html');
const OUT_DIR = path.join(ROOT, 'dist');
const OUT = path.join(OUT_DIR, 'atlas.html');
const LEARN_LIST = path.join(CONTENT, 'learn-list.txt');
const LEARN = new Set(
  (fs.existsSync(LEARN_LIST) ? fs.readFileSync(LEARN_LIST, 'utf8') : '')
    .split('\n').map((l) => l.trim()).filter((l) => l && !l.startsWith('#'))
    .map((l) => l.replace(/\s*\t\s*/, '\t')),
);

const TRACKS = [
  { id: 'roadmap',    short: 'Roadmap',            prefix: '00-', kind: 'guide' },
  { id: 'playbook',   short: 'Interview Playbook', prefix: '13-' },
  { id: 'simple',     short: 'Explained Simply',   prefix: '10-' },
  { id: 'python',     short: 'Python',             prefix: '14-' },
  { id: 'arch',       short: 'Internal Architecture', prefix: '11-' },
  { id: 'design',     short: 'Software Design',    prefix: '12-' },
  { id: 'backend',    short: 'Backend',            prefix: '01-' },
  { id: 'frontend',   short: 'Frontend & React',   prefix: '02-' },
  { id: 'ai',         short: 'LLMs, RAG & Evals',  prefix: '03-' },
  { id: 'agents',     short: 'Agents',             prefix: '04-' },
  { id: 'inference',  short: 'Inference',          prefix: '05-' },
  { id: 'finetuning', short: 'Fine-tuning & ML',   prefix: '06-' },
  { id: 'llmops',     short: 'MLOps & LLMOps',     prefix: '07-' },
  { id: 'devops',     short: 'DevOps',             prefix: '08-' },
  { id: 'cloud',      short: 'Cloud & AWS',        prefix: '09-' },
];

const TAGS = ['Basics', 'Core', 'Advanced', 'Start here', 'New', 'Scenarios'];

marked.setOptions({
  gfm: true,
  breaks: false,
  headerIds: false,
  mangle: false,
  langPrefix: 'hljs language-',
  highlight(code, lang) {
    const l = (lang || '').toLowerCase();
    if (l && hljs.getLanguage(l)) {
      try { return hljs.highlight(code, { language: l, ignoreIllegals: true }).value; } catch { /* fall through */ }
    }
    return escapeHtml(code);
  },
});

function escapeHtml(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function md(src) {
  if (!src || !src.trim()) return '';
  let html = marked.parse(src.trim());
  html = html.replace(/<table>/g, '<div class="tbl"><table>').replace(/<\/table>/g, '</table></div>');
  html = html.replace(/<a href="(https?:[^"]+)"/g, '<a href="$1" target="_blank" rel="noopener"');
  return html;
}

function textOf(html) {
  return html.replace(/<[^>]+>/g, ' ').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/\s+/g, ' ').trim();
}

function slug(s) {
  return s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 60) || 'x';
}

function hash(s) {
  let h = 5381;
  for (let i = 0; i < s.length; i++) h = ((h << 5) + h + s.charCodeAt(i)) | 0;
  return (h >>> 0).toString(36);
}

function normalise(src) {
  return src
    .replace(/\r\n/g, '\n')
    .replace(/[—–]/g, '-')
    .replace(/[‘’]/g, "'")
    .replace(/[“”]/g, '"')
    .replace(/[ \t]+$/gm, '');
}

// Merge part files: keep H1 + intro of the first, drop H1 + leading blockquote of the rest.
function mergeFiles(files) {
  const out = [];
  files.forEach((f, i) => {
    let text = normalise(fs.readFileSync(f, 'utf8'));
    if (i > 0) {
      const lines = text.split('\n');
      let j = 0;
      while (j < lines.length && !lines[j].trim()) j++;
      if (lines[j] && /^# /.test(lines[j])) {
        j++;
        while (j < lines.length && !lines[j].trim()) j++;
        while (j < lines.length && /^>/.test(lines[j])) j++;
      }
      text = lines.slice(j).join('\n');
    }
    out.push(text);
  });
  return out.join('\n\n');
}

function splitTags(rawTitle) {
  let title = rawTitle.trim();
  const tags = [];
  let m;
  while ((m = title.match(/\s*\[([^\]]+)\]\s*$/)) && TAGS.includes(m[1])) {
    tags.unshift(m[1]);
    title = title.slice(0, m.index).trim();
  }
  return { title, tags };
}

// Split markdown into a raw tree: { title, intro[], sections: [{ title, tags, framing[], blocks: [{ heading, lines[] }] }] }
function parseRaw(source, fallbackTitle) {
  const lines = source.split('\n');
  let inFence = false, fenceMark = '';
  let title = fallbackTitle;
  const intro = [];
  const sections = [];
  let section = null;
  let block = null;
  const push = (line) => {
    if (block) block.lines.push(line);
    else if (section) section.framing.push(line);
    else intro.push(line);
  };
  for (const line of lines) {
    const fence = line.match(/^\s*(```+|~~~+)/);
    if (fence) {
      if (!inFence) { inFence = true; fenceMark = fence[1][0]; }
      else if (fence[1][0] === fenceMark) { inFence = false; }
      push(line); continue;
    }
    if (inFence) { push(line); continue; }
    if (/^# /.test(line)) { title = line.replace(/^# /, '').trim(); continue; }
    if (/^## /.test(line)) {
      block = null;
      const { title: t, tags } = splitTags(line.replace(/^## /, ''));
      section = { title: t, tags, framing: [], blocks: [] };
      sections.push(section);
      continue;
    }
    if (/^### /.test(line)) {
      if (!section) { section = { title: 'Overview', tags: [], framing: [], blocks: [] }; sections.push(section); }
      block = { heading: line.replace(/^### /, '').trim(), lines: [] };
      section.blocks.push(block);
      continue;
    }
    push(line);
  }
  return { title, intro, sections };
}

function blockType(heading) {
  if (/^Q\.\s*/i.test(heading)) return 'question';
  if (/^C\.\s*/i.test(heading)) return 'concept';
  if (/^concepts/i.test(heading)) return 'concepts';
  if (/^practice/i.test(heading)) return 'practice';
  if (/^in plain words/i.test(heading)) return 'plain';
  if (/^from your saved posts/i.test(heading)) return 'sources';
  if (/^diagram:/i.test(heading)) return 'diagram';
  if (/^why it exists/i.test(heading)) return 'purpose';
  if (/^walkthrough:/i.test(heading)) return 'walk';
  return 'free';
}

const TOP_TYPES = ['purpose', 'plain', 'sources', 'diagram'];

// A diagram block: raw ```svg fence(s) plus a markdown caption.
function renderDiagram(lines) {
  const text = lines.filter((l) => !/^\s*before:/i.test(l)).join('\n');
  const svgs = [];
  const caption = text.replace(/```svg\n([\s\S]*?)```/g, (_, svg) => { svgs.push(svg.trim()); return ''; });
  return { svg: svgs.join('\n'), caption: md(caption) };
}

// Apply overlay sections onto the raw tree.
function applyOverlay(raw, overlay) {
  const norm = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
  const front = [];
  for (const os of overlay.sections) {
    const target = raw.sections.find((s) => norm(s.title) === norm(os.title));
    if (target) {
      const top = os.blocks.filter((b) => TOP_TYPES.includes(blockType(b.heading)));
      const rest = os.blocks.filter((b) => !TOP_TYPES.includes(blockType(b.heading)));
      // top blocks go after any existing plain/sources/diagram blocks at the start
      let insertAt = 0;
      while (insertAt < target.blocks.length && TOP_TYPES.includes(blockType(target.blocks[insertAt].heading))) insertAt++;
      // a diagram whose first line is "before: <heading prefix>" goes right above that block
      const beforeOf = (b) => {
        const first = b.lines.map((l) => l.trim()).find((l) => l);
        const m = first && first.match(/^before:\s*(.+)$/i);
        return m ? m[1].toLowerCase() : null;
      };
      const anchored = top.filter(beforeOf);
      target.blocks.splice(insertAt, 0, ...top.filter((b) => !beforeOf(b)));
      for (const b of anchored) {
        const idx = target.blocks.findIndex((x) => x.heading.toLowerCase().startsWith(beforeOf(b)));
        if (idx === -1) {
          let at = 0;
          while (at < target.blocks.length && TOP_TYPES.includes(blockType(target.blocks[at].heading))) at++;
          target.blocks.splice(at, 0, b);
          console.warn(`  [overlay] "${b.heading}": no block starting "${beforeOf(b)}"; placed at top`);
        } else {
          target.blocks.splice(idx, 0, b);
        }
      }
      const practiceIdx = target.blocks.findIndex((b) => blockType(b.heading) === 'practice');
      if (practiceIdx === -1) target.blocks.push(...rest); else target.blocks.splice(practiceIdx, 0, ...rest);
      for (const t of os.tags) if (!target.tags.includes(t)) target.tags.push(t);
      if (!target.framing.join('').trim() && os.framing.join('').trim()) target.framing = os.framing;
    } else if (!os.blocks.length && !os.framing.join('').trim()) {
      console.warn(`  [overlay] no section titled "${os.title}" to tag; skipped`);
    } else if (os.tags.includes('Start here')) {
      front.push(os);
    } else {
      raw.sections.push(os);
    }
  }
  raw.sections.unshift(...front);
}

const Q_LABELS = [
  ['short',  /^\*\*Short answer[^*]*:\*\*\s*(.*)$/i],
  ['deep',   /^\*\*Deeper explanation:\*\*\s*(.*)$/i],
  ['follow', /^\*\*Follow-ups they will ask:\*\*\s*(.*)$/i],
  ['mist',   /^\*\*Mistakes to avoid:\*\*\s*(.*)$/i],
];
const C_LABELS = [
  ['line',    /^\*\*In one line:\*\*\s*(.*)$/i],
  ['like',    /^\*\*Think of it like:\*\*\s*(.*)$/i],
  ['example', /^\*\*Example:\*\*\s*(.*)$/i],
  ['say',     /^\*\*Say it in an interview:\*\*\s*(.*)$/i],
  ['deeper',  /^\*\*Go deeper:\*\*\s*(.*)$/i],
];

function splitLabels(lines, labels) {
  const parts = { lead: [] };
  for (const [k] of labels) parts[k] = [];
  let cur = 'lead';
  let inF = false;
  for (const ln of lines) {
    if (/^\s*(```|~~~)/.test(ln)) inF = !inF;
    if (!inF) {
      let matched = false;
      for (const [key, re] of labels) {
        const m = ln.match(re);
        if (m) { cur = key; if (m[1]) parts[key].push(m[1]); matched = true; break; }
      }
      if (matched) continue;
    }
    parts[cur].push(ln);
  }
  const rendered = {};
  for (const k of Object.keys(parts)) rendered[k] = md(parts[k].join('\n'));
  return rendered;
}

function renderTrack(track, raw) {
  let qCount = 0;
  // "Why it exists" always opens a section
  for (const s of raw.sections) {
    const purpose = s.blocks.filter((b) => blockType(b.heading) === 'purpose');
    if (purpose.length) s.blocks = purpose.concat(s.blocks.filter((b) => blockType(b.heading) !== 'purpose'));
  }
  const sections = raw.sections.map((s) => {
    const sid = slug(s.title);
    const blocks = s.blocks.map((b) => {
      let type = blockType(b.heading);
      if (type === 'question' && LEARN.has(track.id + '\t' + b.heading.replace(/^Q\.\s*/i, '').trim())) type = 'learn';
      const titleText = (type === 'question' || type === 'learn') ? b.heading.replace(/^Q\.\s*/i, '').trim()
        : type === 'concept' ? b.heading.replace(/^C\.\s*/i, '').trim()
        : b.heading;
      const id = `${track.id}-${hash(track.id + '|' + s.title + '|' + titleText)}`;
      if (type === 'learn') {
        const parts = splitLabels(b.lines, Q_LABELS);
        return { type, id, title: titleText, parts, text: textOf(Object.values(parts).join(' ')) };
      }
      if (type === 'question' || type === 'concept') {
        qCount++;
        const parts = splitLabels(b.lines, type === 'question' ? Q_LABELS : C_LABELS);
        if (type === 'question' && !parts.short && !parts.deep && parts.lead) { parts.deep = parts.lead; parts.lead = ''; }
        if (type === 'concept' && !parts.line && parts.lead) { parts.line = parts.lead; parts.lead = ''; }
        return { type, id, title: titleText, parts, text: textOf(Object.values(parts).join(' ')) };
      }
      if (type === 'diagram') {
        const { svg, caption } = renderDiagram(b.lines);
        return { type, id, title: titleText.replace(/^diagram:\s*/i, ''), svg, html: caption, text: textOf(caption) };
      }
      const html = md(b.lines.join('\n'));
      const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);
      const shown = type === 'walk' ? cap(titleText.replace(/^walkthrough:\s*/i, '')) : titleText;
      return { type, id, title: shown, html, text: textOf(html) };
    });
    return {
      id: sid,
      title: s.title,
      tags: s.tags,
      framing: md(s.framing.join('\n')),
      blocks,
      questions: blocks.filter((b) => b.type === 'question' || b.type === 'concept').length,
    };
  });
  return {
    id: track.id,
    short: track.short,
    kind: track.kind || 'track',
    title: raw.title,
    intro: md(raw.intro.join('\n')),
    sections,
    questions: qCount,
  };
}

function build() {
  const files = fs.readdirSync(CONTENT).filter((f) => f.endsWith('.md')).sort();
  const overlayFiles = fs.existsSync(OVERLAYS) ? fs.readdirSync(OVERLAYS).filter((f) => f.endsWith('.md')).sort() : [];
  const tracks = [];
  for (const t of TRACKS) {
    const own = files.filter((f) => f.startsWith(t.prefix)).map((f) => path.join(CONTENT, f));
    // content overlays first, diagram overlays last (diagrams anchor to blocks the others add)
    const isDg = (f) => (/diagram/.test(f) ? 1 : 0);
    const ovs = overlayFiles.filter((f) => f.startsWith(t.prefix))
      .sort((a, b) => isDg(a) - isDg(b) || a.localeCompare(b))
      .map((f) => path.join(OVERLAYS, f));
    if (!own.length) { console.warn(`[skip] no content for track ${t.id} (${t.prefix}*.md)`); continue; }
    const raw = parseRaw(mergeFiles(own), t.short);
    for (const o of ovs) applyOverlay(raw, parseRaw(normalise(fs.readFileSync(o, 'utf8')), ''));
    const parsed = renderTrack(t, raw);
    tracks.push(parsed);
    const src = own.map((p) => path.basename(p)).concat(ovs.map((p) => 'overlays/' + path.basename(p)));
    console.log(`[ok] ${t.id.padEnd(11)} ${String(parsed.sections.length).padStart(2)} sections ${String(parsed.questions).padStart(3)} cards  <- ${src.join(', ')}`);
  }
  const data = { generatedAt: new Date().toISOString().slice(0, 10), tracks };
  const json = JSON.stringify(data).replace(/<\//g, '<\\/').replace(/<!--/g, '<\\!--');
  const template = fs.readFileSync(TEMPLATE, 'utf8');
  if (!template.includes('__ATLAS_DATA__')) throw new Error('template is missing the __ATLAS_DATA__ placeholder');
  const html = template.replace('__ATLAS_DATA__', () => json);
  fs.mkdirSync(OUT_DIR, { recursive: true });
  fs.writeFileSync(OUT, html);
  const total = tracks.reduce((n, t) => n + t.questions, 0);
  console.log(`\nWrote ${OUT}  (${(html.length / 1024).toFixed(0)} KB, ${tracks.length} tracks, ${total} question and concept cards)`);
}

build();
