// Cache-busts the locale scripts by stamping each <script src="locale/*.js">
// in index.html with a hash of that file's contents (?v=xxxxxxxxxx).
//
// Why: GitHub Pages serves everything with max-age=600, so right after a
// deploy a browser can pair the NEW index.html with a still-cached OLD
// locale/weddings.enc.js (or en/sk/cz.js) -- e.g. new markup expecting a
// string the old file doesn't have. A changed hash = a new URL = no stale copy.
//
// Usage (from the repo root): node tools/stamp-assets.mjs
// Run after editing any locale/*.js; encrypt-weddings.mjs runs it for you.
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

export function stampAssets(indexPath) {
  const root = dirname(indexPath);
  const html = readFileSync(indexPath, 'utf8');
  const out = html.replace(/(<script src=")(locale\/[\w.-]+\.js)(?:\?v=[\w]+)?(")/g, (m, pre, file, post) => {
    const full = join(root, file);
    if (!existsSync(full)) return m;
    const v = createHash('sha1').update(readFileSync(full)).digest('hex').slice(0, 10);
    return `${pre}${file}?v=${v}${post}`;
  });
  if (out !== html) writeFileSync(indexPath, out);
  return out !== html;
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  const index = join(dirname(fileURLToPath(import.meta.url)), '..', 'index.html');
  console.log(stampAssets(index) ? 'stamped locale script versions in index.html' : 'index.html already up to date');
}
