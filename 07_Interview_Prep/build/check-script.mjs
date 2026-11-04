// Syntax-check the page's own inline script (the last <script> block) and the embedded JSON.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const html = fs.readFileSync(path.join(ROOT, 'dist', 'atlas.html'), 'utf8');
const start = html.lastIndexOf('<script>');
const end = html.lastIndexOf('</script>');
const code = html.slice(start + 8, end);
new vm.Script(code, { filename: 'atlas-inline.js' });
const j0 = html.indexOf('<script type="application/json" id="atlas-data">');
const j1 = html.indexOf('</script>', j0);
const data = JSON.parse(html.slice(j0 + '<script type="application/json" id="atlas-data">'.length, j1));
const count = data.tracks.reduce((n, t) => n + t.questions, 0);
console.log(`script OK (${code.length} chars); data OK: ${data.tracks.length} tracks, ${count} cards; json closes at the right place: ${j1 > j0 && j1 < start}`);
