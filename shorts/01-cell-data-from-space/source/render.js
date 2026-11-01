const { chromium } = require('playwright');
const fs = require('fs');
// usage: node render.js outdir t1,t2,...  |  node render.js outdir --range start end fps
(async () => {
  const out = process.argv[2]; fs.mkdirSync(out, { recursive: true });
  let times = [];
  if (process.argv[3] === '--range') { const [s, e, fps] = process.argv.slice(4).map(Number); for (let f = s; f < e; f++) times.push([f, f / fps]); }
  else times = process.argv[3].split(',').map((x, i) => [x, Number(x)]);
  const b = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  p.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') console.log('PAGE', m.type(), m.text().slice(0, 300)); });
  p.on('pageerror', e => console.log('PAGEERR', e.message));
  await p.goto('http://127.0.0.1:8765/scene.html');
  await p.waitForFunction('window.READY === true', null, { timeout: 180000 });
  const T = await p.evaluate(() => window.TIMES);
  const mb = (t) => (t > T.tNum - 0.3 && t < T.tNum + 0.9) ? 6 : 1;
  for (const [name, t] of times) {
    const t0 = Date.now();
    const url = await p.evaluate(([t, s]) => window.renderFrame(t, s), [t, mb(t)]);
    fs.writeFileSync(`${out}/${typeof name === 'number' ? String(name).padStart(5, '0') : name}.jpg`, Buffer.from(url.split(',')[1], 'base64'));
    if (times.length < 40 || Math.random() < 0.05) console.log('frame', name, ((Date.now() - t0) / 1000).toFixed(2) + 's');
  }
  await b.close();
})();
