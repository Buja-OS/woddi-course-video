// Admin interface screenshots from the live site (desktop). Output: qa-out/*.png (encrypted before leaving the runner).
import { chromium } from 'playwright';
import fs from 'fs';
const SITE = 'https://woddiinstitute.com';
const E = process.env;
fs.mkdirSync('qa-out', { recursive: true });
const sum = [];
const b = await chromium.launch();
const ctx = await b.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1.5, locale: 'en-GB' });
await ctx.addInitScript(() => { try { localStorage.setItem('woddi_consent_v1', '1'); sessionStorage.setItem('woddi_push_later', '1'); } catch (e) {} });
const page = await ctx.newPage();
page.on('dialog', d => d.dismiss().catch(() => {}));
const shot = async (name, full = true) => { try { await page.screenshot({ path: 'qa-out/' + name + '.png', fullPage: full }); sum.push('shot ' + name); } catch (e) { sum.push('shot failed ' + name); } };
try {
  // version check
  const r = await fetch(SITE + '/js/woddi-cheer-v1.js'); const t = await r.text();
  sum.push('live site has v186e: ' + (r.ok && t.includes('Growth Points celebration') ? 'yes' : 'no'));
  // admin portal sign-in page (signed out)
  await page.goto(SITE + '/admin.html', { waitUntil: 'domcontentloaded' }); await page.waitForTimeout(3000); await shot('A00 Admin portal sign-in', false);
  // sign in
  await page.goto(SITE + '/index.html', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => window._sb && window._sb.auth, null, { timeout: 45000 });
  const res = await page.evaluate(async ([e, p]) => { const r = await window._sb.auth.signInWithPassword({ email: e, password: p }); return r.error ? r.error.message : 'ok'; }, [E.ADMIN_EMAIL, E.ADMIN_PW]);
  sum.push('admin sign-in: ' + res);
  // classic admin inside the main app
  await page.goto(SITE + '/', { waitUntil: 'domcontentloaded' }); await page.waitForTimeout(10000);
  await page.addStyleTag({ content: '#woddi-loc,#woddi-consent,#woddi-push-card{display:none!important}' }).catch(() => {});
  await shot('A01 Classic admin - dashboard');
  const tabs = await page.$$eval('.admin-sidebar [onclick], .sidebar [onclick*="setAdmin"], nav [onclick*="setAdminView"], [onclick*="setAdminView"]', els => [...new Set(els.map(e => e.getAttribute('onclick')))].slice(0, 20)).catch(() => []);
  sum.push('classic admin views: ' + tabs.length);
  let i = 2;
  for (const oc of tabs) {
    try {
      const label = await page.$eval(`[onclick="${oc.replace(/"/g, '\\"')}"]`, e => e.innerText.trim().split('\n')[0].slice(0, 40));
      await page.click(`[onclick="${oc.replace(/"/g, '\\"')}"]`, { timeout: 4000 }); await page.waitForTimeout(3500);
      await shot('A' + String(i++).padStart(2, '0') + ' Classic admin - ' + label.replace(/[^\w &-]+/g, '').trim());
    } catch (e) { sum.push('view failed ' + oc.slice(0, 40)); }
  }
  // operations dashboard
  await page.goto(SITE + '/ops.html', { waitUntil: 'domcontentloaded' }); await page.waitForTimeout(9000);
  const secs = await page.$$eval('button.nav[data-s]', els => els.map(e => [e.getAttribute('data-s'), e.innerText.trim()]));
  let j = 1;
  for (const [s, label] of secs) {
    await page.click('button.nav[data-s="' + s + '"]'); await page.waitForTimeout(5500);
    await shot('B' + String(j++).padStart(2, '0') + ' Operations - ' + label.replace(/[^\w &-]+/g, '').trim());
  }
  // member activation
  await page.goto(SITE + '/admin-activation.html', { waitUntil: 'domcontentloaded' }); await page.waitForTimeout(9000);
  await shot('C01 Member activation');
  const at = await page.$$eval('[onclick*="showTab"], [data-tab], .tab-btn, .tabs button', els => els.map((e, k) => k)).catch(() => []);
  let k = 2;
  for (const n of at.slice(0, 12)) {
    try { const el = (await page.$$('[onclick*="showTab"], [data-tab], .tab-btn, .tabs button'))[n]; const label = (await el.innerText()).trim().split('\n')[0].slice(0, 40); await el.click({ timeout: 3000 }); await page.waitForTimeout(3000); await shot('C' + String(k++).padStart(2, '0') + ' Member activation - ' + label.replace(/[^\w &-]+/g, '').trim()); } catch (e) {}
  }
} catch (e) { sum.push('FATAL ' + e.message.slice(0, 150)); }
await b.close();
fs.writeFileSync('qa-summary.txt', sum.join('\n') + '\n');
