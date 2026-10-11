import { pipeline, env } from '@huggingface/transformers';
import fs from 'fs';
env.allowRemoteModels = false; env.localModelPath = process.cwd() + '/';
const res = {};
const T = { yor: 'Báwo ni, Craig. Bí owó tí ń wọlé kò bá pọ̀, a máa ń nira láti fi pamọ́, àmọ́ ó ṣeé ṣe.', ibo: 'Ndewo Craig. Ọ na-esi ike ichekwa ego mgbe ego batara dị ntakịrị, mana ọ ga-ekwe omume.' };
for (const L of ['yor', 'ibo']) {
  try {
    const t0 = Date.now(); const tts = await pipeline('text-to-speech', 'web_' + L, { dtype: 'q8' }); const load = Date.now() - t0;
    const t1 = Date.now(); const o = await tts(T[L].toLowerCase()); const gen = Date.now() - t1;
    res[L] = { load_ms: load, gen_ms: gen, rate: o.sampling_rate, seconds: o.audio.length / o.sampling_rate };
    const pcm = Int16Array.from(o.audio, x => Math.max(-32768, Math.min(32767, x * 32767)));
    const h = Buffer.alloc(44); h.write('RIFF', 0); h.writeUInt32LE(36 + pcm.length * 2, 4); h.write('WAVE', 8); h.write('fmt ', 12); h.writeUInt32LE(16, 16); h.writeUInt16LE(1, 20); h.writeUInt16LE(1, 22); h.writeUInt32LE(o.sampling_rate, 24); h.writeUInt32LE(o.sampling_rate * 2, 28); h.writeUInt16LE(2, 32); h.writeUInt16LE(16, 34); h.write('data', 36); h.writeUInt32LE(pcm.length * 2, 40);
    fs.writeFileSync('res/js_' + L + '_q8.wav', Buffer.concat([h, Buffer.from(pcm.buffer)]));
  } catch (e) { res[L] = 'ERR ' + String(e.stack || e).slice(0, 400); }
}
fs.writeFileSync('res/js.json', JSON.stringify(res, null, 1)); console.log(res);
