/* WODDI free natural voice (v180): Microsoft Edge "Read aloud" neural voices.
   No API key, no account, no package to install: the same free service the Edge browser uses to read pages aloud.
   It gives natural, warm female voices, including a Nigerian English woman (en-NG-EzinneNeural), Kenyan Swahili
   (sw-KE-ZuriNeural), French, Portuguese and Arabic. Hausa, Yoruba and Igbo have no neural voice anywhere yet, so
   they are read by the Nigerian English voice (understandable, with a Nigerian accent).
   Written with Node's own tls and crypto modules (a tiny WebSocket client) so nothing extra has to be bundled.
   synth({ text, lang, voice?, rate?, timeoutMs }) -> Buffer (MP3, 24 kHz mono) */
'use strict';

const tls = require('tls');
const crypto = require('crypto');

const TOKEN = '6A5AA1D4EAFF4E9FB37E23D68491D6F4';
const HOST = 'speech.platform.bing.com';
const PATH = '/consumer/speech/synthesize/readaloud/edge/v1';
const CHROMIUM = '143.0.3650.75'; /* as used by the open-source edge-tts 7.2.8, checked 11 Oct 2026 */

/* natural female voices per WODDI language (and the African languages of the landing page where one exists) */
const VOICES = {
  en: 'en-NG-EzinneNeural', fr: 'fr-FR-DeniseNeural', pt: 'pt-PT-RaquelNeural', ar: 'ar-EG-SalmaNeural', sw: 'sw-KE-ZuriNeural',
  ha: 'en-NG-EzinneNeural', yo: 'en-NG-EzinneNeural', ig: 'en-NG-EzinneNeural', pcm: 'en-NG-EzinneNeural',
  zu: 'zu-ZA-ThandoNeural', af: 'af-ZA-AdriNeural', am: 'am-ET-MekdesNeural', so: 'so-SO-UbaxNeural'
};
const LOCALE = { 'en-NG-EzinneNeural': 'en-NG', 'fr-FR-DeniseNeural': 'fr-FR', 'pt-PT-RaquelNeural': 'pt-PT', 'ar-EG-SalmaNeural': 'ar-EG', 'sw-KE-ZuriNeural': 'sw-KE',
  'zu-ZA-ThandoNeural': 'zu-ZA', 'af-ZA-AdriNeural': 'af-ZA', 'am-ET-MekdesNeural': 'am-ET', 'so-SO-UbaxNeural': 'so-SO' };

