const fs = require('fs'); const { synth } = require('./edge-tts.js');
const S = JSON.parse(fs.readFileSync('script.json')); const L = process.argv[2];
fs.mkdirSync('out/' + L, { recursive: true }); const log = [];
(async () => {
  for (const b of S.beats) {
    const t0 = Date.now(); let ok = false, err = '';
    for (let k = 0; k < 4 && !ok; k++) {
      try { const buf = await synth({ text: b.voice[L], lang: L, rate: '-4%', timeoutMs: 30000 }); if (buf && buf.length > 2000) { fs.writeFileSync(`out/${L}/${b.id}.mp3`, buf); ok = true; } else err = 'empty'; }
      catch (e) { err = String(e.message || e).slice(0, 120); await new Promise(r => setTimeout(r, 2000)); }
    }
    const line = `${b.id} ${ok} ${(Date.now() - t0) / 1000}s ${err}`; log.push(line); console.log(line);
  }
  fs.writeFileSync(`out/log-${L}.txt`, log.join('\n'));
})();
