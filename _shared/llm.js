/* WODDI shared AI helper (v179).
   generate()   text answers. Tries every configured provider in turn until one answers:
                  1. Google Gemini   (GEMINI_API_KEY)  models: GEMINI_MODEL, gemini-2.5-flash, gemini-flash-latest, gemini-2.5-flash-lite
                  2. OpenAI          (OPENAI_API_KEY)  models: OPENAI_MODEL, gpt-4.1-mini, gpt-4o-mini
                  3. Hugging Face    (HF_TOKEN)        model:  HF_MODEL or meta-llama/Llama-3.3-70B-Instruct
   speak()      a natural female voice for the mentor (Gemini TTS, then OpenAI TTS). Returns audio bytes.
   transcribe() turns a short voice recording into text (Gemini, then OpenAI).
   Why the order changed in v179: gemini-flash-latest now points at a model that "thinks" before answering,
   which made answers take 8 seconds and pushed the mentor past Netlify's 10 second limit. gemini-2.5-flash
   with thinking switched off answers in 2 to 4 seconds. A retired or busy model still just moves to the next.
   Every call runs inside a time budget so the Netlify function always returns before its own timeout. */
'use strict';

const GEMINI_BASE = 'https://generativelanguage.googleapis.com/v1beta/models/';
const OPENAI_URL = 'https://api.openai.com/v1/chat/completions';
const HF_URL = 'https://router.huggingface.co/v1/chat/completions';
const edge = require('./edge-tts.js');

function uniq(a) { return a.filter((x, i) => x && a.indexOf(x) === i); }

function providers(fast) {
  const out = [];
  const gm = fast ? ['gemini-2.5-flash-lite', process.env.GEMINI_MODEL, 'gemini-2.5-flash', 'gemini-flash-lite-latest', 'gemini-flash-latest']
                  : [process.env.GEMINI_MODEL, 'gemini-2.5-flash', 'gemini-2.5-flash-lite', 'gemini-flash-latest', 'gemini-flash-lite-latest'];
  if (process.env.GEMINI_API_KEY) out.push({ id: 'gemini', models: uniq(gm) });
  if (process.env.OPENAI_API_KEY) out.push({ id: 'openai', models: uniq(fast ? ['gpt-4o-mini', process.env.OPENAI_MODEL, 'gpt-4.1-mini'] : [process.env.OPENAI_MODEL, 'gpt-4.1-mini', 'gpt-4o-mini']) });
  if (process.env.HF_TOKEN) out.push({ id: 'hf', models: uniq([process.env.HF_MODEL, 'meta-llama/Llama-3.3-70B-Instruct']) });
  /* optional order override, e.g. MENTOR_PROVIDER_ORDER=openai,gemini */
  const order = String(process.env.MENTOR_PROVIDER_ORDER || '').split(',').map(s => s.trim()).filter(Boolean);
  if (order.length) out.sort((a, b) => (order.indexOf(a.id) + 1 || 99) - (order.indexOf(b.id) + 1 || 99));
  return out;
}

async function timed(url, opts, ms) {
  const ctl = new AbortController();
  const t = setTimeout(() => ctl.abort(), Math.max(800, ms));
  try { return await fetch(url, Object.assign({}, opts, { signal: ctl.signal })); }
  finally { clearTimeout(t); }
}

class ModelGone extends Error {}

