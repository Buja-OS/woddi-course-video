const fs = require('fs'); const { speak } = require('./_shared/llm.js');
const T = { en: 'Hello Amina, I am your WODDI mentor. Let us work out a fair price for your liquid soap, step by step.', fr: 'Bonjour Amina, je suis votre mentore WODDI. Calculons ensemble un prix juste pour votre savon liquide.',
  pt: 'Olá Amina, sou a sua mentora WODDI. Vamos calcular juntas um preço justo para o seu sabão líquido.', ar: 'مرحبا أمينة، أنا مرشدتك في WODDI. لنحسب معًا سعرًا عادلًا للصابون السائل.',
  sw: 'Habari Amina, mimi ni mshauri wako wa WODDI. Tupange pamoja bei nzuri ya sabuni yako ya maji.', ha: 'Sannu Amina, ni ce jagorarki ta WODDI. Bari mu lissafa farashi mai adalci na sabulun ruwanki tare.',
  yo: 'Ẹ n lẹ Amina, èmi ni olùtọ́nisọ́nà WODDI rẹ. Ẹ jẹ́ ká jọ ṣírò iye tó tọ́ fún ọṣẹ olómi rẹ.', ig: 'Ndewo Amina, abụ m onye ndụmọdụ WODDI gị. Ka anyị gbakọọ ọnụ ahịa kwesịrị ekwesị maka ncha mmiri gị.' };
(async () => { fs.mkdirSync('out', { recursive: true }); const rep = [];
  for (const l of Object.keys(T)) { const t0 = Date.now();
    try { const r = await speak({ text: T[l], lang: l, deadline: Date.now() + 9300 }); fs.writeFileSync('out/v_' + l + '.mp3', r.audio); rep.push(`${l}: OK ${r.engine} ${r.model} ${r.audio.length} bytes ${Date.now() - t0} ms`); }
    catch (e) { rep.push(`${l}: FAIL ${JSON.stringify(e.tried || e.message)}`); } }
  fs.writeFileSync('out/report3.txt', rep.join('\n')); console.log(rep.join('\n')); })();
