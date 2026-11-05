const { chromium } = require('playwright'); const fs = require('fs');
(async () => {
  const out = process.argv[2]; fs.mkdirSync(out, { recursive: true }); let times = [];
  if (process.argv[3] === '--range') { const [s, e, fps] = process.argv.slice(4).map(Number); for (let f = s; f < e; f++) times.push([String(f).padStart(5, '0'), f / fps]); }
  else times = process.argv[3].split(',').map(x => [x, Number(x)]);
  const b = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  p.on('console', m => { if (m.type() === 'error') console.log('PAGE', m.text().slice(0, 300)); });
  p.on('pageerror', e => console.log('PAGEERR', e.message));
  await p.goto('http://127.0.0.1:8769/sharks.html'); await p.waitForFunction('window.READY === true', null, { timeout: 600000 });
  for (const [name, t] of times) { if (fs.existsSync(`${out}/${name}.jpg`) && fs.statSync(`${out}/${name}.jpg`).size > 10000) continue; const t0 = Date.now(); const url = await p.evaluate(t => window.renderFrame(t), t); fs.writeFileSync(`${out}/${name}.jpg`, Buffer.from(url.split(',')[1], 'base64')); if (times.length < 40) console.log('frame', name, ((Date.now() - t0) / 1000).toFixed(2) + 's'); }
  await b.close();
})();
