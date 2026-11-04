// Tiny static server for previewing dist/ (absolute paths, no cwd dependency)
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const DIST = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', 'dist');
const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.md': 'text/plain; charset=utf-8' };
http.createServer((req, res) => {
  let p = decodeURIComponent((req.url || '/').split('?')[0]);
  if (p === '/' || p === '') p = '/atlas.html';
  const file = path.join(DIST, path.normalize(p));
  if (!file.startsWith(DIST) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) { res.writeHead(404); res.end('not found'); return; }
  res.writeHead(200, { 'content-type': TYPES[path.extname(file)] || 'application/octet-stream', 'cache-control': 'no-store' });
  if (path.extname(file) === '.html') {
    // mimic the artifact publish skeleton (doctype + metas) so the preview renders in standards mode
    res.write('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"><style>[hidden]{display:none!important}body{margin:0;font:14px system-ui}</style></head><body>');
    fs.createReadStream(file).on('end', () => res.end('</body></html>')).pipe(res, { end: false });
    return;
  }
  fs.createReadStream(file).pipe(res);
}).listen(5173, '127.0.0.1', () => console.log('serving', DIST, 'on http://127.0.0.1:5173'));
