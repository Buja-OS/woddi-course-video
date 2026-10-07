/* Render transparent 854x480 overlay PNGs for one video from a JSON job:
   {lang, items:[{id, kind:'label'|'banner'|'step'|'card'|'title'|'end'|'photo', ...}]}
   Usage: node overlays.js job.json outdir */
'use strict';
const fs = require('fs'), path = require('path');
const { chromium } = require(process.env.WODDI_PW || 'playwright');
const NM = process.env.WODDI_NM || path.join(__dirname, '..', 'node', 'node_modules', '@fontsource');
const b64 = f => fs.readFileSync(f).toString('base64');
const face = (fam, file, w) => `@font-face{font-family:${fam};font-weight:${w};src:url(data:font/woff2;base64,${b64(file)}) format('woff2')}`;
const F = [];
for (const w of [400, 700, 800]) {
  F.push(face('NS', `${NM}/noto-sans/files/noto-sans-latin-${w}-normal.woff2`, w));
  F.push(face('NSX', `${NM}/noto-sans/files/noto-sans-latin-ext-${w}-normal.woff2`, w));
  const v = `${NM}/noto-sans/files/noto-sans-vietnamese-${w}-normal.woff2`; if (fs.existsSync(v)) F.push(face('NSV', v, w));
  const c = `${NM}/noto-sans/files/noto-sans-latin-ext-${w}-normal.woff2`;
}
for (const w of [400, 700]) F.push(face('NSA', `${NM}/noto-sans-arabic/files/noto-sans-arabic-arabic-${w}-normal.woff2`, w));
const LOGO = 'data:image/jpeg;base64,' + b64(path.join(__dirname, 'logo.jpg'));
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const CSS = F.join('') + `
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:854px;height:480px;background:transparent;overflow:hidden}
body{font-family:NS,NSX,NSV,NSA,sans-serif;color:#1F1A1D;position:relative}
.rtl{direction:rtl}
.label{position:absolute;left:26px;bottom:30px;max-width:520px;background:rgba(255,255,255,.94);border-radius:12px;padding:9px 18px 10px 16px;
  font-weight:700;font-size:21px;line-height:1.2;box-shadow:0 6px 22px rgba(0,0,0,.22);border-left:6px solid #D4006A}
.rtl .label{left:auto;right:26px;border-left:0;border-right:6px solid #D4006A;padding:9px 16px 10px 18px}
.banner{position:absolute;left:50%;transform:translateX(-50%);top:20px;max-width:760px;background:#D4006A;color:#fff;border-radius:12px;
  padding:9px 18px 10px 14px;font-weight:800;font-size:20px;line-height:1.25;display:flex;gap:10px;align-items:center;box-shadow:0 8px 24px rgba(120,0,60,.35);white-space:nowrap}
.banner svg{flex:0 0 26px}
.step{position:absolute;left:26px;top:22px;background:#7CB518;color:#fff;border-radius:999px;padding:6px 16px;font-weight:800;font-size:18px;box-shadow:0 6px 18px rgba(0,0,0,.2)}
.rtl .step{left:auto;right:26px}
.card{position:absolute;right:22px;top:50%;transform:translateY(-50%);width:340px;background:rgba(255,255,255,.96);border-radius:16px;padding:16px 18px 14px;
  box-shadow:0 12px 34px rgba(0,0,0,.28)}
.rtl .card{right:auto;left:22px}
.card h4{font-size:19px;font-weight:800;color:#D4006A;margin-bottom:8px;line-height:1.2}
.card .r{display:flex;justify-content:space-between;gap:12px;padding:6px 0;border-bottom:1px solid #EFE3DA;font-size:16.5px;line-height:1.25}
.card .r:last-of-type{border-bottom:0}
.card .r b{font-weight:800;white-space:nowrap}
.card .n{margin-top:8px;font-size:13px;color:#6B5E63;line-height:1.3}
.title{position:absolute;left:30px;bottom:34px;right:200px}
.rtl .title{left:200px;right:30px}
.title .k{display:inline-flex;align-items:center;gap:10px;background:#D4006A;color:#fff;font-weight:800;font-size:15px;padding:5px 12px 5px 6px;border-radius:999px;margin-bottom:10px}
.title .k img{width:26px;height:26px;border-radius:7px;background:#fff}
.title h1{font-size:34px;font-weight:800;line-height:1.12;color:#fff;text-shadow:0 2px 14px rgba(0,0,0,.55)}
.title .c{margin-top:8px;font-size:16px;font-weight:700;color:#fff;opacity:.95;text-shadow:0 2px 10px rgba(0,0,0,.6)}
.shade{position:absolute;inset:0;background:linear-gradient(0deg,rgba(0,0,0,.6) 0%,rgba(0,0,0,.15) 45%,rgba(0,0,0,0) 70%)}
.end{position:absolute;inset:0;background:rgba(255,248,251,.94);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px;text-align:center;padding:40px}
.end img{width:96px;height:96px;border-radius:22px;box-shadow:0 10px 30px rgba(212,0,106,.3)}
.end b{font-size:26px;font-weight:800;color:#D4006A}
.end span{font-size:17px;font-weight:700;color:#4A3F44;max-width:640px;line-height:1.35}
.photo{position:absolute;right:24px;top:24px;width:300px;background:#fff;border-radius:12px;padding:8px 8px 6px;box-shadow:0 12px 34px rgba(0,0,0,.3);transform:rotate(1.2deg)}
.rtl .photo{right:auto;left:24px;transform:rotate(-1.2deg)}
.photo img{width:100%;height:190px;object-fit:cover;border-radius:7px;display:block}
.photo .t{font-size:13px;font-weight:800;margin:6px 2px 1px}
.photo .cr{font-size:9.5px;color:#6B5E63;margin:0 2px}
.bug{position:absolute;right:16px;top:14px;width:34px;height:34px;border-radius:9px;opacity:.85}
.rtl .bug{right:auto;left:16px}
`;
const WARN = '<svg viewBox="0 0 24 24" width="26" height="26"><path fill="#fff" d="M12 2 1 21h22L12 2zm0 4.5 7.5 13h-15L12 6.5zM11 10v5h2v-5h-2zm0 6v2h2v-2h-2z"/></svg>';
function body(it) {
  switch (it.kind) {
    case 'label': return `<div class="label">${esc(it.text)}</div>`;
    case 'banner': return `<div class="banner">${WARN}<span>${esc(it.text)}</span></div>`;
    case 'step': return `<div class="step">${esc(it.text)}</div>`;
    case 'card': return `<div class="card"><h4>${esc(it.title)}</h4>${(it.rows || []).map(r => `<div class="r"><span>${esc(r[0])}</span><b>${esc(r[1])}</b></div>`).join('')}${it.note ? `<div class="n">${esc(it.note)}</div>` : ''}</div>`;
    case 'title': return `<div class="shade"></div><div class="title"><div class="k"><img src="${LOGO}">${esc(it.kicker)}</div><h1>${esc(it.text)}</h1><div class="c">${esc(it.course)}</div></div>`;
    case 'end': return `<div class="end"><img src="${LOGO}"><b>WODDI Institute</b><span>${esc(it.text)}</span></div>`;
    case 'photo': return `<div class="photo"><img src="data:image/jpeg;base64,${b64(it.src)}"><div class="t">${esc(it.title)}</div><div class="cr">${esc(it.credit)}</div></div>`;
    case 'bug': return `<img class="bug" src="${LOGO}">`;
  }
  return '';
}
(async () => {
  const job = JSON.parse(fs.readFileSync(process.argv[2], 'utf8')); const out = process.argv[3];
  fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch(fs.existsSync('/opt/pw-browsers/chromium') ? { executablePath: '/opt/pw-browsers/chromium' } : {}); const p = await b.newPage({ viewport: { width: 854, height: 480 } });
  for (const it of job.items) {
    await p.setContent(`<!doctype html><html><head><meta charset="utf-8"><style>${CSS}</style></head><body class="${job.rtl ? 'rtl' : ''}" dir="${job.rtl ? 'rtl' : 'ltr'}">${body(it)}</body></html>`);
    await p.evaluate(() => document.fonts.ready);
    // shrink long single-line banners/labels to fit
    await p.evaluate(() => { for (const el of document.querySelectorAll('.banner,.title h1,.label')) { let fs = parseFloat(getComputedStyle(el).fontSize); while (el.getBoundingClientRect().width > 800 && fs > 13) { fs -= 1; el.style.fontSize = fs + 'px'; } } });
    await p.screenshot({ path: path.join(out, it.id + '.png'), omitBackground: true });
  }
  await b.close();
})();
