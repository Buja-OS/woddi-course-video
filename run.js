const fs = require('fs'); const { synth } = require('./edge-tts.js');
const S = JSON.parse(fs.readFileSync('lines.json')); fs.mkdirSync('out', { recursive: true }); const log = [];
(async () => {
  for (const b of S.lines) {
    for (const [tag, rate] of [['', '-6%']]) {
      let ok = false, err = '';
      for (let k = 0; k < 5 && !ok; k++) {
        try { const buf = await synth({ text: b.voice, lang: 'en', voice: 'en-NG-EzinneNeural', rate, timeoutMs: 30000 }); if (buf && buf.length > 2000) { fs.writeFileSync(`out/${b.id}${tag}.mp3`, buf); ok = true; } else err = 'empty'; }
        catch (e) { err = String(e.message || e).slice(0, 120); await new Promise(r => setTimeout(r, 2500)); }
      }
      log.push(`${b.id}${tag} ${ok} ${err}`); console.log(log[log.length - 1]);
    }
  }
  fs.writeFileSync('out/log.txt', log.join('\n'));
})();
