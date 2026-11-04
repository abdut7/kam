// Validate content/*.md against CONTENT_FORMAT.md. Usage: node build/validate.mjs [file...]
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const CONTENT = path.join(ROOT, 'content');
const files = process.argv.slice(2).length
  ? process.argv.slice(2)
  : fs.readdirSync(CONTENT).filter((f) => f.endsWith('.md')).sort().map((f) => path.join(CONTENT, f));

const LABELS = ['**Short answer', '**Deeper explanation:**', '**Follow-ups they will ask:**', '**Mistakes to avoid:**'];
let problems = 0;

for (const file of files) {
  const src = fs.readFileSync(file, 'utf8');
  const lines = src.split('\n');
  const issues = [];
  let inFence = false;
  let h1 = 0, h2 = 0, q = 0, concepts = 0, practice = 0, otherH3 = 0, h4 = 0, html = 0, dashes = 0, fenceNoLang = 0;
  const sections = [];
  let cur = null;       // current section
  let qBlock = null;    // current question block {title, lines}
  const closeQ = () => {
    if (!qBlock) return;
    const body = qBlock.lines.join('\n');
    const need = qBlock.concept ? ['**In one line:**', '**Think of it like:**', '**Example:**', '**Say it in an interview:**'] : LABELS;
    const missing = need.filter((l) => !body.includes(l));
    const words = body.split(/\s+/).filter(Boolean).length;
    if (missing.length) issues.push(`${qBlock.concept ? 'C' : 'Q'} "${qBlock.title.slice(0, 60)}" missing labels: ${missing.join(', ')}`);
    if (!qBlock.concept && words < 120) issues.push(`Q "${qBlock.title.slice(0, 60)}" is short (${words} words)`);
    if (words > 650) issues.push(`Q "${qBlock.title.slice(0, 60)}" is long (${words} words)`);
    qBlock = null;
  };
  lines.forEach((line, i) => {
    const fence = line.match(/^\s*(```+|~~~+)\s*(\S*)/);
    if (fence) {
      if (!inFence) { inFence = true; if (!fence[2]) fenceNoLang++; } else inFence = false;
      if (qBlock) qBlock.lines.push(line);
      return;
    }
    if (inFence) { if (qBlock) qBlock.lines.push(line); return; }
    if (/[—–]/.test(line)) dashes++;
    if (/<[a-zA-Z][^>]*>/.test(line) && !/`[^`]*<[^`]*`/.test(line)) html++;
    if (/^# /.test(line)) { h1++; return; }
    if (/^## /.test(line)) { closeQ(); h2++; cur = { title: line.slice(3).trim(), q: 0, concepts: 0, practice: 0 }; sections.push(cur); return; }
    if (/^### /.test(line)) {
      closeQ();
      const h = line.slice(4).trim();
      if (/^Q\. /.test(h)) { q++; if (cur) cur.q++; qBlock = { title: h.slice(3), lines: [] }; }
      else if (/^C\. /.test(h)) { q++; if (cur) cur.q++; qBlock = { title: h.slice(3), lines: [], concept: true }; }
      else if (/^(in plain words|from your saved posts|why it exists)$/i.test(h) || /^(diagram|walkthrough):/i.test(h)) { /* allowed */ }
      else if (/^concepts you must understand$/i.test(h)) { concepts++; if (cur) cur.concepts++; }
      else if (/^practice$/i.test(h)) { practice++; if (cur) cur.practice++; }
      else { otherH3++; if (!path.basename(file).startsWith('00-')) issues.push(`line ${i + 1}: unexpected H3 "${h}"`); }
      return;
    }
    if (/^#{4,} /.test(line)) { h4++; issues.push(`line ${i + 1}: H4+ heading not allowed`); return; }
    if (qBlock) qBlock.lines.push(line);
  });
  closeQ();
  const isGuide = /^(00|10|13)-/.test(path.basename(file)) || file.includes('/overlays/');
  if (!isGuide) {
    for (const s of sections) {
      if (s.concepts !== 1) issues.push(`section "${s.title}" has ${s.concepts} Concepts blocks`);
      if (s.practice !== 1) issues.push(`section "${s.title}" has ${s.practice} Practice blocks`);
      if (s.q < (/^1[124]-/.test(path.basename(file)) ? 4 : 5)) issues.push(`section "${s.title}" has only ${s.q} questions`);
    }
  }
  if (h1 !== 1 && !/[a-z][0-9]\.md$/.test(file) && !file.includes('/overlays/')) issues.push(`${h1} H1 headings (expected 1)`);
  if (dashes) issues.push(`${dashes} lines contain em/en dashes (build will replace them)`);
  if (html) issues.push(`${html} lines look like raw HTML`);
  if (fenceNoLang) issues.push(`${fenceNoLang} code fences without a language tag`);
  const words = src.split(/\s+/).filter(Boolean).length;
  const status = issues.length ? 'ISSUES' : 'ok';
  console.log(`${path.basename(file).padEnd(20)} ${status.padEnd(6)} sections=${String(h2).padStart(2)} questions=${String(q).padStart(3)} words=${String(words).padStart(6)}`);
  for (const s of sections) console.log(`    - ${s.title.padEnd(48)} q=${String(s.q).padStart(2)} c=${s.concepts} p=${s.practice}`);
  for (const m of issues) { console.log(`    ! ${m}`); problems++; }
}
console.log(problems ? `\n${problems} issue(s) found` : '\nAll files pass');
