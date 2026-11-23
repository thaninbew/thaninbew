// Usage: node capture.mjs <card.html> <out.webp> <loopMs> [fps=25] [quality=85]
// EXTRA_CSS=<file> injects a stylesheet (e.g. _shell/hero-only.css); CLIP=1200x630 crops every frame from the top-left.
// KEEP_FRAMES=<dir> copies every frame PNG there for review.
// STILLS="0,2500,6000" env also saves those times as <out>.t<ms>.png.
// Seeks every CSS/WAAPI animation to each frame time; calls window.__frame?.(ms) first for JS-driven parts.
import { createRequire } from 'module';
import { execFileSync } from 'child_process';
import { mkdtempSync, readdirSync, rmSync, statSync } from 'fs';
import { tmpdir } from 'os';
import { join, resolve } from 'path';
const require = createRequire(import.meta.url);
const { chromium } = require(join(execFileSync('npm', ['root', '-g']).toString().trim(), 'playwright'));
const [html, out, loopArg, fpsArg = '25', qArg = '85'] = process.argv.slice(2);
const loop = +loopArg, fps = +fpsArg, n = Math.round(loop / 1000 * fps);
const dir = mkdtempSync(join(tmpdir(), 'card-frames-'));
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1200, height: 982 }, deviceScaleFactor: 1 });
page.on('console', m => m.type() === 'error' && console.error('page:', m.text()));
page.on('pageerror', e => console.error('pageerror:', e.message));
await page.goto('file://' + resolve(html));
if (process.env.EXTRA_CSS) await page.addStyleTag({ path: resolve(process.env.EXTRA_CSS) });
const [cw, ch] = (process.env.CLIP || '1200x982').split('x').map(Number);
const shot = { omitBackground: true, clip: { x: 0, y: 0, width: cw, height: ch } };
await page.evaluate(() => document.fonts.ready);
await page.evaluate(() => document.getAnimations().forEach(a => a.pause()));
for (let i = 0; i < n; i++) {
  const t = i * 1000 / fps;
  await page.evaluate(t => { window.__frame?.(t); document.getAnimations().forEach(a => { a.pause(); a.currentTime = t; }); }, t);
  await page.screenshot({ ...shot, path: join(dir, String(i).padStart(4, '0') + '.png') });
}
await browser.close();
const frames = readdirSync(dir).sort().map(f => join(dir, f));
// Every frame is a lossy keyframe: sub-frame blending accumulates lossy residue (ghosting) across the loop.
execFileSync('img2webp', ['-loop', '0', '-kmax', '0', '-lossy', '-exact', '-q', qArg, '-m', '4', '-d', String(Math.round(1000 / fps)), ...frames, '-o', out]);
execFileSync('cp', [frames[0], out.replace(/\.webp$/, '.first.png')]);
execFileSync('cp', [frames[Math.floor(n / 2)], out.replace(/\.webp$/, '.mid.png')]);
if (process.env.STILLS) {
  const b2 = await chromium.launch();
  const p2 = await b2.newPage({ viewport: { width: 1200, height: 982 }, deviceScaleFactor: 1 });
  await p2.goto('file://' + resolve(html));
  if (process.env.EXTRA_CSS) await p2.addStyleTag({ path: resolve(process.env.EXTRA_CSS) });
  await p2.evaluate(() => document.fonts.ready);
  for (const ms of process.env.STILLS.split(',').map(Number)) {
    await p2.evaluate(t => { window.__frame?.(t); document.getAnimations().forEach(a => { a.pause(); a.currentTime = t; }); }, ms);
    await p2.screenshot({ ...shot, path: out.replace(/\.webp$/, `.t${ms}.png`) });
  }
  await b2.close();
}
if (process.env.KEEP_FRAMES) execFileSync('cp', ['-R', dir + '/.', process.env.KEEP_FRAMES]);
rmSync(dir, { recursive: true });
console.log(JSON.stringify({ out, frames: n, fps, bytes: statSync(out).size }));