const SAFETY = [
  { category: 'HARM_CATEGORY_HARASSMENT', threshold: 'BLOCK_ONLY_HIGH' },
  { category: 'HARM_CATEGORY_HATE_SPEECH', threshold: 'BLOCK_ONLY_HIGH' },
  { category: 'HARM_CATEGORY_DANGEROUS_CONTENT', threshold: 'BLOCK_ONLY_HIGH' },
  { category: 'HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold: 'BLOCK_MEDIUM_AND_ABOVE' }
];

/* thinking off where the model allows it: 2.5 models take thinkingBudget 0, newer ones take a level */
function thinking(model) {
  if (/2\.5/.test(model)) return { thinkingBudget: 0 };
  if (/latest|gemini-3/.test(model)) return { thinkingLevel: 'minimal' };
  return undefined;
}
class Rejected extends Error {}
/* a reply cut off by the length limit: keep it if most of it is there (end at the last full sentence), else reject */
function trimCut(text) {
  const m = String(text).match(/^[\s\S]*[.!?؟。](["'”’)\]]*)(?=\s|$)/);
  return m && m[0].length >= Math.min(160, text.length * 0.6) ? m[0].trim() : null;
}

async function geminiPost(model, payload, ms) {
  const res = await timed(GEMINI_BASE + model + ':generateContent?key=' + encodeURIComponent(process.env.GEMINI_API_KEY), {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
  }, ms);
  if (res.status === 404 || res.status === 400) {
    const t = await res.text().catch(() => '');
    if (res.status === 400 && /thinking/i.test(t)) throw new ModelGone('thinking unsupported');
    throw new ModelGone('gemini ' + model + ' ' + res.status + ' ' + t.slice(0, 160));
  }
  if (res.status === 429 || res.status === 503) throw new ModelGone('gemini ' + model + ' busy ' + res.status);
  if (!res.ok) throw new Error('gemini ' + res.status + ' ' + (await res.text().catch(() => '')).slice(0, 200));
  return res.json();
}

async function callGemini(model, system, messages, opt, ms) {
  const contents = messages.map(m => ({ role: m.role === 'assistant' ? 'model' : 'user', parts: [{ text: m.content }] }));
  const build = (th) => ({ contents, systemInstruction: { parts: [{ text: system }] }, safetySettings: SAFETY,
    generationConfig: { temperature: opt.temperature, topP: 0.95, maxOutputTokens: opt.maxTokens, thinkingConfig: th } });
  const t0 = Date.now();
  let data;
  try { data = await geminiPost(model, build(thinking(model)), ms); }
  catch (e) { if (/thinking unsupported/.test(e.message)) data = await geminiPost(model, build(undefined), ms - (Date.now() - t0)); else throw e; }
  const c = data && data.candidates && data.candidates[0];
  let text = c && c.content && c.content.parts ? c.content.parts.map(p => p.thought ? '' : (p.text || '')).join('').trim() : '';
  if (!text) throw new ModelGone('gemini ' + model + ' empty (' + ((c && c.finishReason) || 'no candidate') + ')');
  if (c.finishReason === 'MAX_TOKENS') { const t = trimCut(text); if (!t) throw new Rejected('gemini ' + model + ' cut off: ' + text.slice(-60)); text = t; }
  return text;
}

async function callOpenAICompatible(url, key, model, system, messages, opt, ms) {
  const res = await timed(url, {
    method: 'POST', headers: { Authorization: 'Bearer ' + key, 'Content-Type': 'application/json' },
    body: JSON.stringify({ model, messages: [{ role: 'system', content: system }].concat(messages), max_tokens: opt.maxTokens, temperature: opt.temperature })
  }, ms);
  if (res.status === 404 || res.status === 400 || res.status === 429) throw new ModelGone(model + ' ' + res.status + ' ' + (await res.text().catch(() => '')).slice(0, 160));
  if (!res.ok) throw new Error(model + ' ' + res.status + ' ' + (await res.text().catch(() => '')).slice(0, 200));
  const data = await res.json();
  const ch = data && data.choices && data.choices[0];
  let text = ch && ch.message && ch.message.content;
  if (!text || !String(text).trim()) throw new ModelGone(model + ' empty');
  text = String(text).trim();
  if (ch.finish_reason === 'length') { const t = trimCut(text); if (!t) throw new Rejected(model + ' cut off'); text = t; }
  return text;
}

/* generate({ system, messages, maxTokens, temperature, budgetMs, deadline, fast, validate, health })
   -> { text, engine, model, tried:[...], report:[...] } ; throws Error('all_providers_failed') with .tried and .report
   validate(text) returns a reason string when an answer is not good enough (the next model is then tried).
   health = { model: row from ai_model_status } puts models that recently worked first and skips models that were
   switched off (24 h) or busy (2 min). report lists what happened to every model tried, for ai_model_status. */
async function generate(o) {
  const opt = { maxTokens: o.maxTokens || 2048, temperature: o.temperature == null ? 0.75 : o.temperature };
  const deadline = o.deadline || (Date.now() + (o.budgetMs || 9000));
  const tried = [], report = [], health = o.health || {}, now = Date.now();
  let list = [];
  providers(o.fast).forEach(p => p.models.forEach((m, k) => list.push({ id: p.id, model: m, base: list.length })));
  /* order by what is known to work with this key */
  const score = x => {
    const h = health[x.model]; if (!h) return 1000 + x.base;
    if (h.blocked_until && new Date(h.blocked_until).getTime() > now) return 5000 + x.base;
    const okAt = h.last_ok_at ? new Date(h.last_ok_at).getTime() : 0, failAt = h.last_fail_at ? new Date(h.last_fail_at).getTime() : 0;
    if (okAt && okAt >= failAt) return x.base + Math.min(400, (h.avg_ms || 3000) / 20);
    return 2000 + x.base;
  };
  list.sort((a, b) => score(a) - score(b));
  let skip = null, slowed = false;
  for (let i = 0; i < list.length; i++) {
    const p = list[i], model = p.model;
    if (skip === p.id) continue;
    const left = deadline - Date.now();
    if (left < 1200) { const e = new Error('all_providers_failed'); e.tried = tried.concat(['out of time']); e.report = report; throw e; }
    /* keep about 2.5 s back so a quicker model can still answer if this one is slow */
    const cap = i < list.length - 1 && left > 6000 ? left - 2500 : left - 150;
    const use = slowed ? Object.assign({}, opt, { maxTokens: Math.max(600, Math.round(opt.maxTokens * 0.7)) }) : opt;
    const t0 = Date.now();
    try {
      let text;
      if (p.id === 'gemini') text = await callGemini(model, o.system, o.messages, use, cap);
      else if (p.id === 'openai') text = await callOpenAICompatible(OPENAI_URL, process.env.OPENAI_API_KEY, model, o.system, o.messages, use, cap);
      else text = await callOpenAICompatible(HF_URL, process.env.HF_TOKEN, model, o.system, o.messages, use, cap);
      const bad = o.validate ? o.validate(text) : null;
      if (bad) throw new Rejected('rejected: ' + bad);
      report.push({ model, provider: p.id, ok: true, ms: Date.now() - t0 });
      return { text, engine: p.id, model, tried, report };
    } catch (e) {
      const msg = String(e && e.message || e).slice(0, 160);
      tried.push(p.id + ':' + model + ' -> ' + msg);
      const gone = /\b404\b|not found|is not supported|deprecated|no longer available/i.test(msg) && !(e instanceof Rejected);
      const busy = /busy|\b429\b|\b503\b|quota|exhausted/i.test(msg);
      report.push({ model, provider: p.id, ok: false, ms: Date.now() - t0, error: msg, block_s: gone ? 86400 : busy ? 120 : 0 });
      if (e.name === 'AbortError') {
        slowed = true;
        /* too slow: go straight to this provider's quickest model if there is one, otherwise the next provider */
        const lite = list.findIndex((x, k) => k > i && x.id === p.id && /lite|mini/.test(x.model));
        if (lite > i + 1) { const [x] = list.splice(lite, 1); list.splice(i + 1, 0, x); }
      } else if (!(e instanceof ModelGone) && !(e instanceof Rejected)) skip = p.id; /* provider-level failure: skip its other models */
    }
  }
  const e = new Error('all_providers_failed'); e.tried = tried; e.report = report; throw e;
}

function configured() { return providers().map(p => ({ id: p.id, models: p.models })); }

/* ── voice out: natural female voice ─────────────────────────────────────────── */
function wavFromPcm(pcm, rate) {
  const h = Buffer.alloc(44);
  h.write('RIFF', 0); h.writeUInt32LE(36 + pcm.length, 4); h.write('WAVE', 8); h.write('fmt ', 12);
  h.writeUInt32LE(16, 16); h.writeUInt16LE(1, 20); h.writeUInt16LE(1, 22); h.writeUInt32LE(rate, 24);
  h.writeUInt32LE(rate * 2, 28); h.writeUInt16LE(2, 32); h.writeUInt16LE(16, 34); h.write('data', 36); h.writeUInt32LE(pcm.length, 40);
  return Buffer.concat([h, pcm]);
}

const VOICE_STYLE = 'You are a warm, calm African woman mentor speaking to a woman you care about. Speak naturally, like a real conversation: relaxed pace, gentle warmth, clear pronunciation, natural pauses at commas and full stops. Never sound like a robot or an announcer.';

/* free Google Translate voice: female, no key; speaks Hausa natively (and English, French, Portuguese, Arabic,
   Swahili), up to 200 characters per request, so longer text is sent in pieces and the MP3s are joined */
const GTTS_LANGS = { en: 'en', fr: 'fr', pt: 'pt', ar: 'ar', sw: 'sw', ha: 'ha', af: 'af', am: 'am', so: 'so', zu: 'zu' };
async function googleVoice(text, lang, ms) {
  const tl = GTTS_LANGS[lang]; if (!tl) throw new Error('no google voice for ' + lang);
  const parts = []; let cur = '';
  String(text).split(/(\s+)/).forEach(w => { if ((cur + w).length > 190 && cur.trim()) { parts.push(cur.trim()); cur = w; } else cur += w; });
  if (cur.trim()) parts.push(cur.trim());
  const end = Date.now() + ms;
  const bufs = await Promise.all(parts.slice(0, 6).map(async q => {
    const res = await timed('https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=' + tl + '&q=' + encodeURIComponent(q), { headers: { 'User-Agent': 'Mozilla/5.0', Referer: 'https://translate.google.com/' } }, Math.max(1000, end - Date.now()));
    if (!res.ok) throw new Error('google voice ' + res.status);
    return Buffer.from(await res.arrayBuffer());
  }));
  const audio = Buffer.concat(bufs); if (audio.length < 800) throw new Error('google voice empty');
  return audio;
}

/* speak({ text, lang, langName, deadline }) -> { audio: Buffer, mime, engine, model }
   Order (v180): free Microsoft neural voice (natural women's voices, no key; Nigerian English for English, Yoruba
   and Igbo), Google's free voice first for Hausa (it speaks Hausa natively), then Gemini and OpenAI voices when
   their keys exist, and Google's free voice as the last resort. */
async function speak(o) {
  const deadline = o.deadline || (Date.now() + 9000);
  const tried = [];
  const text = String(o.text || '').slice(0, 900);
  const lang = String(o.lang || 'en').slice(0, 3).replace(/-.*/, '');
  if (lang === 'ha') {
    try { return { audio: await googleVoice(text, 'ha', Math.min(5000, deadline - Date.now() - 300)), mime: 'audio/mpeg', engine: 'google-free', model: 'translate_tts' }; }
    catch (e) { tried.push('google-free:ha -> ' + String(e.message).slice(0, 100)); }
  }
  try {
    const left = deadline - Date.now();
    if (left > 1500) { const mp3 = await edge.synth({ text, lang, timeoutMs: Math.min(7000, left - 300) }); return { audio: mp3, mime: 'audio/mpeg', engine: 'edge-free', model: (edge.VOICES[lang] || edge.VOICES.en) }; }
  } catch (e) { tried.push('edge-free -> ' + String(e.message).slice(0, 120)); }
  if (process.env.GEMINI_API_KEY) {
    const voice = process.env.MENTOR_VOICE || 'Aoede';
    for (const model of uniq([process.env.GEMINI_TTS_MODEL, 'gemini-2.5-flash-preview-tts', 'gemini-2.5-flash-tts'])) {
      const left = deadline - Date.now(); if (left < 1500) break;
      try {
        const data = await geminiPost(model, {
          contents: [{ parts: [{ text: VOICE_STYLE + ' Read this in ' + (o.langName || 'English') + ', exactly as written:\n\n' + text }] }],
          generationConfig: { responseModalities: ['AUDIO'], speechConfig: { voiceConfig: { prebuiltVoiceConfig: { voiceName: voice } } } }
        }, left - 150);
        const part = data && data.candidates && data.candidates[0] && data.candidates[0].content && (data.candidates[0].content.parts || []).find(p => p.inlineData);
        if (!part) throw new ModelGone('no audio');
        const mime = part.inlineData.mimeType || '';
        const raw = Buffer.from(part.inlineData.data, 'base64');
        if (/wav|mpeg|mp3|ogg/.test(mime)) return { audio: raw, mime: mime.split(';')[0], engine: 'gemini', model };
        const rate = Number((mime.match(/rate=(\d+)/) || [])[1] || 24000);
        return { audio: wavFromPcm(raw, rate), mime: 'audio/wav', engine: 'gemini', model };
      } catch (e) { tried.push('gemini:' + model + ' -> ' + String(e.message).slice(0, 120)); }
    }
  }
  if (process.env.OPENAI_API_KEY) {
    for (const model of uniq([process.env.OPENAI_TTS_MODEL, 'gpt-4o-mini-tts', 'tts-1'])) {
      const left = deadline - Date.now(); if (left < 1500) break;
      try {
        const body = { model, voice: process.env.OPENAI_VOICE || 'shimmer', input: text, response_format: 'mp3' };
        if (model !== 'tts-1') body.instructions = VOICE_STYLE;
        const res = await timed('https://api.openai.com/v1/audio/speech', { method: 'POST', headers: { Authorization: 'Bearer ' + process.env.OPENAI_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify(body) }, left - 150);
        if (!res.ok) throw new Error(res.status + ' ' + (await res.text().catch(() => '')).slice(0, 120));
        return { audio: Buffer.from(await res.arrayBuffer()), mime: 'audio/mpeg', engine: 'openai', model };
      } catch (e) { tried.push('openai:' + model + ' -> ' + String(e.message).slice(0, 120)); }
    }
  }
  if (lang !== 'ha' && GTTS_LANGS[lang] && deadline - Date.now() > 1200) {
    try { return { audio: await googleVoice(text, lang, deadline - Date.now() - 300), mime: 'audio/mpeg', engine: 'google-free', model: 'translate_tts' }; }
    catch (e) { tried.push('google-free -> ' + String(e.message).slice(0, 100)); }
  }
  const e = new Error('no_voice'); e.tried = tried; throw e;
}

/* ── voice in: short recording to text ───────────────────────────────────────── */
/* transcribe({ audioB64, mime, langName, deadline }) -> { text, engine } */
async function transcribe(o) {
  const deadline = o.deadline || (Date.now() + 9000);
  const tried = [];
  if (process.env.GEMINI_API_KEY) {
    for (const model of uniq([process.env.GEMINI_MODEL, 'gemini-2.5-flash', 'gemini-flash-latest', 'gemini-2.5-flash-lite'])) {
      const left = deadline - Date.now(); if (left < 1500) break;
      try {
        const data = await geminiPost(model, {
          contents: [{ role: 'user', parts: [
            { inlineData: { mimeType: o.mime || 'audio/wav', data: o.audioB64 } },
            { text: 'Transcribe exactly what this woman says. She is most likely speaking ' + (o.langName || 'English') + ' (she may mix in English or Nigerian Pidgin). Write only her words in the language she used, with correct spelling and accents. If there is no clear speech, reply with exactly: [silence]' }
          ] }],
          generationConfig: { temperature: 0, maxOutputTokens: 400, thinkingConfig: thinking(model) }
        }, left - 150);
        const c = data && data.candidates && data.candidates[0];
        const text = c && c.content && c.content.parts ? c.content.parts.map(p => p.thought ? '' : (p.text || '')).join('').trim() : '';
        if (!text) throw new ModelGone('empty');
        return { text: /^\[?silence\]?$/i.test(text) ? '' : text, engine: 'gemini', model };
      } catch (e) { tried.push('gemini:' + model + ' -> ' + String(e.message).slice(0, 120)); }
    }
  }
  if (process.env.OPENAI_API_KEY) {
    const left = deadline - Date.now();
    if (left > 1500) {
      try {
        const fd = new FormData();
        fd.append('file', new Blob([Buffer.from(o.audioB64, 'base64')], { type: o.mime || 'audio/wav' }), 'voice.wav');
        fd.append('model', process.env.OPENAI_STT_MODEL || 'gpt-4o-mini-transcribe');
        const res = await timed('https://api.openai.com/v1/audio/transcriptions', { method: 'POST', headers: { Authorization: 'Bearer ' + process.env.OPENAI_API_KEY }, body: fd }, left - 150);
        if (!res.ok) throw new Error(res.status + ' ' + (await res.text().catch(() => '')).slice(0, 120));
        const j = await res.json();
        return { text: String(j.text || '').trim(), engine: 'openai' };
      } catch (e) { tried.push('openai -> ' + String(e.message).slice(0, 120)); }
    }
  }
  const e = new Error('no_transcription'); e.tried = tried; throw e;
}

module.exports = { generate, configured, speak, transcribe, wavFromPcm };
