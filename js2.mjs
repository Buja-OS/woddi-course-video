import { pipeline, env } from '@huggingface/transformers';
import fs from 'fs';
const res = {};
const text = 'báwo ni, craig. bí owó tí ń wọlé kò bá pọ̀, a máa ń nira láti fi pamọ́, àmọ́ ó ṣeé ṣe.';
for (const dtype of ['q8', 'fp32']) {
  try {
    const t0 = Date.now(); const tts = await pipeline('text-to-speech', 'Xenova/mms-tts-yor', { dtype }); const load = Date.now() - t0;
    const t1 = Date.now(); const o = await tts(text); const gen = Date.now() - t1;
    res[dtype] = { load_ms: load, gen_ms: gen, rate: o.sampling_rate, seconds: o.audio.length / o.sampling_rate };
    const pcm = Int16Array.from(o.audio, x => Math.max(-32768, Math.min(32767, x * 32767)));
    const h = Buffer.alloc(44); h.write('RIFF', 0); h.writeUInt32LE(36 + pcm.length * 2, 4); h.write('WAVE', 8); h.write('fmt ', 12); h.writeUInt32LE(16, 16); h.writeUInt16LE(1, 20); h.writeUInt16LE(1, 22); h.writeUInt32LE(o.sampling_rate, 24); h.writeUInt32LE(o.sampling_rate * 2, 28); h.writeUInt16LE(2, 32); h.writeUInt16LE(16, 34); h.write('data', 36); h.writeUInt32LE(pcm.length * 2, 40);
    fs.writeFileSync('res/xenova_yor_' + dtype + '.wav', Buffer.concat([h, Buffer.from(pcm.buffer)]));
  } catch (e) { res[dtype] = 'ERR ' + String(e.stack || e).slice(0, 300); }
}
try { const info = await (await fetch('https://huggingface.co/api/models/Xenova/mms-tts-yor?blobs=true')).json(); res.files = (info.siblings || []).map(s => [s.rfilename, s.size]); } catch (e) { res.files = String(e); }
fs.writeFileSync('res/xenova.json', JSON.stringify(res, null, 1)); console.log(res);
