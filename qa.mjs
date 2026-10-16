// Live QA of woddiinstitute.com (admin + learner). Writes qa-out/ (encrypted later) and qa-summary.txt (counts only).
import { chromium } from 'playwright';
import fs from 'fs';
const SITE = 'https://woddiinstitute.com';
const SB = 'https://cmwhxfaskxsttvjvcijv.supabase.co';
const ANON = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNtd2h4ZmFza3hzdHR2anZjaWp2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTIxMDQwNjQsImV4cCI6MjEwNzY4MDA2NH0.A2kjgE-UnmX8ebzM2qqSXSCZHtmgN4BsiBTMGKVtzBw';
const E = process.env;
fs.mkdirSync('qa-out', { recursive: true });
const report = { pages: [], functions: {}, anon: {}, notes: [] };
const summary = [];
const strip = u => { try { const x = new URL(u); return x.origin + x.pathname; } catch (e) { return String(u).split('?')[0]; } };
const IGNORE = /google-analytics|googletagmanager|doubleclick|facebook|fonts\.g|gstatic|clarity\.ms|favicon/;

function watch(page, bucket) {
  page.on('console', m => { if (m.type() === 'error') bucket.console.push(m.text().slice(0, 400)); });
  page.on('pageerror', e => bucket.pageerrors.push(String(e && e.message || e).slice(0, 400)));
  page.on('response', r => { const s = r.status(); if (s >= 400 && !IGNORE.test(r.url())) bucket.http.push(s + ' ' + r.request().method() + ' ' + strip(r.url())); });
  page.on('requestfailed', r => { if (!IGNORE.test(r.url())) bucket.failed.push((r.failure() && r.failure().errorText) + ' ' + strip(r.url())); });
}
function newBucket(name) { const b = { name, console: [], pageerrors: [], http: [], failed: [], text: '' }; report.pages.push(b); return b; }
async function shot(page, name) { try { await page.screenshot({ path: 'qa-out/' + name + '.png', fullPage: false }); } catch (e) {} }