/* the service asks for a time-based token (Sec-MS-GEC), the same one the Edge browser sends */
let skew = 0; /* seconds between our clock and Microsoft's, learned from a refused request */
function gec() {
  let ticks = Math.floor(Date.now() / 1000 + skew) + 11644473600;
  ticks -= ticks % 300;
  const v = BigInt(ticks) * 10000000n;
  return crypto.createHash('sha256').update(v.toString() + TOKEN, 'ascii').digest('hex').toUpperCase();
}
function xmlEsc(s) { return String(s).replace(/[<>&"']/g, c => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;', "'": '&apos;' })[c]); }
function stamp() { return new Date().toUTCString().replace('GMT', 'GMT+0000 (Coordinated Universal Time)'); }

/* one masked client frame */
function frame(op, payload) {
  const data = Buffer.isBuffer(payload) ? payload : Buffer.from(payload, 'utf8');
  const len = data.length; let head;
  if (len < 126) { head = Buffer.alloc(2); head[1] = 0x80 | len; }
  else if (len < 65536) { head = Buffer.alloc(4); head[1] = 0x80 | 126; head.writeUInt16BE(len, 2); }
  else { head = Buffer.alloc(10); head[1] = 0x80 | 127; head.writeBigUInt64BE(BigInt(len), 2); }
  head[0] = 0x80 | op;
  const mask = crypto.randomBytes(4), body = Buffer.alloc(len);
  for (let i = 0; i < len; i++) body[i] = data[i] ^ mask[i & 3];
  return Buffer.concat([head, mask, body]);
}

/* retry once with the server's clock if the first try is refused because our clock is off */
async function synth(o) {
  try { return await synthOnce(o); }
  catch (e) {
    if (e.serverDate) { const d = Date.parse(e.serverDate); if (d) { skew = (d - Date.now()) / 1000; return synthOnce(o); } }
    throw e;
  }
}
function synthOnce(o) {
  const voice = o.voice || VOICES[String(o.lang || 'en').slice(0, 3)] || VOICES[String(o.lang || 'en').slice(0, 2)] || VOICES.en;
  const text = String(o.text || '').replace(/\s+/g, ' ').trim().slice(0, 1500);
  const rate = o.rate || '-4%';
  return new Promise((resolve, reject) => {
    if (!text) return reject(new Error('empty text'));
    const conn = crypto.randomUUID().replace(/-/g, '');
    const path = `${PATH}?TrustedClientToken=${TOKEN}&Sec-MS-GEC=${gec()}&Sec-MS-GEC-Version=1-${CHROMIUM}&ConnectionId=${conn}`;
    const key = crypto.randomBytes(16).toString('base64');
    let done = false, buf = Buffer.alloc(0), upgraded = false, msg = [], msgOp = 0;
    const audio = [];
    const sock = tls.connect({ host: HOST, port: 443, servername: HOST });
    const timer = setTimeout(() => finish(new Error('edge tts timeout')), o.timeoutMs || 8000);
    function finish(err) {
      if (done) return; done = true; clearTimeout(timer);
      try { sock.end(frame(0x8, Buffer.from([0x03, 0xe8]))); } catch (e) {} try { sock.destroy(); } catch (e) {}
      if (err) reject(err); else if (!audio.length) reject(new Error('edge tts: no audio')); else resolve(Buffer.concat(audio));
    }
    sock.on('error', e => finish(e));
    sock.on('close', () => finish(audio.length ? null : new Error('edge tts closed')));
    sock.on('secureConnect', () => {
      const muid = crypto.randomBytes(16).toString('hex').toUpperCase();
      sock.write(`GET ${path} HTTP/1.1\r\nHost: ${HOST}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: ${key}\r\nSec-WebSocket-Version: 13\r\n` +
        `Origin: chrome-extension://jdiccldimpdaibmpdkjnbmckianbfold\r\nPragma: no-cache\r\nCache-Control: no-cache\r\nAccept-Encoding: gzip, deflate, br, zstd\r\nAccept-Language: en-US,en;q=0.9\r\nCookie: muid=${muid};\r\n` +
        `User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/${CHROMIUM.split('.')[0]}.0.0.0 Safari/537.36 Edg/${CHROMIUM.split('.')[0]}.0.0.0\r\n\r\n`);
    });
    function onMessage(op, data) {
      if (op === 0x1) { if (/Path:turn\.end/.test(data.toString('utf8'))) finish(null); return; }
      if (op === 0x2 && data.length > 2) {
        const hl = data.readUInt16BE(0), header = data.slice(2, 2 + hl).toString('utf8');
        if (/Path:audio/.test(header)) { const a = data.slice(2 + hl); if (a.length) audio.push(a); }
      }
    }
    sock.on('data', chunk => {
      buf = Buffer.concat([buf, chunk]);
      if (!upgraded) {
        const end = buf.indexOf('\r\n\r\n'); if (end < 0) return;
        const head = buf.slice(0, end).toString('utf8'); buf = buf.slice(end + 4);
        if (!/^HTTP\/1\.1 101/.test(head)) { const er = new Error('edge tts handshake: ' + head.split('\r\n')[0]); const dm = head.match(/\r\ndate:\s*([^\r\n]+)/i); if (/403/.test(head) && dm && !o._retried) { er.serverDate = dm[1]; o._retried = true; } return finish(er); }
        upgraded = true;
        const req = crypto.randomUUID().replace(/-/g, '');
        sock.write(frame(0x1, `X-Timestamp:${stamp()}\r\nContent-Type:application/json; charset=utf-8\r\nPath:speech.config\r\n\r\n` +
          '{"context":{"synthesis":{"audio":{"metadataoptions":{"sentenceBoundaryEnabled":"false","wordBoundaryEnabled":"false"},"outputFormat":"audio-24khz-48kbitrate-mono-mp3"}}}}'));
        const loc = LOCALE[voice] || 'en-US';
        sock.write(frame(0x1, `X-RequestId:${req}\r\nContent-Type:application/ssml+xml\r\nX-Timestamp:${stamp()}Z\r\nPath:ssml\r\n\r\n` +
          `<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='${loc}'><voice name='${voice}'><prosody pitch='+0Hz' rate='${rate}' volume='+0%'>${xmlEsc(text)}</prosody></voice></speak>`));
      }
      /* read frames */
      while (buf.length >= 2) {
        const fin = (buf[0] & 0x80) !== 0, op = buf[0] & 0x0f; let len = buf[1] & 0x7f, off = 2;
        if (len === 126) { if (buf.length < 4) return; len = buf.readUInt16BE(2); off = 4; }
        else if (len === 127) { if (buf.length < 10) return; len = Number(buf.readBigUInt64BE(2)); off = 10; }
        if (buf.length < off + len) return;
        const data = buf.slice(off, off + len); buf = buf.slice(off + len);
        if (op === 0x8) return finish(audio.length ? null : new Error('edge tts closed by server'));
        if (op === 0x9) { sock.write(frame(0xA, data)); continue; }
        if (op === 0x0) { msg.push(data); if (fin) { onMessage(msgOp, Buffer.concat(msg)); msg = []; } continue; }
        if (fin) onMessage(op, data); else { msgOp = op; msg = [data]; }
      }
    });
  });
}

module.exports = { synth, VOICES };
