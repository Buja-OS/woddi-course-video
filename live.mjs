import { chromium } from 'playwright';
import fs from 'fs';
fs.mkdirSync('shots', { recursive: true });
const b = await chromium.launch();
for (const [name, w, h, light] of [['desk-light', 1920, 960, true], ['desk-dark', 1920, 960, false], ['mob-light', 390, 844, true]]) {
  const p = await b.newPage({ viewport: { width: w, height: h } });
  p.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') console.log(name, 'console', m.type(), m.text().slice(0, 300)); });
  p.on('pageerror', e => console.log(name, 'PAGEERROR', e.message));
  p.on('requestfailed', r => console.log(name, 'FAILED', r.url().slice(0, 160), r.failure() && r.failure().errorText));
  p.on('response', r => { if (r.status() >= 400) console.log(name, 'HTTP', r.status(), r.url().slice(0, 160)); });
  await p.goto('https://woddiinstitute.com/?nocache=' + Date.now(), { waitUntil: 'networkidle', timeout: 60000 }).catch(e => console.log('goto', e.message));
  await p.waitForTimeout(3000);
  if (light) { await p.evaluate(() => { try { localStorage.setItem('woddi_theme_user_set', '1'); if (AppState.theme === 'dark') toggleTheme(); } catch (e) {} }); await p.waitForTimeout(500); }
  console.log(name, 'scripts', await p.evaluate(() => [...document.scripts].map(s => s.src).filter(s => /auth|landing|version/.test(s)).join(' ')));
  await p.screenshot({ path: `shots/${name}-0.png` });
  const btn = await p.$('#landing .lp-actions .lp-btn.ghost') || await p.$('text=Sign in');
  if (btn && await btn.isVisible()) await btn.click(); else await p.evaluate(() => openAuth('signin'));
  await p.waitForTimeout(1500);
  await p.screenshot({ path: `shots/${name}-1.png` });
  console.log(name, 'modal', await p.evaluate(() => { const m = document.getElementById('auth-modal'); const bx = document.getElementById('auth-box');
    if (!bx) return 'no box; modal html len ' + (m ? m.innerHTML.length : -1) + ' class ' + (m && m.className);
    const r = bx.getBoundingClientRect(); const cs = getComputedStyle(bx);
    const top = document.elementFromPoint(r.x + r.width / 2, r.y + 100);
    return JSON.stringify({ r: [r.x, r.y, r.width, r.height], op: cs.opacity, vis: cs.visibility, disp: cs.display, anim: cs.animationName, tr: cs.transform, top: top && (top.id || top.className || top.tagName), mz: getComputedStyle(m).zIndex });
  }));
  await p.close();
}
await b.close();