async function login(b, email, pw, label) {
  const ctx = await b.newContext({ viewport: { width: 1366, height: 900 }, locale: 'en-GB' });
  const page = await ctx.newPage();
  const bk = newBucket(label + ': sign-in');
  watch(page, bk);
  await page.goto(SITE + '/index.html', { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForFunction(() => window._sb && window._sb.auth, null, { timeout: 45000 });
  const res = await page.evaluate(async ([e, p]) => { const r = await window._sb.auth.signInWithPassword({ email: e, password: p }); return r.error ? 'ERR ' + r.error.message : 'ok'; }, [email, pw]);
  bk.text = 'sign-in: ' + res;
  summary.push(label + ' sign-in: ' + (res === 'ok' ? 'ok' : 'FAILED'));
  const tok = await page.evaluate(async () => { const s = await window._sb.auth.getSession(); return s && s.data && s.data.session && s.data.session.access_token; });
  return { ctx, page, tok };
}

async function visit(ctx, url, label, opts = {}) {
  const page = await ctx.newPage();
  const bk = newBucket(label); watch(page, bk);
  try {
    await page.goto(SITE + url, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(opts.wait || 9000);
    bk.text = (await page.evaluate(() => document.body.innerText)).slice(0, 3000);
    await shot(page, label.replace(/[^a-z0-9]+/gi, '_'));
  } catch (e) { bk.pageerrors.push('visit failed: ' + e.message); }
  return { page, bk };
}

async function fn(name, path, init) {
  try {
    const r = await fetch(SITE + path, init);
    const t = (await r.text()).slice(0, 600);
    report.functions[name] = { status: r.status, body: t };
    summary.push('function ' + name + ': ' + r.status);
  } catch (e) { report.functions[name] = { error: e.message }; summary.push('function ' + name + ': error'); }
}

const b = await chromium.launch();
try {
  /* 1) anonymous exposure check: can the public key read learners' contact details? */
  {
    const r = await fetch(SB + '/rest/v1/users?select=email,phone_number&limit=5', { headers: { apikey: ANON, Authorization: 'Bearer ' + ANON } });
    const j = r.ok ? await r.json() : [];
    const n = Array.isArray(j) ? j.filter(x => x && (x.email || x.phone_number)).length : 0;
    report.anon.users_contact_rows_visible = n; report.anon.status = r.status;
    summary.push('anonymous can read learner emails/phones: ' + (n > 0 ? 'YES (' + n + ' of 5 sampled)' : 'no') + ' [status ' + r.status + ']');
  }

  /* 2) learner */
  const L = await login(b, E.STU_EMAIL, E.STU_PW, 'learner');
  await L.page.waitForTimeout(6000);
  {
    const bk = report.pages[report.pages.length - 1];
    bk.text = bk.text + '\n' + (await L.page.evaluate(() => document.body.innerText)).slice(0, 2000);
    await shot(L.page, 'learner_home');
  }
  await visit(L.ctx, '/index.html#points', 'learner: growth points', { wait: 8000 });
  await L.page.evaluate(() => localStorage.setItem('woddi_lang', 'fr'));
  const course = await visit(L.ctx, '/course-core-skill.html?id=core-scam-awareness-and-digital-trust', 'learner: course page in French', { wait: 9000 });
  try {
    const btn = await course.page.$('[data-action="resume"]');
    if (btn) { await btn.click(); await course.page.waitForTimeout(6000); }
    const t = await course.page.evaluate(() => { const L = document.querySelector('.v3-lesson'); return L ? L.innerText.slice(0, 800) : ''; });
    course.bk.text += '\n--- lesson ---\n' + t;
    const fr = /\b(le|la|les|des|une|est|vous|pour)\b/i.test(t), en = /\b(the|and|you|your|every|scam)\b/i.test(t);
    summary.push('course lesson text language: ' + (fr && !en ? 'French' : fr && en ? 'mixed French/English' : 'English'));
    await shot(course.page, 'learner_course_fr_lesson');
  } catch (e) { course.bk.pageerrors.push('lesson: ' + e.message); }
  await fn('mentor-voice (needs Netlify SUPABASE_URL on the new project)', '/.netlify/functions/mentor-voice', { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + L.tok }, body: JSON.stringify({ action: 'speak', text: 'Well done, Amina! You have earned 10 Growth Points.', language: 'en' }) });
  await fn('mentor-chat health', '/.netlify/functions/mentor-chat?health=1', {});
  await fn('translation pack (/i18n, new in v186e)', '/i18n/fr/_catalog.json', {});
  if (E.CERT) await fn('verify page', '/verify/' + E.CERT, {});
  {
    const r = await fetch(SB + '/rest/v1/rpc/my_points', { method: 'POST', headers: { apikey: ANON, Authorization: 'Bearer ' + L.tok, 'Content-Type': 'application/json' }, body: '{}' });
    summary.push('my_points for learner: ' + r.status);
  }
  await L.ctx.close();

  /* 3) admin */
  const A = await login(b, E.ADMIN_EMAIL, E.ADMIN_PW, 'admin');
  await A.page.goto(SITE + '/', { waitUntil: 'domcontentloaded' }); await A.page.waitForTimeout(10000);
  {
    const bk = newBucket('admin: main app'); watch(A.page, bk);
    bk.text = (await A.page.evaluate(() => document.body.innerText)).slice(0, 3000);
    await shot(A.page, 'admin_main');
    // click through the admin sidebar items in the main app, if present
    const items = await A.page.$$eval('[onclick*="adminTab"], [data-admin-tab], .admin-nav button, .admin-sidebar button, .admin-tabs button', els => els.map((e, i) => i)).catch(() => []);
    bk.text += '\nadmin nav items found: ' + items.length;
  }
  for (const [path, label] of [['/ops.html', 'admin: operations dashboard'], ['/admin-activation.html', 'admin: member activation'], ['/admin.html', 'admin: admin portal page']]) {
    const v = await visit(A.ctx, path, label, { wait: 10000 });
    if (path === '/ops.html') {
      const sections = await v.page.$$eval('button.nav[data-s]', els => els.map(e => e.getAttribute('data-s'))).catch(() => []);
      v.bk.text += '\nsections: ' + sections.join(',');
      for (const s of sections) {
        const bk = newBucket('ops section: ' + s); watch(v.page, bk);
        try {
          await v.page.click('button.nav[data-s="' + s + '"]'); await v.page.waitForTimeout(5000);
          bk.text = (await v.page.evaluate(() => (document.querySelector('main') || document.body).innerText)).slice(0, 1500);
          await shot(v.page, 'ops_' + s);
        } catch (e) { bk.pageerrors.push('click: ' + e.message); }
      }
    }
  }
  await fn('ops-analytics (admin)', '/.netlify/functions/ops-analytics', { headers: { Authorization: 'Bearer ' + A.tok } });
  await fn('staff-access (admin)', '/.netlify/functions/staff-access', { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + A.tok }, body: JSON.stringify({ action: 'list' }) });
  await fn('support-desk (admin)', '/.netlify/functions/support-desk', { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + A.tok }, body: JSON.stringify({ action: 'list' }) });
  await A.ctx.close();
} catch (e) {
  report.notes.push('fatal: ' + e.message); summary.push('FATAL ' + e.message.slice(0, 160));
} finally {
  await b.close();
}
for (const p of report.pages) {
  const bad = p.console.length + p.pageerrors.length + p.http.length + p.failed.length;
  summary.push(p.name + ': console ' + p.console.length + ', script errors ' + p.pageerrors.length + ', http errors ' + p.http.length + ', failed requests ' + p.failed.length + (bad ? '' : ' (clean)'));
}
fs.writeFileSync('qa-out/report.json', JSON.stringify(report, null, 1));
fs.writeFileSync('qa-summary.txt', summary.join('\n') + '\n');
